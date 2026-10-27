#!/usr/bin/env python3
"""Audit the last 24 hours of main: does each commit that entered it carry a gate receipt?

Ticket 1179 (after 1157, tracker 1045). Stateless and git-only: no forge, no
watermark, no stored state, except that --after runs the gate's check set and
pushes its record as a note to refs/notes/gate. It reads the repository it runs in and prints
nothing when the base declares no gate (no `.merge-gate.json` at the tip, or
`"gate": "off"`).

The receipt is the merge gate's record (scripts/merge-gate.py): a note in
refs/notes/gate on the candidate, the deterministic --no-ff merge of a branch
head into the base tip. The forge's merge commit M is another object (other
author, date, message), so for a merge with exactly two parents (P1, P2) the
audit rebuilds the candidate from (P1, P2) with merge-gate.py's own function,
requires M's tree to be the candidate's, and reads the note there; the latest
entry for that candidate decides, under the before-merge scope that P1
declares (ticket 1245: its "before" set, or the full set without one). A receipt
made on another base tip names another candidate, so a merge whose first
parent moved after the gate ran reads as a finding. A single-parent commit is
read as before: the note on the commit itself. A parentless commit is a
finding when its own tree declares the gate (an orphan cannot be gated).

Each commit is `ok`, `finding`, or `ungated` (its first parent declared no
gate: the commit predates the gate). Window: git cannot tell when a commit
entered main, only its committer date. The audit walks the newest --max-count
first-parent commits of --ref and covers every one from the tip down to the
deepest dated in the last 24 hours, so an old-dated commit above a recent one
is covered and cannot hide it. Work stops after --time-limit seconds. Exit 0:
no finding. 1: a finding. 2: could not look in full; a range cut by a cap says
so on stdout and exits 2 whatever it found, so a cut never reads as an
all-clear.

With --after (ticket 1244), it also lists the first-parent tips newer than
the newest one carrying an after-merge record (a record covers the tips its
runner passed over) and runs `merge-gate.py run-after` on the latest; a red
run is a finding. So is a gap tip committed more than --stale-minutes ago
(ticket 1265): hooks/reference-transaction starts the runner on every move of
main, so a tip that old without a record means the runner never started or
died.

Never run in the merge path: run by hand, or from the end-of-day wrap-up with
--summary (one line).
"""

import argparse
import importlib.util
import io
import logging
import os
import sys
import time
from pathlib import Path

WINDOW_SECONDS = 24 * 3600
log = logging.getLogger("main_sweep")


