#!/usr/bin/env python3
"""Update skills catalog in README.md from generated catalog lines."""

import re
import subprocess


def main():
    # Generate catalog lines
    result = subprocess.run(
        ["./scripts/gen-skills-catalog.sh", "."],
        capture_output=True,
        text=True,
        check=True,
    )
    catalog_lines = result.stdout.rstrip()

    # Read current README
    with open("README.md", "r") as f:
        content = f.read()

    # Replace content between sentinels
    pattern = r"(<!-- skills:begin -->\n\n\| Command \| Description \|\n\|------+\|\-+\|\n)(.*?)(<!-- skills:end -->)"
    replacement = r"\1" + catalog_lines + r"\n\n\3"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Write back
    with open("README.md", "w") as f:
        f.write(new_content)

    print("Done. Updated README.md with current skills catalog.")


if __name__ == "__main__":
    main()
