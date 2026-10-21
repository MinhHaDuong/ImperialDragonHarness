#!/usr/bin/env python3
"""Treatment follow-up (ticket 1170): did a fix move the error class it treats?

Zero-LLM, standard-library-only. Reads the daily series of
scripts/trace-friction.py (its --json output) and the closed tickets that
declare a treatment, and emits one verdict per treatment.

Convention (docs/trace-treatments.md): a closed ticket names the class it
treats and its baseline in two body lines, read as declared fields, never
inferred from prose:

    Treats: no_such_tool
    Baseline: 2026-10-20=26 2026-10-21=14

The merge date is the date of the commit that added the ticket under
tickets/closed/ on the first-parent history of origin/main. The rate is the
mean errors per day of the class: baseline days before, series days strictly
after the merge date. Days with no transcripts are absent, not zero.

Verdicts: unmeasured (no baseline, no merge date, unknown class, or no series
day after the merge), too_few_days (fewer than 7 days after), then improved
(rate after <= half of before), worse (>= 1.5x before), unchanged otherwise.
The report only proposes; it closes and reopens nothing.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CAUSES = ("worktree_guard", "no_such_tool", "write_outside_worktree", "other")
MIN_DAYS_AFTER = 7
IMPROVED_RATIO = 0.5
WORSE_RATIO = 1.5

TREATS_RE = re.compile(r"^Treats:[ \t]*(\w+)[ \t]*$", re.MULTILINE)
BASELINE_RE = re.compile(r"^Baseline:[ \t]*(.+)$", re.MULTILINE)
PAIR_RE = re.compile(r"(\d{4}-\d{2}-\d{2})=(\d+)")


def parse_treatment(text: str) -> tuple[str | None, dict[str, int]]:
    """Return (class, {date: count}) from the declared body lines only."""
    if "--- body ---" not in text:
        raise ValueError("ticket has no '--- body ---' marker; cannot read Treats:")
    body = text.split("--- body ---", 1)[1]
    m = TREATS_RE.search(body)
    b = BASELINE_RE.search(body)
    baseline = {d: int(n) for d, n in PAIR_RE.findall(b.group(1))} if b else {}
    return (m.group(1) if m else None), baseline


def merge_date(root: Path, path: str, ref: str | None = "origin/main") -> str | None:
    """Date (YYYY-MM-DD) of the first-parent commit that added `path`."""
    cmd = ["git", "-C", str(root), "log", "--first-parent", "-M",
           "--diff-filter=AR", "--format=%cs", ref or "HEAD", "--", path]  # fmt: skip
    out = subprocess.run(cmd, capture_output=True, text=True)
    lines = out.stdout.split()
    return lines[-1] if out.returncode == 0 and lines else None


def find_treatments(root: Path, ref: str | None = "origin/main") -> list[dict]:
    found = []
    for f in sorted((root / "tickets" / "closed").glob("*.erg")):
        cls, baseline = parse_treatment(f.read_text(encoding="utf-8"))
        if cls is None:
            continue
        rel = f.relative_to(root).as_posix()
        found.append({
            "id": f.name.split("-", 1)[0], "file": rel, "cls": cls,
            "baseline": baseline, "merge": merge_date(root, rel, ref),
        })  # fmt: skip
    return found


def _mean(values: list[int]) -> float:
    return sum(values) / len(values)


def evaluate(t: dict, daily: list[dict]) -> dict:
    """Verdict for one treatment against the daily series."""
    res = {"id": t["id"], "cls": t["cls"], "merge": t["merge"],
           "days_before": len(t["baseline"]), "days_after": 0,
           "rate_before": None, "rate_after": None, "verdict": "unmeasured"}  # fmt: skip
    if t["cls"] not in CAUSES or not t["baseline"] or not t["merge"]:
        return res
    after = [d["errors_by_cause"].get(t["cls"], 0) for d in daily
             if d["date"] > t["merge"]]  # fmt: skip
    res["days_after"] = len(after)
    res["rate_before"] = round(_mean(list(t["baseline"].values())), 2)
    if not after:
        return res
    res["rate_after"] = round(_mean(after), 2)
    before, now = res["rate_before"], res["rate_after"]
    if len(after) < MIN_DAYS_AFTER:
        res["verdict"] = "too_few_days"
    elif now <= before * IMPROVED_RATIO and now < before:
        res["verdict"] = "improved"
    elif now >= before * WORSE_RATIO and now > before:
        res["verdict"] = "worse"
    else:
        res["verdict"] = "unchanged"
    return res


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Before/after verdict per treatment.")
    ap.add_argument("--friction-json", type=Path, required=True,
                    help="Output of trace-friction.py --json")  # fmt: skip
    ap.add_argument("--root", type=Path, default=root, help="Harness checkout")
    ap.add_argument("--ref", default="origin/main", help="History to date merges on")
    ap.add_argument("--json", action="store_true", help="Print JSON")
    args = ap.parse_args()
    daily = json.loads(args.friction_json.read_text(encoding="utf-8"))["daily"]
    rows = [evaluate(t, daily) for t in find_treatments(args.root, args.ref)]
    if args.json:
        json.dump(rows, sys.stdout, indent=2)
        print()
        return
    print("ticket  class                   merge       before(d)  after(d)  verdict")
    for r in rows:
        b = "-" if r["rate_before"] is None else f"{r['rate_before']:.2f}"
        a = "-" if r["rate_after"] is None else f"{r['rate_after']:.2f}"
        print(f"{r['id']:6}  {r['cls']:22}  {str(r['merge']):10}  "
              f"{b:>6}({r['days_before']:2d})  {a:>6}({r['days_after']:2d})  "
              f"{r['verdict']}")  # fmt: skip


if __name__ == "__main__":
    main()
