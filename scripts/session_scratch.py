#!/usr/bin/env python3
"""Session scratch-directory accounting and sweep (ticket 0854).

Every Claude Code session gets `<temp-root>/<cwd-key>/<session-id>/`, one per
distinct cwd it visits, and the runtime only ever creates them: no
delete-on-exit, no startup sweep, no settings key. Where the temp root is a
tmpfs under a per-user quota, the leftovers are charged to every later session
of the same user until the Bash tool dies with EDQUOT (2026-09-06 on this host:
three sessions killed at once, ending in a reboot).

Two consumers:

* `project-state.py` calls `scan()` for healthcheck item 12 — usage against the
  per-user cap, and the session directories whose session has no live process.
  Report only.
* `/molt` calls `--sweep`, which removes exactly those orphans. It re-runs the
  liveness test itself rather than trusting a list computed earlier: a session
  can start between the probe and the sweep.

Liveness, three signals, union (any one means live — the test fails safe):

1. an open descriptor of a live process resolves inside the session directory —
   the CLI holds one on the session's `tasks/` directory for the session's whole
   life, which is the signal that covers an idle session with no children;
2. a live process's cwd is inside it (the rail `worktree-gc.sh` uses);
3. the session id appears in a live process's environment or command line.

Plus a minimum-age rail: a directory touched within the last few minutes is
never swept, so a session that has just created its directory and not yet
opened anything in it cannot be caught in the gap.

What this cannot see: a session belonging to another user, or one running on
another machine against a shared filesystem. Their directories are unreadable
or their processes invisible, so they would read as orphans. That is why the
sweep is scoped to the current user's own root and why the age rail exists.

Never relocates the temp root: the runtime's relocation knob is an operator
decision (the root must also stay short — sandbox socket paths are built under
it), so this reports and cleans, and the healthcheck names the knob.
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

# A session directory's name is a uuid. Anything else under a cwd-key directory
# is not ours to reason about, let alone delete.
SESSION_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_UUID_ANYWHERE_RE = re.compile(
    rb"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

# systemd mounts a quota-enabled tmpfs /tmp and caps each user at 80% of it at
# login. The quota tools cannot read a tmpfs quota (measured on this host,
# 2026-09-07: `quota -f /tmp -u` and `repquota /tmp` both fail with "Cannot
# stat() mounted device tmpfs"), so the cap is INFERRED from that default, never
# measured. `cap_source` says so; do not present it as a reading.
SYSTEMD_TMPFS_USER_QUOTA_FRACTION = 0.8

# Warn once the harness's own scratch root reaches this share of the cap.
WARN_FRACTION = 0.6
# And warn on this many orphan directories however small they are: the count is
# the leak signal, the bytes are the damage.
WARN_ORPHAN_COUNT = 8
# Never sweep a directory touched more recently than this.
MIN_ORPHAN_AGE_MINUTES = 15
# Walk ceiling, so a pathological tree cannot stall a healthcheck.
MAX_ENTRIES = 200_000


def scratch_root(env=None):
    """The current user's session scratch root, as a Path (may not exist).

    `CLAUDE_SESSION_SCRATCH_ROOT` is the test seam and the explicit override;
    otherwise the runtime's own layout: one directory per uid under the temp
    base, with the runtime's temp knob taking precedence over `TMPDIR`.
    """
    env = os.environ if env is None else env
    override = env.get("CLAUDE_SESSION_SCRATCH_ROOT")
    if override:
        return Path(override)
    base = env.get("CLAUDE_CODE_TMPDIR") or env.get("TMPDIR") or "/tmp"
    return Path(base) / f"claude-{os.getuid()}"


def _proc_paths_and_ids(proc_root):
    """Scan live processes once: (paths held open or cwd'd into, session ids).

    Every read is best effort — another user's `/proc` entry, a kernel thread,
    and a process that exits mid-scan all raise, and all are skipped. A process
    we cannot read simply contributes no signal.
    """
    held_paths = []
    ids = set()
    try:
        entries = os.listdir(proc_root)
    except OSError:
        return held_paths, ids
    for entry in entries:
        if not entry.isdigit():
            continue
        proc = os.path.join(proc_root, entry)
        for name in ("environ", "cmdline"):
            try:
                with open(os.path.join(proc, name), "rb") as fh:
                    blob = fh.read()
            except OSError:
                continue
            ids.update(m.decode() for m in _UUID_ANYWHERE_RE.findall(blob))
        links = [os.path.join(proc, "cwd")]
        fd_dir = os.path.join(proc, "fd")
        try:
            links.extend(os.path.join(fd_dir, fd) for fd in os.listdir(fd_dir))
        except OSError:
            pass
        for link in links:
            try:
                held_paths.append(os.readlink(link))
            except OSError:
                continue
    return held_paths, ids


def live_session_ids(root, proc_root="/proc"):
    """Session ids that a live process names, holds open, or sits inside."""
    root = str(Path(root))
    held_paths, ids = _proc_paths_and_ids(proc_root)
    live = set(ids)
    prefix = root.rstrip("/") + "/"
    for path in held_paths:
        if not path.startswith(prefix):
            continue
        parts = path[len(prefix) :].split("/")
        if len(parts) >= 2 and SESSION_ID_RE.match(parts[1]):
            live.add(parts[1])
    return live


def _dir_bytes(path):
    """Disk usage of a directory tree, in bytes, hardlinks counted once.

    `st_blocks` (what `du` reports), not apparent size: a quota counts blocks.
    Returns (bytes, truncated) — truncated when the walk hit MAX_ENTRIES.
    """
    total = 0
    seen = set()
    entries = 0
    for dirpath, dirnames, filenames in os.walk(path, onerror=lambda _e: None):
        for name in dirnames + filenames:
            entries += 1
            if entries > MAX_ENTRIES:
                return total, True
            try:
                st = os.lstat(os.path.join(dirpath, name))
            except OSError:
                continue
            if st.st_nlink > 1:
                key = (st.st_dev, st.st_ino)
                if key in seen:
                    continue
                seen.add(key)
            total += st.st_blocks * 512
    return total, False


def _newest_mtime(path):
    """Directory mtime, or its newest immediate child's — whichever is later.

    A session writing into `scratchpad/` bumps that subdirectory, not the
    session directory itself, so the bare mtime understates recent activity.
    """
    newest = 0.0
    try:
        newest = os.stat(path).st_mtime
    except OSError:
        return newest
    try:
        for child in os.scandir(path):
            try:
                newest = max(newest, child.stat(follow_symlinks=False).st_mtime)
            except OSError:
                continue
    except OSError:
        pass
    return newest


def _mount_for(path):
    """The mount entry (mountpoint, fstype, options) carrying `path`."""
    best = None
    try:
        with open("/proc/mounts", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    target = str(path)
    for line in lines:
        fields = line.split()
        if len(fields) < 4:
            continue
        mountpoint = fields[1].replace("\\040", " ")
        if target == mountpoint or target.startswith(mountpoint.rstrip("/") + "/"):
            if best is None or len(mountpoint) > len(best[0]):
                best = (mountpoint, fields[2], fields[3])
    return best


def _filesystem_state(path):
    """Size/used/avail of the filesystem holding `path`, plus the cap inference."""
    state = {
        "mount": None,
        "type": None,
        "size_bytes": None,
        "used_bytes": None,
        "avail_bytes": None,
        "cap_bytes": None,
        "cap_source": "none",
    }
    probe = path if path.exists() else path.parent
    try:
        st = os.statvfs(probe)
    except OSError:
        return state
    size = st.f_blocks * st.f_frsize
    state["size_bytes"] = size
    state["avail_bytes"] = st.f_bavail * st.f_frsize
    state["used_bytes"] = size - st.f_bfree * st.f_frsize
    mount = _mount_for(probe)
    if mount:
        state["mount"], state["type"], options = mount
        if "usrquota" in options.split(","):
            state["cap_bytes"] = int(size * SYSTEMD_TMPFS_USER_QUOTA_FRACTION)
            state["cap_source"] = (
                "inferred: mount carries usrquota; the init system's default "
                f"per-user share is {int(SYSTEMD_TMPFS_USER_QUOTA_FRACTION * 100)}% "
                "of the mount. Quota tools cannot read a tmpfs quota, so this is "
                "an inference, not a measurement."
            )
    return state


def scan(root=None, proc_root="/proc", min_age_minutes=MIN_ORPHAN_AGE_MINUTES):
    """Temp-root usage and the orphan session directories. Never raises."""
    root = Path(root) if root is not None else scratch_root()
    now = time.time()
    out = {
        "root": str(root),
        "exists": root.is_dir(),
        "sessions_total": 0,
        "live": 0,
        "orphan_count": 0,
        "orphan_bytes": 0,
        "root_bytes": 0,
        "truncated": False,
        "usage_fraction": None,
        "orphans": [],
        "status": "ok",
        "reasons": [],
    }
    out.update({k: v for k, v in _filesystem_state(root).items()})
    if not out["exists"]:
        return out

    live = live_session_ids(root, proc_root=proc_root)
    root_bytes, truncated = _dir_bytes(root)
    out["root_bytes"] = root_bytes
    out["truncated"] = truncated

    age_floor = now - min_age_minutes * 60
    for key_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if key_dir.is_symlink():
            continue
        for session_dir in sorted(p for p in key_dir.iterdir() if p.is_dir()):
            if session_dir.is_symlink():
                continue
            session_id = session_dir.name
            if not SESSION_ID_RE.match(session_id):
                continue
            out["sessions_total"] += 1
            if session_id in live:
                out["live"] += 1
                continue
            mtime = _newest_mtime(session_dir)
            if mtime > age_floor:
                # Too fresh to call dead: a session that has just created its
                # directory may not have opened anything in it yet.
                out["live"] += 1
                continue
            size, size_truncated = _dir_bytes(session_dir)
            out["truncated"] = out["truncated"] or size_truncated
            out["orphan_count"] += 1
            out["orphan_bytes"] += size
            out["orphans"].append(
                {
                    "path": str(session_dir),
                    "session_id": session_id,
                    "bytes": size,
                    "age_hours": round((now - mtime) / 3600, 1),
                }
            )
    out["orphans"].sort(key=lambda o: o["bytes"], reverse=True)

    cap = out.get("cap_bytes")
    if cap:
        out["usage_fraction"] = round(root_bytes / cap, 3)
        if out["usage_fraction"] >= WARN_FRACTION:
            out["status"] = "warn"
            out["reasons"].append(
                f"session scratch holds {_human(root_bytes)}, "
                f"{int(out['usage_fraction'] * 100)}% of the inferred per-user cap "
                f"({_human(cap)})"
            )
    if out["orphan_count"] >= WARN_ORPHAN_COUNT or out["orphan_bytes"] >= 1 << 30:
        out["status"] = "warn"
        out["reasons"].append(
            f"{out['orphan_count']} orphan session directories "
            f"({_human(out['orphan_bytes'])}) — no live process owns them"
        )
    return out


def _human(n):
    if n is None:
        return "unknown"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def sweep(
    root=None,
    proc_root="/proc",
    min_age_minutes=MIN_ORPHAN_AGE_MINUTES,
    dry_run=False,
):
    """Remove the orphan session directories. Re-runs the liveness test itself.

    Never trusts a list computed earlier: a session can start between the probe
    and the sweep, and the invariant is that no directory whose session has a
    live process is ever removed.
    """
    state = scan(root=root, proc_root=proc_root, min_age_minutes=min_age_minutes)
    root_path = Path(state["root"])
    removed, failed = [], []
    for orphan in state["orphans"]:
        path = Path(orphan["path"])
        # Re-derive containment rather than trusting the recorded path.
        try:
            relative = path.resolve().relative_to(root_path.resolve())
        except (ValueError, OSError):
            failed.append({**orphan, "error": "outside the scratch root"})
            continue
        if len(relative.parts) != 2 or not SESSION_ID_RE.match(relative.parts[1]):
            failed.append({**orphan, "error": "not a <cwd-key>/<session-id> path"})
            continue
        if dry_run:
            removed.append(orphan)
            continue
        try:
            shutil.rmtree(path)
        except OSError as exc:
            failed.append({**orphan, "error": str(exc)[:120]})
            continue
        removed.append(orphan)
        try:
            path.parent.rmdir()  # prune the cwd key once its last session is gone
        except OSError:
            pass
    return {
        "root": state["root"],
        "dry_run": dry_run,
        "removed": removed,
        "removed_bytes": sum(o["bytes"] for o in removed),
        "failed": failed,
        "live": state["live"],
        "sessions_total": state["sessions_total"],
    }


def _report_scan(state):
    if not state["exists"]:
        return
    if state["status"] == "ok" and not state["orphans"]:
        return  # nothing to say
    print(
        f"session-scratch: {state['sessions_total']} session dirs "
        f"({state['live']} live, {state['orphan_count']} orphan, "
        f"{_human(state['orphan_bytes'])} reclaimable) under {state['root']}"
    )
    for reason in state["reasons"]:
        print(f"session-scratch: warn — {reason}")
    for orphan in state["orphans"][:10]:
        print(
            f"session-scratch: orphan {orphan['session_id']} "
            f"({_human(orphan['bytes'])}, {orphan['age_hours']} h) {orphan['path']}"
        )


def _report_sweep(result):
    if not result["removed"] and not result["failed"]:
        return  # silent when there is nothing to do
    verb = "would remove" if result["dry_run"] else "removed"
    for orphan in result["removed"]:
        print(
            f"session-scratch-gc: {verb} {orphan['session_id']} "
            f"({_human(orphan['bytes'])}, idle {orphan['age_hours']} h)"
        )
    for orphan in result["failed"]:
        print(
            f"session-scratch-gc: skipped {orphan['session_id']} — {orphan['error']}",
            file=sys.stderr,
        )
    print(
        f"session-scratch-gc: {verb} {len(result['removed'])} orphan dir(s), "
        f"{_human(result['removed_bytes'])} reclaimed; "
        f"{result['live']} live session(s) untouched."
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root", default=None, help="Scratch root (default: this user's)"
    )
    parser.add_argument(
        "--sweep", action="store_true", help="Remove the orphan directories"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="With --sweep: list, remove nothing"
    )
    parser.add_argument("--json", action="store_true", help="JSON on stdout")
    parser.add_argument(
        "--min-age-minutes",
        type=int,
        default=MIN_ORPHAN_AGE_MINUTES,
        help="Never treat a directory touched more recently than this as an orphan",
    )
    args = parser.parse_args(argv)

    if args.sweep:
        result = sweep(
            root=args.root,
            min_age_minutes=args.min_age_minutes,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2)) if args.json else _report_sweep(result)
    else:
        state = scan(root=args.root, min_age_minutes=args.min_age_minutes)
        print(json.dumps(state, indent=2)) if args.json else _report_scan(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
