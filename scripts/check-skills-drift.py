#!/usr/bin/env python3
"""Check if skills catalog in README.md is in sync with SKILL.md files."""

import re
import subprocess
import sys


def main():
    # Generate expected catalog
    result = subprocess.run(
        ["./scripts/gen-skills-catalog.sh", "."],
        capture_output=True,
        text=True,
        check=True,
    )
    expected = set(result.stdout.strip().split("\n"))

    # Extract actual catalog from README
    with open("README.md", "r") as f:
        content = f.read()

    match = re.search(
        r"<!-- skills:begin -->\n\n\| Command \| Description \|\n\|------+\|\-+\|\n(.*?)\n\n<!-- skills:end -->",
        content,
        re.DOTALL,
    )
    if match:
        actual_block = match.group(1)
        actual = set(
            line for line in actual_block.split("\n") if line.strip().startswith("|")
        )
    else:
        actual = set()

    if expected == actual:
        print("OK: Skills catalog is in sync.")
        sys.exit(0)
    else:
        print("DRIFT DETECTED: skills catalog in README.md is out of sync")
        print("Run 'make skills-catalog' to regenerate")
        sys.exit(1)


if __name__ == "__main__":
    main()
