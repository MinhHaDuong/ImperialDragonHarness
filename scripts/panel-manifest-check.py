#!/usr/bin/env python3
"""Fail closed unless every line of a review panel manifest names its seat's model.

A manifest line is `perspective<TAB>model<TAB>family<TAB>reason`, written by the
orchestrator before launching. An empty model, family or reason means the launch
choice was not made, which is the failure the manifest exists to expose.

With `--seats a,b` (the `panel_seats:` line of `gaze_brief.py resolve`), the
manifest must list exactly those perspectives: gaze adds no seat to the
caller's brief and drops none (ticket 1225).
"""

import re
import sys
from pathlib import Path

NAME = re.compile(r"[A-Za-z0-9_-]+")
FIELDS = ("perspective", "model", "family", "reason")


def check(text: str) -> list[str]:
    problems = []
    seen = 0
    names: set[str] = set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        seen += 1
        cells = line.split("\t")
        if len(cells) != len(FIELDS):
            problems.append(f"line {number}: expected {len(FIELDS)} tab-separated fields, got {len(cells)}")
            continue
        name = cells[0]
        if name.strip() and not NAME.fullmatch(name):
            problems.append(f"line {number}: perspective {name!r} must match [A-Za-z0-9_-]+")
        elif name in names:
            problems.append(f"line {number}: duplicate perspective {name!r}")
        names.add(name)
        problems += [f"line {number}: empty {name}" for name, cell in zip(FIELDS, cells) if not cell.strip()]
    if not seen:
        problems.append("manifest lists no perspective")
    return problems


def against_brief(text: str, seats: str) -> list[str]:
    listed = [line.split("\t")[0] for line in text.splitlines() if line.strip() and not line.startswith("#")]
    wanted = [seat for seat in seats.split(",") if seat]
    return [f"perspective {name!r} is not in the brief" for name in listed if name not in wanted] + [
        f"brief seat {name!r} is missing from the manifest" for name in wanted if name not in listed
    ]


def main(argv: list[str]) -> int:
    seats = None
    if len(argv) == 4 and argv[2] == "--seats":
        seats = argv[3]
        argv = argv[:2]
    if len(argv) != 2:
        print("usage: panel-manifest-check.py <manifest.txt> [--seats a,b]", file=sys.stderr)
        return 2
    try:
        text = Path(argv[1]).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        print(f"PANEL-MANIFEST: cannot read {argv[1]}: {error}", file=sys.stderr)
        return 1
    problems = check(text)
    if seats is not None:
        problems += against_brief(text, seats)
    for problem in problems:
        print(f"PANEL-MANIFEST: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
