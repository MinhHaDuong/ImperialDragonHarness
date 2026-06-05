#!/usr/bin/env python3
"""
Provenance tracking and promotion/decay helpers for /dream v2.
Pure I/O — no LLM calls, no Anthropic imports.

Manages ~/.claude/memory/.provenance.json which tracks:
- Per-entry metadata: originating projects, first_seen, last_confirmed
- Promotion status
- Decay candidates (>90 days unconfirmed)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HARNESS_MEMORY = Path.home() / ".claude" / "memory"
PROVENANCE_PATH = HARNESS_MEMORY / ".provenance.json"
PROJECTS_BASE = Path.home() / ".claude" / "projects"
DECAY_DAYS = 90


def _load_provenance() -> dict:
    if PROVENANCE_PATH.exists():
        return json.loads(PROVENANCE_PATH.read_text())
    return {"entries": {}}


def _save_provenance(data: dict) -> None:
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_PATH.write_text(json.dumps(data, indent=2) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record(args):
    """Record that an entry was seen in a project consolidation."""
    data = _load_provenance()
    entries = data["entries"]

    slug = args.slug
    project = args.project
    now = _now_iso()

    if slug not in entries:
        entries[slug] = {
            "projects": [project],
            "first_seen": now,
            "last_confirmed": now,
            "promoted": False,
        }
    else:
        entry = entries[slug]
        if project not in entry["projects"]:
            entry["projects"].append(project)
        entry["last_confirmed"] = now

    _save_provenance(data)
    print(json.dumps(entries[slug], indent=2))


def candidates(args):
    """List promotion candidates: entries seen in >=2 distinct projects, not yet promoted."""
    data = _load_provenance()
    result = []
    for slug, entry in data["entries"].items():
        if len(entry["projects"]) >= 2 and not entry["promoted"]:
            result.append({"slug": slug, **entry})
    json.dump(result, sys.stdout, indent=2)
    print()


def promote(args):
    """Mark an entry as promoted."""
    data = _load_provenance()
    slug = args.slug
    if slug not in data["entries"]:
        print(f"Unknown entry: {slug}", file=sys.stderr)
        sys.exit(1)
    data["entries"][slug]["promoted"] = True
    data["entries"][slug]["promoted_at"] = _now_iso()
    _save_provenance(data)
    print(f"Promoted: {slug}")


def decay(args):
    """List harness entries not confirmed in DECAY_DAYS days."""
    data = _load_provenance()
    now = datetime.now(timezone.utc)
    flagged = []
    for slug, entry in data["entries"].items():
        if not entry.get("promoted"):
            continue
        last = datetime.fromisoformat(entry["last_confirmed"].replace("Z", "+00:00"))
        age_days = (now - last).days
        if age_days > DECAY_DAYS:
            flagged.append({
                "slug": slug,
                "last_confirmed": entry["last_confirmed"],
                "age_days": age_days,
                "projects": entry["projects"],
            })
    json.dump(flagged, sys.stdout, indent=2)
    print()


def show(args):
    """Show full provenance data."""
    data = _load_provenance()
    json.dump(data, sys.stdout, indent=2)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Provenance tracking for /dream memory promotion and decay."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    record_p = sub.add_parser("record", help="Record entry seen in a project.")
    record_p.add_argument("slug", help="Stable entry identifier (e.g. feedback_vim)")
    record_p.add_argument("project", help="Project directory name")
    record_p.set_defaults(func=record)

    candidates_p = sub.add_parser(
        "candidates", help="List promotion candidates (>=2 projects, not promoted)."
    )
    candidates_p.set_defaults(func=candidates)

    promote_p = sub.add_parser("promote", help="Mark entry as promoted to harness.")
    promote_p.add_argument("slug", help="Entry slug to promote")
    promote_p.set_defaults(func=promote)

    decay_p = sub.add_parser(
        "decay", help=f"List promoted entries unconfirmed for >{DECAY_DAYS} days."
    )
    decay_p.set_defaults(func=decay)

    show_p = sub.add_parser("show", help="Show full provenance data.")
    show_p.set_defaults(func=show)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
