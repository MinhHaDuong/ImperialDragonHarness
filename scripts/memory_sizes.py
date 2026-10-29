#!/usr/bin/env python3
"""Report memory topic sizes against the byte cap (ticket 1348).

The definitions live in memory/SMELT.md § Job of a topic and caps. A page is
measured in UTF-8 bytes over every H2 section except `Retired` and `Sources`
(the title and any text before the first H2 count). The Commission page is
never cut to fit: over the cap it is reported and does not fail the check.

Usage: memory_sizes.py [topics_dir]   (default: memory/topics)
Exit 1 when a non-Commission page is over the cap.
"""

import sys
from pathlib import Path

CAP = 4096  # bytes per topic page
INDEX_LINES = 40  # lines in memory/MEMORY.md, blanks counted
COMMISSION = "commission.md"  # provisional name, ticket 1349 may rename it
OUTSIDE = {"retired", "sources"}


def guide_bytes(text: str) -> int:
    """UTF-8 bytes of the page minus its Retired and Sources sections."""
    kept, skipping = [], False
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            skipping = line[3:].strip().lower() in OUTSIDE
        if not skipping:
            kept.append(line)
    return len("".join(kept).encode("utf-8"))


def index_ok(text: str) -> bool:
    return len(text.splitlines()) <= INDEX_LINES


def report(topics_dir: Path):
    """Yield (name, bytes, cap, status) for each topic page, status OK or OVER."""
    for path in sorted(Path(topics_dir).glob("*.md")):
        size = guide_bytes(path.read_text(encoding="utf-8"))
        yield path.name, size, CAP, "OK" if size <= CAP else "OVER"


def main(topics_dir: Path | None = None) -> int:
    if topics_dir is None:
        topics_dir = Path(__file__).resolve().parents[1] / "memory" / "topics"
    failed = False
    for name, size, cap, status in report(topics_dir):
        note = ""
        if status == "OVER" and name == COMMISSION:
            note = " (promote to rules, brood 1351)"
        elif status == "OVER":
            failed = True
        print(f"{name:42} {size:6} / {cap}  {status}{note}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
