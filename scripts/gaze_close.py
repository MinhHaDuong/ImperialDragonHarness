#!/usr/bin/env python3
"""Gaze closing in one call (ticket 1227): scratch cleanup, review-worktree
removal, containment report, duration line, result and attribution on notes and,
for a PR, a one-line pointer comment.

    gaze_close.py <pr> --branch <pr-branch> [--repo <primary>] [--token T] [--entry-branch B]
                  --attribution-file F [--comment-file F]

Review scratch contract (ticket 0948, pinned by tests/test_review_panel_cleanup_contract.py):
every exit path runs this after the panel has consumed its artifacts; the
scratch `.panel/<pr>` and `build/panel-head` are removed only when untracked,
after `worktree-tmp-guard.py removal`; `worktree-exit-preflight.sh --removal
--branch` must pass, else the review worktree stays registered (cleanup blocked,
exit 1) and the result is ESCALATE naming the files; the attribution lines are built
before cleanup so a blocked cleanup still records the review, as an ESCALATE answer
on notes carrying them, with its pointer on the PR. A tree with real uncommitted files is never force-removed.

`--attribution-file` is required (an empty file records nothing); a call
without it fails at argument parsing rather than skipping attribution.

`--comment-file` holds the result text (the output shape of skills/gaze/references/output.md);
it is the answer's text on notes, never posted whole. The file is scrubbed
(`gaze_seat.scrub`: emails, key- and token-shaped strings, home logins) before the
script's own lines fill the placeholders, because a quoted seat body lands there verbatim
and notes are permanent (tickets 1375, 1378).

A comment whose `seats:` field says `panel` is refused (exit 2, nothing removed or
posted) unless `seat_clock.py seats` reads `seats: panel` on the review panel: an item
other than self filed a report the plan check accepts (ticket 1287).

The `seat:` lines of the result and the `reviewer:` lines of the attribution are never typed
(ticket 1303). The comment file holds `{{seats}}`, which the script replaces with the lines
`seat_clock.py identities` builds from the plan (one name per seat: the plan item's) and the
launcher-set `worker:` headers, read before cleanup removes the panel and carried into a
blocked-cleanup ESCALATE answer; a typed `seat:` line, or a comment without the placeholder, exits 2
before anything is removed or posted. `--session-runtime` and `--session-model` (env
`IDH_SESSION_RUNTIME`, `IDH_SESSION_MODEL`) give the identity of a `self` item. The attribution file holds
only `finding: <seat> · verifiable|consider · <path:line> · adopted: yes|no` lines; the script
writes each seat's `reviewer:` line (through `attribution_record.seat_lines`) and puts the seat's
findings beneath it. A finding naming a seat absent from the plan, or a seat that did not run, or any other
typed line, exits 2 before anything is removed, recorded or posted.

The comment file must hold `{{plan_check}}` (ticket 1267) and no typed
`plan check:` line; otherwise the call exits 2 before anything is removed or
posted. The script replaces it with the first line of `seat_clock.py
plan-check` on the review panel (read before cleanup removes it), `plan check:
FAIL — manifest unreadable` when the panel cannot be read, so the verdict is
never the model's to write; the line is also printed on stdout, before
cleanup, for the caller's return text and a blocked-cleanup ESCALATE. The line is also printed on stdout, before cleanup, so a blocked cleanup
still gives the calling gaze the line to paste. It may also hold `{{duration}}` and
`{{containment}}`; both are replaced by the script's own readings. Exit: 0 clean, 1 cleanup blocked
(ESCALATE answer recorded with its attribution; 2 when the answer also failed or a seat line failed), 2 also when cwd is inside the review worktree (refused, nothing removed), 2 read failure, 4 containment flagged (result still recorded).

Every unit records its result in refs/notes/review (ticket 1273 for `branch:<name>`,
ticket 1300 for a PR number): the attribution lines and the result text go into one
`answer` entry through review_notes.py, bound to the request and run id gaze_setup froze in
the entry state (ticket 1281). The write is local and makes no network call: a remote gets
a detached background sync whose result is ignored (exit 2 only when the entry could not be
written); a blocked cleanup records an ESCALATE answer. The answer is the evidence for a PR
unit (`pr:<n>`) too (ticket 1301): the PR comment is one line, `/gaze review on notes: <review_id>,
verdict <V>`, posted best-effort after the answer (a failure is printed, never an exit code),
and none when the answer failed. Attribution lives only in the answer, every unit (ticket 1307):
this script makes no PR-body edit; landing renders the notes block into a PR body just before
the merge (`raid_land.py`, merge step 5a). The `branch:` unit's paths use `unit_key`.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import attribution_record
import forge  # same directory: the script dir is on sys.path
from gaze_seat import scrub  # the one scrub: seat text quoted into the answer is permanent on notes (ticket 1378)
import review_notes as rn

HERE = Path(__file__).resolve().parent
# A typed verdict line in any dress: indented, quoted, emphasised, any case.
TYPED_SEAT = re.compile(r"^[\s>*_`#-]*seat\s*:", re.MULTILINE | re.IGNORECASE)
FINDING = re.compile(r"finding: ([^·=:]*[^\s·=:]) · (verifiable|consider) · (.+) · adopted: (yes|no)")
TYPED_PLAN_CHECK = re.compile(r"^[\s>*_`#-]*plan check\s*[:*_]", re.MULTILINE | re.IGNORECASE)


def unit_key(pr):
    """Path segment for a review unit: a request number as is; `branch:<name>` (no forge,
    ticket 1273) as `branch-<slug>`, safe in a worktree and panel path."""
    pr = str(pr).strip()
    m = re.fullmatch(r"branch:(\S+?)(?:\s+base=\S+)?", pr)
    return "branch-" + re.sub(r"[^A-Za-z0-9._-]+", "-", m.group(1)) if m else pr


def review_unit(pr):
    """The notes unit of a PR number, `pr:<n>` (ticket 1300); None for `branch:<name>`, whose
    reviews are found by branch. Fork PRs are out of scope: the harness takes none."""
    pr = str(pr).strip()
    return None if pr.startswith("branch:") else f"pr:{pr.lstrip('#')}"


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


CLOSED_MARKER = "gaze-closed"


def closed_marker(tree):
    """`<git dir of the tree>/gaze-closed`: outside the status-visible tree, so it
    survives a refused close and bumps no mtime in the tree; None when unreadable."""
    rc, gd = git("rev-parse", "--absolute-git-dir", cwd=tree)
    return None if rc or not gd else Path(gd) / CLOSED_MARKER


def cleanup(primary, pr, branch):
    """Remove scratch and the review worktree; return (ok, message)."""
    key = unit_key(pr)
    tree = primary / ".claude" / "worktrees" / f"review-{key}"
    if not tree.is_dir():
        return True, "no review worktree"
    marker = closed_marker(tree)  # the run that held the liveness lock has ended
    if marker is not None:
        marker.write_text("closed\n")
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


def seat_block(primary, pr, runtime, model):
    """The `seat:` lines `seat_clock.py identities` builds from the review panel, as a list;
    empty when the panel cannot be read."""
    key = unit_key(pr)
    panel = primary / ".claude" / "worktrees" / f"review-{key}" / ".panel" / key
    r = subprocess.run([sys.executable, str(HERE / "seat_clock.py"), "identities", str(panel),
                        "--session-runtime", runtime or "", "--session-model", model or ""],
                       capture_output=True, text=True)
    return [ln for ln in r.stdout.splitlines() if ln.strip()] if r.returncode == 0 else []


def attribution_lines(file_text, seats):
    """(lines, failures): the answer's attribution lines from the generated seats and the finding lines of the
    attribution file. Each seat's `reviewer:` line is derived (attribution_record.seat_lines);
    its findings follow it. A file the contract refuses raises ValueError, before anything is
    removed or posted; failures are the capture failures of a derived line (an unobserved model)."""
    names = {ln.split(" · ")[0][len("seat: "):]: ln for ln in seats}
    findings = {}
    for ln in file_text.splitlines():
        if not ln.strip():
            continue
        m = FINDING.fullmatch(ln.strip())
        if not m:
            raise ValueError("the attribution file holds only `finding: <seat> · verifiable|consider · <path:line> · "
                             f"adopted: yes|no` lines; the script writes the reviewer lines: {ln.strip()}")
        seat = m.group(1)
        if seat not in names:
            raise ValueError(f"finding names seat {seat!r}, absent from the plan ({', '.join(names) or 'no seats'})")
        if not names[seat].endswith("status: ran"):
            raise ValueError(f"finding names seat {seat!r}, which did not run")
        findings.setdefault(seat, []).append(f"  finding: {m.group(2)} · {m.group(3)} · adopted: {m.group(4)}")
    out, failures = [], []
    for ln in seats:
        reviewers, failed = attribution_record.seat_lines(ln, "")
        failures += failed
        for rv in reviewers:
            out += [rv, *findings.get(ln.split(" · ")[0][len("seat: "):], [])]
    return out, failures


def read_entry(primary, pr):
    """State recorded by gaze_setup.py at entry (branch, porcelain lines), if any."""
    key = unit_key(pr)
    f = primary / ".claude" / "worktrees" / f"review-{key}" / ".panel" / key / "entry-state.json"
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return {"branch": None, "status": [], "primary": []}


def containment(primary, entry_branch, entry_status=(), entry_primary=(), session_tree=None):
    """Return (flags, report). Flags are the findings to surface; the caller's
    own uncommitted work at entry is not contamination. The session worktree is the one
    gaze_setup recorded (ticket 1356), never wherever the runtime moved the shell; an entry
    state without it (legacy) reads the cwd."""
    flags = []
    cwd = session_tree or None
    _, top = git("rev-parse", "--show-toplevel", cwd=cwd)
    _, st = git("status", "--porcelain", cwd=cwd)
    _, br = git("branch", "--show-current", cwd=cwd)
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


def seats_claims(text):
    """Every `seats:` value in a comment, lowercased: one reader for the claim check and the
    notes record (ticket 1287). A leading list, quote or heading mark, markup around the key,
    and spaces before the colon do not hide the claim."""
    plain = re.sub(r"[*_`]", "", text or "")
    return [v.lower() for v in re.findall(r"^[\s>#-]*seats\s*:\s*([A-Za-z][\w-]*)", plain, re.M | re.I)]


def seats_claim(text):
    """The value the comment claims: `panel` when any line says it, else the first, else None."""
    claims = seats_claims(text)
    return "panel" if "panel" in claims else (claims[0] if claims else None)


def record_answer(primary, pr, text, attribution, identity=None):
    """The result becomes an `answer` entry in refs/notes/review, the store verify-gate reads
    (ticket 1273; every unit since ticket 1300). `identity` is what gaze_setup froze
    (review_id, request_id, run_id): the answer binds to that request, never to one written
    while the run went on (ticket 1281). Without it (no entry state) a PR unit's review is
    found locally by its unit, a branch unit's is resolved, and the answer takes the latest
    request, only if that request is on the reviewed head: review_notes refuses otherwise.
    The write path is local (ticket 1300): no fetch, no push, no forge call; a remote gets a
    detached background sync, never waited. Returns 0, or 2 when the entry could not be written."""
    cwd = str(primary)
    identity = identity or {}
    unit = review_unit(pr)
    try:
        rid = identity.get("review_id") or (
            rn.find_unit(cwd, unit) if unit else forge.get_forge("none", pr, cwd).resolve(pr).get("review_id"))
        if not rid:
            print("answer: FAILED no review request for this branch (gaze_setup opens one)")
            return 2
        result = _field(text, "result")
        forge_read = identity.get("forge") or "read"  # gaze_setup's forge read (ticket 1308)
        if forge_read != "read" and not re.search(r"^forge:", text, re.M):
            text = text.rstrip("\n") + f"\nforge: {forge_read}\n"
        entry = rn.add(cwd, "answer", rid, {
            "forge": forge_read,
            "run_id": identity.get("run_id") or f"gz-{rn._compact(rn._now())}-{rn._hex(4)}",
            "result": result if result in ("REVIEWED", "FINDINGS", "ESCALATE") else "ESCALATE",
            "seats": seats_claim(text) or "self-only",
            "attribution": attribution.splitlines() if attribution else [],
            "text": text}, head=_field(text, "reviewed_head_sha"), skill="gaze",
            request_id=identity.get("request_id"))
    except (rn.Refusal, forge.ForgeRefusal) as exc:
        print(f"answer: FAILED {exc}")
        return 2
    started = rn.sync_background(cwd)
    print(f"answer: recorded {entry['id']} in review {rid} (local"
          f"{'; background sync started' if started else ''})")
    return 0


def pointer(primary, pr, result, identity=None):
    """Post the one-line pointer to the answer on notes (ticket 1301); best-effort, never a
    status. The review id is the one gaze_setup froze, else the PR unit's, read locally."""
    unit = review_unit(pr)
    rid = (identity or {}).get("review_id") or rn.find_unit(str(primary), unit)
    if not rid:
        print("pointer: not posted (no review id)")
        return
    try:
        forge.get_forge(None, pr, cwd=str(primary)).comment(pr, f"/gaze review on notes: {rid}, verdict {result}", strict=True)
        print("pointer: posted")
    except forge.ForgeRefusal as exc:
        print(f"pointer: not posted ({exc}); the answer on notes is the result")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pr")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--repo", type=Path, help="the reviewed project's checkout, as gaze_setup printed "
                    "`repo=` (default: the cwd's); the close never reads the project off a moved cwd")
    ap.add_argument("--token")
    ap.add_argument("--entry-branch")
    ap.add_argument("--attribution-file", type=Path, required=True)
    ap.add_argument("--comment-file", type=Path)
    ap.add_argument("--session-runtime", default=os.environ.get("IDH_SESSION_RUNTIME", ""),
                    help="runtime of this session, for a `self` seat")
    ap.add_argument("--session-model", default=os.environ.get("IDH_SESSION_MODEL", ""),
                    help="model of this session, for a `self` seat")
    a = ap.parse_args()
    primary = primary_root(cwd=a.repo)
    tree = (primary / ".claude" / "worktrees" / f"review-{unit_key(a.pr)}").resolve()
    here = Path.cwd().resolve()
    if here == tree or tree in here.parents:
        print(f"gaze_close: cwd is inside the review worktree {tree}, which this call removes; "
              "run it from the invoking session worktree", file=sys.stderr)
        return 2
    comment_text = scrub(a.comment_file.read_text()) if a.comment_file else None  # before the placeholders fill: only free text is scrubbed
    if comment_text is not None and ("{{plan_check}}" not in comment_text
                                     or TYPED_PLAN_CHECK.search(comment_text)):
        print("gaze_close: the comment file needs the {{plan_check}} placeholder and no typed "
              "'plan check:' line; the script writes that line", file=sys.stderr)
        return 2
    if comment_text is not None and ("{{seats}}" not in comment_text or TYPED_SEAT.search(comment_text)):
        print("gaze_close: the comment file needs the {{seats}} placeholder and no typed 'seat:' "
              "line; the script writes those lines from the plan and the worker headers", file=sys.stderr)
        return 2
    if seats_claim(comment_text) == "panel":  # in any case or markup, key and value
        derived = panel_reading(primary, a.pr, "seats") or "seats: self-only (panel unreadable)"
        if derived != "seats: panel":  # ticket 1287: a typed panel claim no non-self report backs
            print(f"gaze_close: the comment says seats: panel, the panel reads {derived}: no item "
                  "but self filed a report; post seats: self-only", file=sys.stderr)
            return 2
    plan_line = plan_check_line(primary, a.pr)
    print(plan_line)  # the callers copy this line (comment, blocked-cleanup ESCALATE); never typed
    seats = seat_block(primary, a.pr, a.session_runtime, a.session_model)  # before cleanup removes the panel
    for ln in seats:
        print(ln)
    try:
        lines, failures = attribution_lines(a.attribution_file.read_text(), seats)
    except ValueError as exc:
        print(f"gaze_close: {exc}", file=sys.stderr)
        return 2
    entry = read_entry(primary, a.pr)
    entry_branch = a.entry_branch or entry["branch"]
    status = 2 if failures else 0
    for failure in failures:
        print(f"attribution: seat line FAILED {failure}")
    lines = "\n".join(lines)
    local = unit_key(a.pr) != str(a.pr).strip()  # branch:<name>: the none backend
    if lines:  # every unit (ticket 1307): landing renders the block, nothing edits a PR body here
        print("attribution: carried in the answer entry")
    ok, msg = cleanup(primary, a.pr, a.branch)
    print(f"cleanup: {msg}")
    if not ok:
        answered = record_answer(primary, a.pr, f"result: ESCALATE\nreason: cleanup blocked: {msg}\n{plan_line}\n" + "\n".join(seats),
                                 lines, entry)
        if answered == 0 and not local:
            pointer(primary, a.pr, "ESCALATE", entry)
        print(f"/gaze cleanup blocked: {msg}; ESCALATE "
              + ("recorded on notes: the calling gaze returns it naming these files" if answered == 0 else
                 "NOT recorded: the calling gaze returns it naming these files"), file=sys.stderr)
        return 2 if (status or answered) else 1
    flags, report = containment(primary, entry_branch, entry["status"], entry["primary"], entry.get("session_tree"))
    print(report)
    r = subprocess.run([sys.executable, str(HERE / "step_clock.py"), "end", a.token or ""],
                       capture_output=True, text=True)
    duration = r.stdout.strip() or "duration: not measured"
    print(duration)
    if a.comment_file:
        text = (comment_text.replace("{{plan_check}}", plan_line)
                .replace("{{seats}}", "\n".join(seats)).replace("{{duration}}", duration).replace("{{containment}}", report))
        answered = record_answer(primary, a.pr, text, lines, entry)  # the evidence, every unit
        status = answered or status
        if local or answered:
            return 4 if flags and status == 0 else status
        result = _field(text, "result")
        pointer(primary, a.pr, result if result in ("REVIEWED", "FINDINGS", "ESCALATE") else "ESCALATE", entry)
    return 4 if flags and status == 0 else status


if __name__ == "__main__":
    sys.exit(main())
