#!/usr/bin/env python3
"""Fail closed unless every line of a review panel manifest names its seat's model.

A manifest line is `perspective<TAB>model<TAB>family<TAB>reason`, written by the
orchestrator before launching. An empty model, family or reason means the launch
choice was not made, which is the failure the manifest exists to expose.
"""

import sys
from pathlib import Path

FIELDS = ("perspective", "model", "family", "reason")


def check(text: str) -> list[str]:
    problems = []
    seen = 0
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        seen += 1
        cells = line.split("\t")
        if len(cells) != len(FIELDS):
            problems.append(f"line {number}: expected {len(FIELDS)} tab-separated fields, got {len(cells)}")
            continue
        problems += [f"line {number}: empty {name}" for name, cell in zip(FIELDS, cells) if not cell.strip()]
    if not seen:
        problems.append("manifest lists no perspective")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: panel-manifest-check.py <manifest.txt>", file=sys.stderr)
        return 2
    problems = check(Path(argv[1]).read_text())
    for problem in problems:
        print(f"PANEL-MANIFEST: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
