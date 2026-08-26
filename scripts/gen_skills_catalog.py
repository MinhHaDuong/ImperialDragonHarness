#!/usr/bin/env python3
"""Generate the skills catalog from SKILL.md frontmatter.

Prints a sorted markdown table suitable for README.md. Replaces the bash
wrapper gen-skills-catalog.sh (ticket 0531): the wrapper only fed a python
heredoc through an environment variable, and it was what made the shared
frontmatter extraction (scripts/skill_frontmatter.py) impossible to import.

The frontmatter is parsed as YAML, not pattern-matched: a regex that pulls
`description:` out and strips the quotes accepts a document PyYAML rejects,
so its "all clear" is indistinguishable from "I could not look" — that is
how four unparseable SKILL.md files went unnoticed (ticket 0515).
"""

import sys
from pathlib import Path

import skill_frontmatter


def catalog_lines(root: str = ".") -> list[str]:
    """The sorted markdown table rows — the importable seam the sibling
    callers (update-skills-catalog.py, check-skills-drift.py) use directly,
    instead of forking python to re-split printed stdout."""
    catalog = []
    for skill_file in sorted((Path(root) / "skills").glob("*/SKILL.md")):
        try:
            meta = skill_frontmatter.load(skill_file)
        except skill_frontmatter.FrontmatterError as exc:
            print(f"Warning: {exc}", file=sys.stderr)
            continue
        name, description = meta.get("name"), meta.get("description")
        if not isinstance(name, str) or not isinstance(description, str):
            continue
        # Collapse the line breaks of a folded/multi-line description into
        # one table row.
        catalog.append((name, " ".join(description.split())))

    catalog.sort(key=lambda entry: entry[0])

    # Escape pipes so a description cannot open a new table column.
    return ["| `/{}` | {} |".format(name, description.replace("|", "\\|"))
            for name, description in catalog]


def main(root: str = ".") -> None:
    for line in catalog_lines(root):
        print(line)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
