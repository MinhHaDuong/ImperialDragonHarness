#!/usr/bin/env python3
"""Gaze closing in one call (ticket 1227): scratch cleanup, review-worktree
removal, containment report, duration line, attribution append, result comment.

    gaze_close.py <pr> --branch <pr-branch> [--token T] [--entry-branch B]
                  --attribution-file F [--comment-file F]

Review scratch contract (ticket 0948, pinned by tests/test_review_panel_cleanup_contract.py):
every exit path runs this after the panel has consumed its artifacts; the
scratch `.panel/<pr>` and `build/panel-head` are removed only when untracked,
after `worktree-tmp-guard.py removal`; `worktree-exit-preflight.sh --removal
--branch` must pass, else the review worktree stays registered (cleanup blocked,
exit 1) and the result is ESCALATE naming the files; attribution is appended
before cleanup so a blocked cleanup still records the review, and the script
posts nothing then: the calling gaze posts the ESCALATE comment itself. A tree with real uncommitted
files is never force-removed.

`--attribution-file` is required (an empty file records nothing); a call
without it fails at argument parsing rather than skipping attribution.

The comment file must hold `{{plan_check}}` (ticket 1267) and no typed
`plan check:` line; otherwise the call exits 2 before anything is removed or
posted. The script replaces it with the first line of `seat_clock.py
plan-check` on the review panel (read before cleanup removes it), `plan check:
FAIL — manifest unreadable` when the panel cannot be read, so the verdict is
never the model's to write; the line is also printed on stdout, before
cleanup, for the caller's return text and a blocked-cleanup ESCALATE. The line is also printed on stdout, before cleanup, so a blocked cleanup
still gives the calling gaze the line to paste. It may also hold `{{duration}}` and
`{{containment}}`; both are replaced by the script's own readings. Exit: 0 clean, 1 cleanup blocked
(attribution appended, no comment posted; 2 when the append also failed), 2 also when cwd is inside the review worktree (refused, nothing removed), 2 read failure, 4 containment flagged (comment still posted).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def primary_root(cwd=None):
    """The primary checkout: parent of the shared `.git`, read from git.

    Not by cutting the toplevel at `/.claude/worktrees/`: a repository whose
    own path holds that segment (a test fixture under a worktree's TMPDIR)
    would resolve to the outer checkout. A bare-hub layout, whose common dir
    is not a `.git`, keeps the path cut.
    """
    rc, top = git("rev-parse", "--show-toplevel", cwd=cwd)
    if rc:
        raise SystemExit("gaze_close: not inside a git repository")
    rc, common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=cwd)
    if not rc and Path(common).name == ".git":
        return Path(common).parent
    return Path(top.split("/.claude/worktrees/")[0])


def cleanup(primary, pr, branch):
    """Remove scratch and the review worktree; return (ok, message)."""
    tree = primary / ".claude" / "worktrees" / f"review-{pr}"
    if not tree.is_dir():
        return True, "no review worktree"
    tmp = tree / ".tmp"
    if tmp.exists() or tmp.is_symlink():
        r = subprocess.run([sys.executable, str(HERE / "worktree-tmp-guard.py"), "removal",
                            str(primary), str(tree), "--branch", branch],
                           capture_output=True, text=True)
        if r.returncode:
            return False, (r.stderr or r.stdout).strip() or "tmp guard blocked"
    rc1, tracked_panel = git("ls-files", "--", f".panel/{pr}", cwd=tree)
    rc2, tracked_base = git("ls-files", "--", "build/panel-head", cwd=tree)
    if rc1 or rc2:
        return False, "cannot read tracked files in the review worktree"
    if not tracked_panel:
        shutil.rmtree(tree / ".panel" / str(pr), ignore_errors=True)
    if not (tree / "build").is_symlink() and not tracked_base:
        shutil.rmtree(tree / "build" / "panel-head", ignore_errors=True)
    try:
        (tree / ".panel").rmdir()
    except OSError:
        pass
    r = subprocess.run([str(HERE / "worktree-exit-preflight.sh"), "--removal",
                        "--branch", branch, str(tree)], capture_output=True, text=True)
    if r.returncode:
        return False, f"real WIP remains in {tree}: " + (r.stderr or r.stdout).strip()
    r = subprocess.run(["git", "-C", str(primary), "worktree", "remove", str(tree)],
                       capture_output=True, text=True)
    if r.returncode:
        return False, r.stderr.strip()
    return True, "review worktree removed"


def plan_check_line(primary, pr):
    """The checker's verdict line for the review panel, verbatim."""
    panel = primary / ".claude" / "worktrees" / f"review-{pr}" / ".panel" / str(pr)
    r = subprocess.run([sys.executable, str(HERE / "seat_clock.py"), "plan-check", str(panel)],
                       capture_output=True, text=True)
    first = r.stdout.splitlines()[0] if r.stdout.strip() else ""
    return first if first.startswith("plan check:") else "plan check: FAIL — manifest unreadable"


def read_entry(primary, pr):
    """State recorded by gaze_setup.py at entry (branch, porcelain lines), if any."""
    f = primary / ".claude" / "worktrees" / f"review-{pr}" / ".panel" / str(pr) / "entry-state.json"
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return {"branch": None, "status": [], "primary": []}


def containment(primary, entry_branch, entry_status=(), entry_primary=()):
    """Return (flags, report). Flags are the findings to surface; the caller's
    own uncommitted work at entry is not contamination."""
    flags = []
    _, top = git("rev-parse", "--show-toplevel")
    _, st = git("status", "--porcelain")
    _, br = git("branch", "--show-current")
    _, pst = git("-C", str(primary), "status", "--porcelain")
    new = [ln for ln in st.splitlines() if ln not in entry_status]
    if new:
        flags.append("foreign files in session worktree: " + "; ".join(new))
    newp = [ln for ln in pst.splitlines() if ln not in entry_primary]
    if newp and Path(top).resolve() != primary.resolve():
        flags.append("foreign files in primary checkout: " + "; ".join(newp))
    if entry_branch and br != entry_branch:
        flags.append(f"branch {br!r} differs from entry branch {entry_branch!r}")
    report = f"containment: toplevel={top} branch={br}; " + ("FLAGGED " + " | ".join(flags) if flags else "clean")
    return flags, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pr")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--token")
    ap.add_argument("--entry-branch")
    ap.add_argument("--attribution-file", type=Path, required=True)
    ap.add_argument("--comment-file", type=Path)
    a = ap.parse_args()
    primary = primary_root()
    tree = (primary / ".claude" / "worktrees" / f"review-{a.pr}").resolve()
    here = Path.cwd().resolve()
    if here == tree or tree in here.parents:
        print(f"gaze_close: cwd is inside the review worktree {tree}, which this call removes; "
              "run it from the invoking session worktree", file=sys.stderr)
        return 2
    comment_text = a.comment_file.read_text() if a.comment_file else None
    if comment_text is not None and ("{{plan_check}}" not in comment_text
                                     or re.search(r"^plan check:", comment_text, re.MULTILINE)):
        print("gaze_close: the comment file needs the {{plan_check}} placeholder and no typed "
              "'plan check:' line; the script writes that line", file=sys.stderr)
        return 2
    plan_line = plan_check_line(primary, a.pr)
    print(plan_line)  # the callers copy this line (comment, blocked-cleanup ESCALATE); never typed
    entry = read_entry(primary, a.pr)
    entry_branch = a.entry_branch or entry["branch"]
    status = 0
    lines = a.attribution_file.read_text().strip()
    if lines:
        r = subprocess.run([sys.executable, str(HERE / "attribution_record.py"),
                            "--append-pr", a.pr, "--append", lines,
                             "--project", primary.name],
                           capture_output=True, text=True)
        print("attribution: " + ("appended" if r.returncode == 0 else "FAILED " + r.stderr.strip()))
        if r.returncode:
            status = 2
    ok, msg = cleanup(primary, a.pr, a.branch)
    print(f"cleanup: {msg}")
    if not ok:
        print(f"/gaze cleanup blocked: {msg}; nothing posted: the calling gaze posts the "
              "ESCALATE comment (gh pr comment) naming these files", file=sys.stderr)
        return 2 if status else 1
    flags, report = containment(primary, entry_branch, entry["status"], entry["primary"])
    print(report)
    r = subprocess.run([sys.executable, str(HERE / "step_clock.py"), "end", a.token or ""],
                       capture_output=True, text=True)
    duration = r.stdout.strip() or "duration: not measured"
    print(duration)
    if a.comment_file:
        text = (comment_text.replace("{{plan_check}}", plan_line)
                .replace("{{duration}}", duration).replace("{{containment}}", report))
        r = subprocess.run(["gh", "pr", "comment", a.pr, "--body", text], capture_output=True, text=True)
        print("comment: " + ("posted" if r.returncode == 0 else "FAILED " + r.stderr.strip()))
        if r.returncode:
            status = 2
    return 4 if flags and status == 0 else status


if __name__ == "__main__":
    sys.exit(main())
