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

A comment whose `seats:` field says `panel` is refused (exit 2, nothing removed or
posted) unless `seat_clock.py seats` reads `seats: panel` on the review panel: an item
other than self filed a report the plan check accepts (ticket 1287).

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

No forge (`branch:<name>`, ticket 1273): the review unit's paths use `unit_key`; the
attribution lines and the result text go into one `answer` entry of refs/notes/review
through review_notes.py, bound to the request and run id gaze_setup froze in the entry
state (ticket 1281), published with read-back when there is a remote (exit 2 when
it is not retrievable); a blocked cleanup records an ESCALATE answer.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import forge  # same directory: the script dir is on sys.path
import review_notes as rn

HERE = Path(__file__).resolve().parent
# A typed verdict line in any dress: indented, quoted, emphasised, any case.
TYPED_PLAN_CHECK = re.compile(r"^[\s>*_`#-]*plan check\s*[:*_]", re.MULTILINE | re.IGNORECASE)


def unit_key(pr):
    """Path segment for a review unit: a request number as is; `branch:<name>` (no forge,
    ticket 1273) as `branch-<slug>`, safe in a worktree and panel path."""
    pr = str(pr).strip()
    m = re.fullmatch(r"branch:(\S+?)(?:\s+base=\S+)?", pr)
    return "branch-" + re.sub(r"[^A-Za-z0-9._-]+", "-", m.group(1)) if m else pr


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
    key = unit_key(pr)
    tree = primary / ".claude" / "worktrees" / f"review-{key}"
    if not tree.is_dir():
        return True, "no review worktree"
    tmp = tree / ".tmp"
    if tmp.exists() or tmp.is_symlink():
        r = subprocess.run([sys.executable, str(HERE / "worktree-tmp-guard.py"), "removal",
                            str(primary), str(tree), "--branch", branch],
                           capture_output=True, text=True)
        if r.returncode:
            return False, (r.stderr or r.stdout).strip() or "tmp guard blocked"
    rc1, tracked_panel = git("ls-files", "--", f".panel/{key}", cwd=tree)
    rc2, tracked_base = git("ls-files", "--", "build/panel-head", cwd=tree)
    if rc1 or rc2:
        return False, "cannot read tracked files in the review worktree"
    if not tracked_panel:
        shutil.rmtree(tree / ".panel" / key, ignore_errors=True)
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


def panel_reading(primary, pr, mode):
    """First stdout line of `seat_clock.py <mode>` on the review panel."""
    key = unit_key(pr)
    panel = primary / ".claude" / "worktrees" / f"review-{key}" / ".panel" / key
    r = subprocess.run([sys.executable, str(HERE / "seat_clock.py"), mode, str(panel)],
                       capture_output=True, text=True)
    return r.stdout.splitlines()[0] if r.stdout.strip() else ""


def plan_check_line(primary, pr):
    """The checker's verdict line for the review panel, verbatim."""
    first = panel_reading(primary, pr, "plan-check")
    return first if first.startswith("plan check:") else "plan check: FAIL — manifest unreadable"


def read_entry(primary, pr):
    """State recorded by gaze_setup.py at entry (branch, porcelain lines), if any."""
    key = unit_key(pr)
    f = primary / ".claude" / "worktrees" / f"review-{key}" / ".panel" / key / "entry-state.json"
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


def _field(text, name):
    m = re.search(rf"^{name}:\s*(\S+)", text, re.MULTILINE)
    return m.group(1) if m else None


def answer_scope(text):
    """Spec §4: a narrow intent is never widened. `scope:` when given, else full only for the
    default intent (`intent: default`); any other intent, or none, records delta."""
    scope = _field(text, "scope")
    if scope in ("full", "delta"):
        return scope
    first = re.search(r"^intent:[ \t]*(.*?)[ \t]*$", text, re.MULTILINE)  # the field, not a quote below
    value = first.group(1) if first else ""
    return "full" if value == "default" or value.startswith("default:") else "delta"


