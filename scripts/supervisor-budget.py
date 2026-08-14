#!/usr/bin/env python3
"""Decide whether the supervisor may raise a budget or timeout, and by how much.

The convergence rule used to live as prose in nightbeat-supervisor/SKILL.md,
where an executor had to re-derive four thresholds from a paragraph every
cycle. Thresholds are exactly what a language model drifts on, so they live
here instead: the skill states the invariant, this script decides the number.

Emits JSON: {"action": "raise"|"ticket"|"hold", "value": float|None,
             "warn": bool, "reason": str}

  raise  — apply `value` to the per-project config field.
  ticket — do not raise; file the ticket whose text is in `reason`.
  hold   — nothing to do (the current value already meets the request).
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# A raise is 20% of current, never past 2x the module-level default.
RAISE_FACTOR = 1.20
HARD_CEILING_MULTIPLE = 2.0
# Above this multiple a raise still applies but is flagged for the report.
WARN_CEILING_MULTIPLE = 1.5
# This many repairs for one project+phase inside the window means the budget
# is not converging: raising again just buys another failure.
NONCONVERGENCE_REPAIRS = 3
NONCONVERGENCE_WINDOW_DAYS = 7


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def count_recent_repairs(
    journal: list[dict], project: str, phase: str, now: datetime
) -> int:
    """Repair entries for this project+phase inside the non-convergence window."""
    cutoff = now - timedelta(days=NONCONVERGENCE_WINDOW_DAYS)
    n = 0
    for entry in journal:
        if entry.get("action") != "repair":
            continue
        if entry.get("project") != project or entry.get("phase") != phase:
            continue
        ts = _parse_ts(entry.get("ts"))
        if ts is not None and ts >= cutoff:
            n += 1
    return n


def decide(
    current: float,
    default: float,
    project: str,
    phase: str,
    journal: list[dict],
    now: datetime,
) -> dict:
    """Return the raise/ticket/hold decision for one budget or timeout field."""
    repairs = count_recent_repairs(journal, project, phase, now)
    if repairs >= NONCONVERGENCE_REPAIRS:
        return {
            "action": "ticket",
            "value": None,
            "warn": False,
            "reason": (
                f"budget not converging for {project} {phase} — "
                f"{repairs} raises in {NONCONVERGENCE_WINDOW_DAYS} days, "
                f"current={current}, default={default}"
            ),
        }

    ceiling = default * HARD_CEILING_MULTIPLE
    if current >= ceiling:
        return {
            "action": "ticket",
            "value": None,
            "warn": False,
            "reason": (
                f"{project} {phase} is at the hard ceiling "
                f"({current} >= {HARD_CEILING_MULTIPLE}x default {default}); "
                f"the work does not fit the phase, so split the ticket"
            ),
        }

    proposed = min(current * RAISE_FACTOR, ceiling)
    if proposed <= current:
        return {
            "action": "hold",
            "value": None,
            "warn": False,
            "reason": f"{project} {phase} already at {current}",
        }

    warn = proposed > default * WARN_CEILING_MULTIPLE
    return {
        "action": "raise",
        "value": round(proposed, 4),
        "warn": warn,
        "reason": (
            f"raise {project} {phase} {current} -> {round(proposed, 4)}"
            + (
                f" (above {WARN_CEILING_MULTIPLE}x default {default} — "
                f"note it in the morning report)"
                if warn
                else ""
            )
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--phase", required=True, help="Phase the field belongs to (e.g. raid)"
    )
    parser.add_argument(
        "--current", type=float, required=True, help="Current per-project value"
    )
    parser.add_argument(
        "--default",
        type=float,
        required=True,
        help="Module-level default for this field; never modified",
    )
    parser.add_argument(
        "--journal",
        help="Supervisor journal JSONL (default: $HARNESS_DIR/nightbeat-supervisor-journal.jsonl)",
    )
    parser.add_argument("--now", help="ISO timestamp override, for tests")
    args = parser.parse_args()

    harness = Path(__file__).resolve().parent.parent
    journal_path = (
        Path(args.journal)
        if args.journal
        else harness / "nightbeat-supervisor-journal.jsonl"
    )
    now = _parse_ts(args.now) or datetime.now(timezone.utc)

    decision = decide(
        current=args.current,
        default=args.default,
        project=args.project,
        phase=args.phase,
        journal=_read_jsonl(journal_path),
        now=now,
    )
    json.dump(decision, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
