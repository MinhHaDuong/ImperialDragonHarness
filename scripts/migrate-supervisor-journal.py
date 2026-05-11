#!/usr/bin/env python3
"""One-time migration: merge logs/nightbeat-supervisor-journal.jsonl into root.

Run once to consolidate entries that a supervisor cycle mistakenly wrote to
~/.claude/logs/ instead of ~/.claude/ (ticket 0116).

After running, the logs/ file is left in place but can be removed safely:
  rm ~/.claude/logs/nightbeat-supervisor-journal.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
ROOT_JOURNAL = HARNESS_DIR / "nightbeat-supervisor-journal.jsonl"
LOGS_JOURNAL = HARNESS_DIR / "logs" / "nightbeat-supervisor-journal.jsonl"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"Warning: skipping malformed line in {path}: {line!r}")
    return rows


def main() -> None:
    root_entries = _load(ROOT_JOURNAL)
    logs_entries = _load(LOGS_JOURNAL)

    if not logs_entries:
        print(f"Nothing to migrate: {LOGS_JOURNAL} is empty or absent.")
        return

    # Dedup key: (ts, action) — enough to identify duplicates
    existing_keys: set[tuple[str, str]] = {
        (e.get("ts", ""), e.get("action", "")) for e in root_entries
    }

    new_entries = [
        e
        for e in logs_entries
        if (e.get("ts", ""), e.get("action", "")) not in existing_keys
    ]

    if not new_entries:
        print(f"All {len(logs_entries)} logs/ entries already present in root journal.")
        return

    # Append new entries to root journal
    with ROOT_JOURNAL.open("a") as f:
        for entry in new_entries:
            f.write(json.dumps(entry) + "\n")

    print(
        f"Migrated {len(new_entries)} of {len(logs_entries)} entries from\n"
        f"  {LOGS_JOURNAL}\n  → {ROOT_JOURNAL}\n"
        f"({len(logs_entries) - len(new_entries)} already present, skipped)"
    )
    print(f"\nYou may now remove the stale logs/ file:\n  rm {LOGS_JOURNAL}")


if __name__ == "__main__":
    main()
