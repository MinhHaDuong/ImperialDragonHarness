#!/usr/bin/env python3
"""Land one merge request by /merge's recipe, in one call (ticket 1255).

    raid_land.py <pr> --ruled-head <sha|-> --ruled-claims <ids|-> [--base main] [--cleanup]

Run it from the request's own worktree on its head branch. It executes
`skills/merge/SKILL.md` § The recipe, steps 0 to 8; step 9 (the after-merge
runner) needs no call here: hooks/reference-transaction starts it when step 8's
sync moves main (ticket 1265). That file stays the contract.
`--ruled-head` is the tip the review gate ruled on (`-` for a bookkeeping tier
request, which then must read as bookkeeping). `--ruled-claims` is the comma
list of ticket ids the gate ruled on (`-` for none); the body must still claim
exactly that set. Prints one `<pr> merge <start> <end>` row for
`step_clock.py table` and posts the duration comment.

Exit: 0 merged and synced; 1 refused before any merge (reason on stderr);
4 merged but local main not synced (sync script missing, failing or unknown
output); 5 queued on an ungated base; 6 merge outcome unknown (an error after
the merge call: read the request by hand, never re-run).
With no forge (`<pr>` = `branch:<name> [base=<ref>]`, forge.NoneForge; ticket 1275) the same
recipe runs locally: the merge is forge.NoneForge.merge (a `--no-ff` merge pinned by head OID,
the base moved under the main-update guard, pushed when origin exists), the gate record lives
in refs/notes/gate of this repository, claimed tickets must already be closed on the branch,
and step 8 is read from the refs. Forge calls live in scripts/forge.py; git, merge-gate.py, erg and
sync-local-main.sh are called directly.
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import forge
from step_clock import fmt

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "merge-gate.py"
SYNC = ROOT / "scripts" / "sync-local-main.sh"
OK, REFUSED, UNSYNCED, QUEUED, UNKNOWN = 0, 1, 4, 5, 6


class Refusal(Exception):
    """A reason to stop; the message goes to stderr."""


class PostMerge(Refusal):
    """A failure after the merge call: the outcome is unknown, never re-merge."""


def git(cwd, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)


def rev(cwd, ref: str) -> str:
    done = git(cwd, "rev-parse", ref)
    if done.returncode != 0:
        raise Refusal(f"cannot resolve {ref}")
    return done.stdout.strip()


def gate(cwd, *args: str) -> int:
    return subprocess.run([sys.executable, str(GATE), *args], cwd=cwd,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode


def close_claims(body: str) -> list[str]:
    """Ticket ids claimed in the body (forge.parse_claims, the one parser), a stop as a Refusal."""
    try:
        return forge.parse_claims(body)
    except forge.ForgeRefusal as exc:
        raise Refusal(str(exc)) from exc


def close_tickets(cwd: Path, pr: str, ids: list[str]) -> bool:
    """Step 1. True when a close commit was pushed."""
    todo = []
    for tid in ids:
        closed = list((cwd / "tickets" / "closed").glob(f"{tid}-*.erg"))
        if closed and "\nClosed:" in closed[0].read_text():
            continue
        if not closed and not list((cwd / "tickets").glob(f"{tid}-*.erg")):
            raise Refusal(f"claimed ticket {tid} is in neither tickets/ nor tickets/closed/")
        todo.append(tid)
    if not todo:
        return False
    erg = os.environ.get("ERG") or "tickets/erg"
    for tid in todo:
        subprocess.run([erg, "close", tid, f"autoclosed — PR #{pr}"], cwd=cwd, check=False)
        subprocess.run([erg, "archive", tid], cwd=cwd, check=False)
        git(cwd, "add", "-u", "tickets/")
        git(cwd, "add", *map(str, (cwd / "tickets" / "closed").glob(f"{tid}-*.erg")))
    msg = f"ticket({', '.join(todo)}): close and archive — PR #{pr}"
    if git(cwd, "commit", "-m", msg).returncode != 0 or git(cwd, "push", "origin", "HEAD").returncode != 0:
        raise Refusal("close commit or push failed")
    return True


def check_closed(cwd: Path, ids: list[str]) -> None:
    """No-forge step 1: hunt closes the ticket on the branch, so a claimed ticket must already be
    closed there; nothing is committed or pushed from here."""
    for tid in ids:
        closed = list((cwd / "tickets" / "closed").glob(f"{tid}-*.erg"))
        if not (closed and "\nClosed:" in closed[0].read_text()):
            raise Refusal(f"claimed ticket {tid} is not closed on the branch (no forge: close it there)")


def check_head(cwd: Path, branch: str, base_ref: str, ruled: str, remote: bool = True) -> str:
    """`base_ref` is the ref the gate and tier judge against: origin/<base>, or the local branch with no forge."""
    head = rev(cwd, "HEAD")
    if remote:
        git(cwd, "fetch", "-q", "origin")
        if head != rev(cwd, f"origin/{branch}"):
            raise Refusal("local head differs from origin/" + branch + " (sync, never merge)")
    if ruled == "-":
        if gate(cwd, "tier", "--base", base_ref, "--head", "HEAD") != 0:
            raise Refusal("no ruled head given and the request is not bookkeeping tier")
    elif head != ruled and gate(
            cwd, "tier", "--base", base_ref, "--head", "HEAD", "--since", ruled) != 0:
        raise Refusal(f"head {head[:12]} adds more than bookkeeping to the ruled tip {ruled[:12]}")
    return head


def record(cwd: Path, base_ref: str, notes_remote: str | None = None) -> None:
    """Steps 4: check the gate record, writing it when missing; one re-record on a moved base.
    `notes_remote` is where refs/notes/gate lives when it is not origin: with no remote, this
    repository's own git directory, so the record lands in refs/notes/gate where the main-update
    guard reads it (merge-gate.py `--no-push` records are never accepted for a merge)."""
    args = ("--base", base_ref, "--head", "HEAD")
    where = ("--remote", notes_remote) if notes_remote else ()
    for _ in range(2):
        rc = gate(cwd, "check", *args, *where)
        if rc == 2:
            gate(cwd, "run", *args, *where)
            rc = gate(cwd, "check", *args, *where)
        if rc != 2:
            break
    if rc == 2:
        raise Refusal("gate record stale twice (the base keeps moving)")
    if rc != 0:
        raise Refusal(f"gate check answered {rc}")


SYNCED = re.compile(r"fast-forwarded at|updated by ref")


def sync(primary: Path, base: str) -> tuple[bool, list[str]]:
    """Step 8. (synced, lines): synced only on exit 0 and a known success line."""
    try:
        done = subprocess.run([str(SYNC), str(primary), base], capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, [f"sync-local-main: could not run ({exc})"]
    lines = (done.stdout + done.stderr).strip().splitlines()
    ok = done.returncode == 0 and any(SYNCED.search(line) for line in lines)
    if not ok and not lines:
        lines = [f"sync-local-main: no output (exit {done.returncode}), not confirmed synced"]
    return ok, lines


def attribution(body: str) -> str:
    """Step 0 warning text: `ok`, `missing`, `invalid: ...` or `unchecked`; never a refusal."""
    try:
        done = subprocess.run([sys.executable, str(ROOT / "scripts" / "attribution_record.py"), "--pr-body"],
                              input=body, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "unchecked"
    out = done.stdout.strip()
    return out if done.returncode == 0 and out else (out or "unchecked")


def cleanup(cwd: Path, branch: str, head: str, base: str, base_ref: str | None = None) -> str:
    """Remove the merged worktree from outside it; retain on any doubt."""
    base_ref = base_ref or f"origin/{base}"
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    primary = Path(common).parent
    os.chdir(primary)
    git(primary, "fetch", "-q", "--prune", "origin")
    if git(primary, "merge-base", "--is-ancestor", head, base_ref).returncode != 0:
        return f"cleanup skipped: {head[:12]} not in {base_ref}"
    git(primary, "worktree", "unlock", str(cwd))
    if git(primary, "worktree", "remove", str(cwd)).returncode != 0:
        return f"cleanup skipped: worktree {cwd} not removed"
    if git(primary, "branch", "-d", branch).returncode != 0:
        return f"cleanup: branch {branch} retained"
    return f"cleaned {cwd} ({branch})"


def same_claims(body: str, ruled: list[str]) -> None:
    if sorted(close_claims(body)) != sorted(ruled):
        raise Refusal(f"close claims in the body {close_claims(body)} differ from the ruled set {sorted(ruled)}")


def claims_of(info: dict, local: bool) -> list[str]:
    """The ticket ids a request claims: body lines on a forge, commit trailers (resolve's `claims`) without."""
    if not local:
        return close_claims(info.get("body") or "")
    if info.get("claims_error"):
        raise Refusal(info["claims_error"])
    return list(info.get("claims") or [])


def land(fg, pr: str, ruled: str, base: str = "main", cwd: Path | None = None,
         do_cleanup: bool = False, out=print, ruled_claims: list[str] | None = None) -> int:
    cwd = Path(cwd or os.getcwd()).resolve()
    ruled_claims = ruled_claims or []
    start = int(time.time())
    local = bool(getattr(fg, "local", False))  # no forge: the merge is the local one (forge.NoneForge)
    info = fg.resolve(pr)
    branch = info["branch"]
    if info["state"] != "OPEN":
        raise Refusal(f"request is {info['state']}, not OPEN")
    if git(cwd, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != branch:
        raise Refusal(f"cwd is not on branch {branch}")
    remote = git(cwd, "remote", "get-url", "origin").returncode == 0
    if local:
        base = fg.base_branch(info)
        base_ref = base
        if remote:
            if git(cwd, "fetch", "-q", "origin").returncode != 0 or git(
                    cwd, "rev-parse", "--verify", "-q", f"origin/{base}").returncode != 0:
                raise Refusal(f"cannot read origin/{base} (fetch failed or the remote has no {base})")
            # The push publishes every commit under the merge, so the local base must be origin's exactly.
            if rev(cwd, base) != rev(cwd, f"origin/{base}"):
                raise Refusal(f"local {base} differs from origin/{base} (behind, ahead or diverged: sync it first)")
    else:
        base = info.get("base") or base
        base_ref = f"origin/{base}"
        out(f"attribution: {attribution(info.get('body') or '')}")
    claims = claims_of(info, local)
    if local:
        if sorted(claims) != sorted(ruled_claims):
            raise Refusal(f"close claims {claims} differ from the ruled set {sorted(ruled_claims)}")
    else:
        same_claims(info.get("body") or "", ruled_claims)
    head = check_head(cwd, branch, base_ref, ruled, remote=not local)
    if local:
        check_closed(cwd, claims)
    elif close_tickets(cwd, pr, claims):
        head = check_head(cwd, branch, base_ref, ruled)
    if info.get("draft"):
        fg.ready(pr)
    again = fg.resolve(pr)  # step 3: a body edited after approval is a stop
    if local:
        if sorted(claims_of(again, local)) != sorted(ruled_claims) or again["head"] != head:
            raise Refusal("the unit's claims or head changed since the review gate ruled")
    else:
        same_claims(again.get("body") or "", ruled_claims)
    enabled = gate(cwd, "enabled", "--base", base_ref)
    if enabled not in (0, 1):
        raise Refusal("gate configuration unreadable (never remove the file to get through)")
    gated = enabled == 0
    if gated:
        notes = None
        if local and not remote:
            notes = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
        record(cwd, base_ref, notes)
        if fg.auto_merge_armed(pr):
            fg.disarm(pr)
            if fg.auto_merge_armed(pr):
                raise Refusal("auto-merge still armed")
    try:
        try:
            fg.merge(pr, head, auto=not gated and not local)
        except forge.MergeRefused as exc:  # the adapter's class, not a Refusal
            # Definite "not merged" only when the forge refused AND the request is still OPEN at this head.
            back = fg.read_back(pr)
            if back is not None and back.split()[:2] == ["OPEN", head] and "queued" not in back:
                raise Refusal(f"forge refused the merge, request still open at {head[:12]}: {exc}") from exc
            raise PostMerge(f"forge reported a refusal ({exc}) but the read-back is {back!r}") from exc
        return after_merge(fg, pr, cwd, branch, base, head, gated, start, do_cleanup, out, local)
    except Refusal:
        raise
    except Exception as exc:
        raise PostMerge(f"{type(exc).__name__}: {exc}") from exc


def sync_local(cwd: Path, base: str) -> tuple[bool, list[str]]:
    """Step 8 with no forge. The merge already moved the local base (and pushed it when origin exists),
    so sync-local-main.sh has nothing to move and prints nothing: synced is read from the refs."""
    primary = Path(git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()).parent
    if git(primary, "remote", "get-url", "origin").returncode != 0:
        return True, [f"no remote: local {base} at {rev(primary, 'refs/heads/' + base)[:12]}"]
    ok, lines = sync(primary, base)
    git(primary, "fetch", "-q", "origin", base)
    if not ok and git(primary, "rev-parse", f"refs/heads/{base}").stdout == git(
            primary, "rev-parse", f"refs/remotes/origin/{base}").stdout != "":
        return True, lines + [f"{base} equals origin/{base}"]
    return ok, lines


def after_merge(fg, pr, cwd, branch, base, head, gated, start, do_cleanup, out, local=False) -> int:
    back = fg.read_back(pr)
    if back is None:
        raise PostMerge("read-back unreadable")
    state, oid, queued = back.split()
    if state == "OPEN" and queued == "queued" and not gated:
        out(f"{pr} queued (pending checks)")
        return QUEUED
    if not (state == "MERGED" and oid == head):
        raise PostMerge(f"read-back {back!r}, expected MERGED {head}")
    end = int(time.time())
    out(f"{pr} merge {start} {end}")
    try:
        fg.comment(pr, f"merge {head}: duration: {fmt(end - start)}")
    except Exception as exc:  # the merge landed; a lost comment is reported
        out(f"duration comment failed: {exc}")
    if local:
        synced, lines = sync_local(cwd, base)
    else:
        common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
        synced, lines = sync(Path(common).parent, base)
    for line in lines:
        out(line)
    if not synced:
        return UNSYNCED
    if do_cleanup:
        out(cleanup(cwd, branch, head, base, base if local else None))
    return OK


def main_land(fg, pr, ruled, ruled_claims, base, cwd, out=print, do_cleanup=False) -> int:
    """land() with refusals mapped to exit codes; usable by tests with a stub forge."""
    try:
        return land(fg, pr, ruled, base, cwd, do_cleanup, out, ruled_claims)
    except PostMerge as exc:
        out(f"raid_land: {pr} merge outcome unknown: {exc}; the merge was called, read the request by hand, never re-run")
        try:
            out(f"read-back now: {fg.read_back(pr)}")
        except Exception as exc2:
            out(f"read-back now: unreadable ({exc2})")
        return UNKNOWN
    except (Refusal, forge.ForgeRefusal) as exc:  # the adapter's refusals before the merge call
        print(f"raid_land: {pr} refused: {exc}", file=sys.stderr)
        return REFUSED


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("pr")
    p.add_argument("--ruled-head", required=True, help="tip the gate ruled on, or - (bookkeeping)")
    p.add_argument("--ruled-claims", required=True,
                   help="comma list of ticket ids the gate ruled on, or - for none")
    p.add_argument("--base", default="main")
    p.add_argument("--cleanup", action="store_true", help="remove the merged worktree and branch")
    a = p.parse_args(argv)
    claims = [] if a.ruled_claims == "-" else [c for c in a.ruled_claims.split(",") if c]
    return main_land(forge.get_forge(None, a.pr), a.pr, a.ruled_head, claims, a.base, None, print, a.cleanup)


if __name__ == "__main__":
    sys.exit(main())
