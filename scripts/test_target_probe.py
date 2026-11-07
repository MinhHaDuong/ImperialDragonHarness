#!/usr/bin/env python3
"""On-demand test-target diagnostic, never a merge gate or a routine check.

A detached worktree protects checkout files, not paths/services a recipe can
reach outside it. Inspect those routes and prerequisites before invoking.
Reports contain paths/hashes, never the target's output; inspect its retained
log locally before quoting it. Endpoint snapshots miss write-then-restore.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import tempfile


def git(project, *args):
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True)
    if result.returncode:
        # Do not echo arbitrary git stderr (hooks/config may contain secrets).
        raise OSError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def snapshot(project):
    """Status plus tracked contents/modes; symlinks hash the link, not its target."""
    hashes = {}
    for raw in git(project, "ls-files", "-z").split(b"\0"):
        if not raw:
            continue
        name = os.fsdecode(raw)
        path = project / name
        try:
            mode = path.lstat().st_mode
            if stat.S_ISREG(mode):
                content = path.read_bytes()
            elif stat.S_ISLNK(mode):
                content = os.fsencode(os.readlink(path))
            else:
                # A target can replace a tracked file with a FIFO/socket or
                # directory. Its type already proves a change; never open it.
                hashes[name] = [mode, None]
                continue
            hashes[name] = [mode, hashlib.sha256(content).hexdigest()]
        except FileNotFoundError:
            hashes[name] = None
    return {"status": os.fsdecode(git(project, "status", "--porcelain")), "tracked": hashes}


def changes(before, after):
    return {
        "status_changed": before["status"] != after["status"],
        "tracked_changed": sorted(name for name in before["tracked"] | after["tracked"]
                                  if before["tracked"].get(name) != after["tracked"].get(name)),
    }


def probe(project, target, scratch_dir, timeout=300):
    """Run one explicit Make target at pinned HEAD; retain findings/inconclusive runs."""
    if target not in ("check-fast", "check", "test"):
        raise ValueError("select check-fast, check, or test")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    project = Path(project).resolve()
    scratch_dir = Path(scratch_dir).resolve()
    scratch_dir.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="test-target-", dir=scratch_dir))
    tree = run_dir / "worktree"
    log = run_dir / "target.log"
    report = {"project": str(project), "target": target, "status": "unavailable",
              "execution": "not-run", "worktree": str(tree), "log": str(log),
              "report": str(run_dir / "report.json")}
    try:
        report["head"] = git(project, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
        git(project, "worktree", "add", "--detach", str(tree), report["head"])
        before = snapshot(tree)
        report["before"] = before
        if before["status"]:
            raise OSError("detached checkout is not clean")
        if not (tree / "Makefile").is_file() or shutil.which("make") is None:
            raise OSError("Makefile or make unavailable; prerequisites not established")
        with log.open("wb") as output:
            process = subprocess.Popen(["make", target], cwd=tree, stdout=output,
                                       stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                       start_new_session=True)
            try:
                report["returncode"] = process.wait(timeout=timeout)
                report["execution"] = "pass" if process.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                # Kill the whole target process group: make's children must not
                # continue writing after the endpoint snapshot.
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                report["execution"] = "timeout"
        after = snapshot(tree)
        report["after"] = after
        report["changes"] = changes(before, after)
        if report["changes"]["status_changed"] or report["changes"]["tracked_changed"]:
            report["status"] = "finding"
        elif report["execution"] == "pass":
            report["status"] = "unchanged"
        else:
            report["reason"] = "target failed or timed out; prerequisite/completion evidence unavailable"
        if report["status"] == "unchanged":
            # Only an unchanged worktree is removed. Logs and report survive.
            git(project, "worktree", "remove", str(tree))
    except OSError as exc:
        report["status"] = "unavailable"
        report["reason"] = str(exc)
    Path(report["report"]).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--target", required=True, choices=("check-fast", "check", "test"))
    parser.add_argument("--scratch-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be positive and finite")
    report = probe(args.project, args.target, args.scratch_dir, args.timeout)
    # A diagnostic finding is data, never a failing gate. Invalid invocation
    # remains argparse's exit 2; unavailable evidence is explicit JSON.
    print(json.dumps(report))


if __name__ == "__main__":
    main()