def record_answer(primary, pr, text, attribution, identity=None):
    """No forge (ticket 1273): the result becomes an `answer` entry in refs/notes/review, the
    store verify-gate reads, then is published with read-back when there is a remote.
    `identity` is what gaze_setup froze (review_id, request_id, run_id): the answer binds to
    that request, never to one written while the run went on (ticket 1281). Without it (no
    entry state) the review is resolved and the answer takes the latest request, only if
    that request is on the reviewed head: review_notes refuses otherwise.
    Returns 0, or 2 when the entry could not be written or its publication not verified."""
    cwd = str(primary)
    identity = identity or {}
    try:
        rid = identity.get("review_id") or forge.get_forge("none", pr, cwd).resolve(pr).get("review_id")
        if not rid:
            print("answer: FAILED no review request for this branch (gaze_setup opens one)")
            return 2
        result = _field(text, "result")
        scope = answer_scope(text)
        cov = {"scope": scope}
        if scope == "delta":  # spec §4: a delta counts only through the answer it carries (ticket 1274)
            cov["carried"] = rn.carry_target(cwd, rid)
        entry = rn.add(cwd, "answer", rid, {
            "run_id": identity.get("run_id") or f"gz-{rn._compact(rn._now())}-{rn._hex(4)}",
            "result": result if result in ("REVIEWED", "FINDINGS", "ESCALATE") else "ESCALATE",
            "seats": _field(text, "seats") or "self-only",
            "coverage": cov,
            "attribution": attribution.splitlines() if attribution else [],
            "text": text}, head=_field(text, "reviewed_head_sha"), skill="gaze",
            request_id=identity.get("request_id"))
        level = rn.publish(cwd, [entry["id"]])
    except (rn.Refusal, forge.ForgeRefusal) as exc:
        print(f"answer: FAILED {exc}")
        return 2
    print(f"answer: recorded {entry['id']} in review {rid} ({level})")
    remote = rn.setup(cwd) is not None
    return 2 if remote and level != "retrievable" else 0


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
    tree = (primary / ".claude" / "worktrees" / f"review-{unit_key(a.pr)}").resolve()
    here = Path.cwd().resolve()
    if here == tree or tree in here.parents:
        print(f"gaze_close: cwd is inside the review worktree {tree}, which this call removes; "
              "run it from the invoking session worktree", file=sys.stderr)
        return 2
    comment_text = a.comment_file.read_text() if a.comment_file else None
    if comment_text is not None and ("{{plan_check}}" not in comment_text
                                     or TYPED_PLAN_CHECK.search(comment_text)):
        print("gaze_close: the comment file needs the {{plan_check}} placeholder and no typed "
              "'plan check:' line; the script writes that line", file=sys.stderr)
        return 2
    if comment_text is not None and _field(comment_text, "seats") == "panel":
        derived = panel_reading(primary, a.pr, "seats") or "seats: self-only (panel unreadable)"
        if derived != "seats: panel":  # ticket 1287: a typed panel claim no non-self report backs
            print(f"gaze_close: the comment says seats: panel, the panel reads {derived}: no item "
                  "but self filed a report; post seats: self-only", file=sys.stderr)
            return 2
    plan_line = plan_check_line(primary, a.pr)
    print(plan_line)  # the callers copy this line (comment, blocked-cleanup ESCALATE); never typed
    entry = read_entry(primary, a.pr)
    entry_branch = a.entry_branch or entry["branch"]
    status = 0
    lines = a.attribution_file.read_text().strip()
    local = unit_key(a.pr) != str(a.pr).strip()  # branch:<name>: the none backend
    if local and lines:
        print("attribution: carried in the answer entry (no forge)")
    elif lines:
        r = subprocess.run([sys.executable, str(HERE / "attribution_record.py"),
                            "--append-pr", a.pr, "--append", lines,
                             "--project", primary.name],
                           capture_output=True, text=True)
        print("attribution: " + ("appended" if r.returncode == 0 else "FAILED " + r.stderr.strip()))
        if r.returncode:
            status = 2
    ok, msg = cleanup(primary, a.pr, a.branch)
    print(f"cleanup: {msg}")
    if not ok and local:
        status = record_answer(primary, a.pr, f"result: ESCALATE\nreason: cleanup blocked: {msg}\n{plan_line}",
                               lines, entry) or status
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
        if local:
            status = record_answer(primary, a.pr, text, lines, entry) or status
            return 4 if flags and status == 0 else status
        try:
            forge.get_forge(None, a.pr).comment(a.pr, text, strict=True)
            print("comment: posted")
            if re.search(r"^seat: ", text, re.M):  # derive the reviewer lines the file lacks from the posted result (ticket 1286)
                r = subprocess.run([sys.executable, str(HERE / "attribution_record.py"),
                                    "--seats-pr", a.pr, "--project", primary.name],
                                   capture_output=True, text=True)
                print("attribution: " + ("seats appended" if r.returncode == 0 else "seats FAILED " + r.stderr.strip()))
                if r.returncode:
                    status = 2
        except forge.ForgeRefusal as exc:
            print("comment: FAILED " + str(exc))
            status = 2
    return 4 if flags and status == 0 else status


if __name__ == "__main__":
    sys.exit(main())
