#!/usr/bin/env python3
"""Audit the last 24 hours of main: does each commit that entered it carry a gate receipt?

Ticket 1179 (after 1157, tracker 1045). Stateless and git-only: no forge, no
watermark, no stored state. It reads the repository it runs in and prints
nothing when the base declares no gate (no `.merge-gate.json` at the tip, or
`"gate": "off"`).

The receipt is the merge gate's record (scripts/merge-gate.py): a note in
refs/notes/gate on the candidate, the deterministic --no-ff merge of a branch
head into the base tip. The forge's merge commit M is another object (other
author, date, message), so for a merge with parents (P1, P2) the audit rebuilds
the candidate from (P1, P2) with merge-gate.py's own function and reads the
note there; the latest entry for that candidate decides, under the scope that
P1 declares. A receipt made on another base tip names another candidate, so a
merge whose first parent moved after the gate ran reads as a finding. A
single-parent commit is read as before: the note on the commit itself.

Each commit is `ok`, `finding`, or `ungated` (its first parent declared no
gate: the commit predates the gate). Window: the first-parent commits of
--ref committed in the last 24 hours, at most --max-count of them and
--time-limit seconds of work. Exit 0: no finding. 1: a finding. 2: could not
look in full; a range cut by a cap says so on stdout and exits 2 whatever it
found, so a cut never reads as an all-clear.

Never run in the merge path: run by hand, or from the end-of-day wrap-up with
--summary (one line).
"""

import argparse
import importlib.util
import logging
import sys
import time
from pathlib import Path

WINDOW = "24 hours ago"
log = logging.getLogger("main_sweep")


def _merge_gate():
    """scripts/merge-gate.py: the one builder of the candidate and reader of receipts."""
    spec = importlib.util.spec_from_file_location("merge_gate", Path(__file__).with_name("merge-gate.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mg = _merge_gate()


def classify(sha: str) -> dict:
    parents = mg.git("rev-list", "--parents", "-n", "1", sha).stdout.split()[1:]
    subject = mg.git("log", "-1", "--format=%s", sha).stdout.strip()
    result = {"sha": sha, "subject": subject, "status": "finding", "reason": ""}
    config = mg.load_config(parents[0]) if parents else None
    if config is None:
        result.update(status="ungated", reason="its base declares no gate")
        return result
    if len(parents) == 1:
        if mg.read_note(sha).strip():
            result.update(status="ok", reason="note on the commit itself")
        else:
            result["reason"] = "single-parent commit without a note"
        return result
    try:
        target = mg.candidate(parents[0], parents[1])
    except mg.GateError as exc:
        result["reason"] = f"candidate cannot be rebuilt: {exc}"
        return result
    code, reason = mg.decide(mg.parse_note(mg.read_note(target)), target, mg.scope_line(config))
    if code == mg.PASS:
        result.update(status="ok", reason=reason)
    elif code == mg.MISSING:
        result["reason"] = f"no receipt on candidate {target[:12]} (none, or made on another base)"
    else:
        result["reason"] = reason
    return result


def audit(ref: str, max_count: int, time_limit: float) -> tuple[list[dict], list[str]]:
    """(results newest first, reasons the range was cut)."""
    commits = mg.git("rev-list", "--first-parent", f"--since={WINDOW}",
                     f"--max-count={max_count + 1}", ref).stdout.split()
    cut = []
    if len(commits) > max_count:
        commits = commits[:max_count]
        cut.append(f"range cut at --max-count {max_count}")
    results, start = [], time.monotonic()
    for sha in commits:
        if time.monotonic() - start >= time_limit:
            cut.append(f"range cut at --time-limit {time_limit:g} s after {len(results)} commit(s)")
            break
        results.append(classify(sha))
    return results, cut


def render(results: list[dict], cut: list[str], summary: bool) -> str:
    findings = [r for r in results if r["status"] == "finding"]
    if summary:
        line = f"main audit: {len(results)} merges in the last 24 h, {len(findings)} without a gate receipt"
        line += f": {findings[0]['sha'][:12]}" if findings else ""
        return line + "".join(f"; {c}" for c in cut)
    lines = [f"{r['status']:8} {r['sha'][:12]}  {r['subject'][:60]}  [{r['reason']}]" for r in results]
    lines += cut
    lines.append(f"summary: {len(results)} commit(s) in the last 24 h, {len(findings)} finding(s)")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ref", default="origin/main", help="branch to audit (default origin/main)")
    p.add_argument("--max-count", type=int, default=200, help="hard cap on commits (default 200)")
    p.add_argument("--time-limit", type=float, default=60, help="seconds of work before the range is cut")
    p.add_argument("--fetch", action="store_true", help="fetch origin main and refs/notes/gate first")
    p.add_argument("--summary", action="store_true", help="one line, for the end-of-day wrap-up")
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    # Gate declared? Read before any fetch, so a project without the gate is
    # left alone and prints nothing.
    if mg.load_config(mg.rev(args.ref) or "HEAD") is None:
        return 0
    if args.fetch:
        mg.git("fetch", "--quiet", "origin", "main")
        mg.fetch_notes("origin")
    tip = mg.rev(args.ref)
    if not tip:
        raise mg.GateError(f"unknown ref {args.ref}")
    if mg.load_config(tip) is None:
        return 0
    results, cut = audit(tip, args.max_count, args.time_limit)
    sys.stdout.write(render(results, cut, args.summary) + "\n")
    if cut:
        return 2
    return 1 if any(r["status"] == "finding" for r in results) else 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="main_sweep: %(message)s")
    args = parse_args(argv)
    try:
        return run(args)
    except (mg.GateError, OSError) as exc:
        if args.summary:
            sys.stdout.write(f"main audit: not checked ({exc})\n")
        log.error("could not look: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