def _merge_gate():
    """scripts/merge-gate.py: the one builder of the candidate and reader of receipts."""
    spec = importlib.util.spec_from_file_location("merge_gate", Path(__file__).with_name("merge-gate.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mg = _merge_gate()


def _tree(oid: str) -> str:
    return mg.git("rev-parse", f"{oid}^{{tree}}").stdout.strip()


def _verdict(sha: str, parents: list[str], config: dict) -> tuple[str, str]:
    if len(parents) == 1:
        text = mg.read_note(sha)
        entries = mg.parse_note(text)
        if entries and all(mg.is_after_entry(e) for e in entries):  # ticket 1244: never admits a commit
            return "finding", "single-parent commit with an after-merge record only"
        if text.strip():
            return "ok", "note on the commit itself"
        return "finding", "single-parent commit without a note"
    if len(parents) != 2:
        return "finding", f"merge of {len(parents)} parents: the gate covers two"
    try:
        target = mg.candidate(parents[0], parents[1])
    except mg.GateError as exc:
        return "finding", f"candidate cannot be rebuilt: {exc}"
    if _tree(target) != _tree(sha):
        return "finding", f"tree differs from candidate {target[:12]}"
    code, reason = mg.decide(mg.parse_note(mg.read_note(target)), target, mg.accepted_scopes(config))
    if code == mg.PASS:
        return "ok", reason
    if code == mg.MISSING:
        return "finding", f"no receipt on candidate {target[:12]} (none, or made on another base)"
    return "finding", reason


def classify(sha: str) -> dict:
    parents = mg.git("rev-list", "--parents", "-n", "1", sha).stdout.split()[1:]
    subject = mg.git("log", "-1", "--format=%s", sha).stdout.strip()
    result = {"sha": sha, "subject": subject}
    config = mg.load_config(parents[0] if parents else sha)
    if config is None:
        result.update(status="ungated", reason="its base declares no gate")
    elif not parents:
        result.update(status="finding", reason="parentless commit on a gated base")
    else:
        status, reason = _verdict(sha, parents, config)
        result.update(status=status, reason=reason)
    return result


def window(ref: str, max_count: int) -> tuple[list[str], list[str]]:
    """(commits to audit, newest first; reasons the range was cut)."""
    walked = [line.split() for line in mg.git(
        "log", "--first-parent", f"--max-count={max_count + 1}", "--format=%H %ct", ref
    ).stdout.splitlines()]
    cutoff = time.time() - WINDOW_SECONDS
    recent = [i for i, (_, stamp) in enumerate(walked) if int(stamp) >= cutoff]
    commits = [sha for sha, _ in walked[: recent[-1] + 1]] if recent else []
    if len(commits) > max_count:
        return commits[:max_count], [f"range cut at --max-count {max_count}"]
    return commits, []


def audit(ref: str, max_count: int, time_limit: float) -> tuple[list[dict], list[str]]:
    """(results newest first, reasons the range was cut)."""
    commits, cut = window(ref, max_count)
    results, start = [], time.monotonic()
    for sha in commits:
        if time.monotonic() - start >= time_limit:
            cut.append(f"range cut at --time-limit {time_limit:g} s after {len(results)} commit(s)")
            break
        results.append(classify(sha))
    return results, cut


def after_gaps(tip: str, max_count: int) -> tuple[list[tuple[str, int, str]], str]:
    """First-parent tips above the newest one with an after-merge record (ticket 1244).

    A record covers its tip and every tip below it that it passed over, so
    the gaps are the tips newer than the newest recorded one, newest first.
    Returns (gaps as (sha, committer time, subject), what bounds them).
    """
    walked = mg.git("log", "--first-parent", f"--max-count={max_count}", "--format=%H %ct %s", tip).stdout.splitlines()
    gaps = []
    for line in walked:
        sha, stamp, subject = (line.split(" ", 2) + [""])[:3]
        if mg.after_entries(sha):
            return gaps, f"since the after-merge record on {sha[:12]}"
        gaps.append((sha, int(stamp), subject))
    return gaps, f"none in the newest {max_count} first-parent commits"


def after_audit(tip: str, ref: str, max_count: int, summary: bool, stale_minutes: float = 60) -> tuple[list[str], int]:
    """Report the gaps, flag the stale ones, and run the full set on the latest tip when there is one."""
    gaps, bound = after_gaps(tip, max_count)
    lines = [] if summary else [f"after-gap {sha[:12]}  {subject[:60]}" for sha, _, subject in gaps]
    if not gaps:
        return lines + [f"after: every tip carries an after-merge record ({bound})"], 0
    remote, _, branch = ref.partition("/") if ref.startswith("origin/") else ("origin", "", ref)
    actor = mg.actor_line("", "", "")
    command = f"main_sweep --after: merge-gate run-after --remote {remote} --ref {branch}"
    code = mg.run_after(remote, branch, actor, command) if not summary else _quiet_run(remote, branch, actor, command)
    head = f"after: {len(gaps)} tip(s) without an after-merge record ({bound})"
    cutoff = time.time() - stale_minutes * 60
    stale = [sha for sha, stamp, _ in gaps if stamp < cutoff]
    if stale:  # the hook should have started a runner on each of them long ago
        head += f", {len(stale)} older than {stale_minutes:g} min: {stale[0][:12]}"
    if code == mg.BUSY:
        return lines + [f"{head}; not run: another runner holds the lock and will cover the newest tip"], int(bool(stale))
    lines.append(f"{head}; ran on {gaps[0][0][:12]}: {'environment' if code == mg.ENV else 'red' if code else 'green'}")
    return lines, code or int(bool(stale))


def _quiet_run(remote: str, branch: str, actor: str, command: str) -> int:
    """run_after with its own text and its checks' output kept off fds 1 and 2 (the summary is one line).

    The checks are subprocesses inheriting the file descriptors, so swapping
    sys.stdout alone would not hold them; the record on the tip keeps the detail.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    saved = [os.dup(fd) for fd in (1, 2)]
    real, sys.stdout = sys.stdout, io.StringIO()
    try:
        with open(os.devnull, "w") as sink:
            for fd in (1, 2):
                os.dup2(sink.fileno(), fd)
            return mg.run_after(remote, branch, actor, command)
    finally:
        for fd, copy in zip((1, 2), saved):
            os.dup2(copy, fd)
            os.close(copy)
        sys.stdout = real


def render(results: list[dict], cut: list[str], summary: bool) -> str:
    findings = [r for r in results if r["status"] == "finding"]
    if summary:
        line = f"main audit: {len(results)} commits in the last 24 h, {len(findings)} without a gate receipt"
        line += f": {findings[0]['sha'][:12]}" if findings else ""
        return line + "".join(f"; {c}" for c in cut)
    lines = [f"{r['status']:8} {r['sha'][:12]}  {r['subject'][:60]}  [{r['reason']}]" for r in results]
    lines += cut
    lines.append(f"summary: {len(results)} commit(s) in the last 24 h, {len(findings)} finding(s)")
    return "\n".join(lines)


def _positive(kind):
    def parse(text):
        value = kind(text)
        if value < (1 if kind is int else 0):
            raise argparse.ArgumentTypeError(f"out of range: {text}")
        return value
    return parse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ref", default="origin/main", help="branch to audit (default origin/main)")
    p.add_argument("--max-count", type=_positive(int), default=200,
                   help="hard cap on first-parent commits walked (default 200, at least 1)")
    p.add_argument("--time-limit", type=_positive(float), default=60,
                   help="seconds of work before the range is cut (default 60)")
    p.add_argument("--fetch", action="store_true", help="fetch origin main and refs/notes/gate first")
    p.add_argument("--summary", action="store_true", help="one line, for the end-of-day wrap-up")
    p.add_argument("--after", action="store_true",
                   help="also report tips with no after-merge record and run the full set on the latest one")
    p.add_argument("--stale-minutes", type=_positive(float), default=60,
                   help="with --after, a tip without a record committed longer ago is a finding (default 60)")
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    fetch_error = None
    if args.fetch:  # before the gate check, so a gate turned on upstream is seen
        try:
            mg.git("fetch", "--quiet", "origin", "main")
        except mg.GateError as exc:
            fetch_error = exc
    tip = mg.rev(args.ref)
    if mg.load_config(tip or "HEAD") is None:
        return 0  # the base declares no gate: nothing to audit, nothing printed
    if fetch_error:
        raise fetch_error
    if not tip:
        raise mg.GateError(f"unknown ref {args.ref}")
    if args.fetch:
        mg.fetch_notes("origin")
    results, cut = audit(tip, args.max_count, args.time_limit)
    text = render(results, cut, args.summary)
    after_code = 0
    if args.after:
        lines, after_code = after_audit(tip, args.ref, args.max_count, args.summary, args.stale_minutes)
        text += "; " + lines[-1] if args.summary else "\n" + "\n".join(lines)
    sys.stdout.write(text + "\n")
    if cut:
        return 2
    return 1 if after_code or any(r["status"] == "finding" for r in results) else 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="main_sweep: %(message)s")
    args = parse_args(argv)
    try:
        return run(args)
    except (mg.GateError, OSError, ValueError) as exc:
        if args.summary:
            sys.stdout.write(f"main audit: not checked ({exc})\n")
        log.error("could not look: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
