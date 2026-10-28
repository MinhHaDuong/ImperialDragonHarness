#!/usr/bin/env python3
"""Generate the skills catalog from SKILL.md frontmatter.

Prints grouped markdown tables for skills-catalog.md. Replaces the bash
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


CATEGORIES = {
    "build": "The build loop",
    "session": "The session loop",
    "maintenance": "Project maintenance",
    "memory": "Memory and learning",
    "runtime-review": "Runtime and review support",
    "research": "Research and bibliography",
    "reviewing": "Reviewing",
    "writing": "Copyediting",
    "publication": "Submission and publication",
}
GENERALIST = {"build", "session", "maintenance", "memory", "runtime-review"}


def catalog_lines(root: str = ".") -> list[str]:
    """The grouped Markdown catalog lines — the importable seam the sibling
    callers (update-skills-catalog.py, check-skills-drift.py) use directly,
    instead of forking python to re-split printed stdout."""
    catalog = []
    for skill_file in sorted((Path(root) / "skills").glob("*/SKILL.md")):
        # Private skills are symlinked into skills/ (gitignored): the runtime
        # discovers them, but repo files carry NO pointers to them — the
        # published catalog included their descriptions, which carry T2
        # topology (personal cloud endpoints, machine names), until this
        # skip (2026-09-28). Anything symlinked here is private by design.
        if skill_file.parent.is_symlink():
            continue
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
        metadata = meta.get("metadata")
        category = metadata.get("category") if isinstance(metadata, dict) else None
        if category not in CATEGORIES:
            raise ValueError(f"{skill_file}: missing or unknown category {category!r}")
        # An optional metadata.order puts a section in workflow order; skills
        # without one follow, by name.
        order = metadata.get("order", float("inf"))
        catalog.append((category, order, name, " ".join(description.split())))

    lines = []
    current_family = None
    for category, title in CATEGORIES.items():
        entries = [(name, desc) for cat, _, name, desc in
                   sorted(e for e in catalog if e[0] == category)]
        if not entries:
            continue
        if lines:
            lines.append("")
        family = "Generalist" if category in GENERALIST else "Research"
        if family != current_family:
            lines.extend([f"## {family}", ""])
            current_family = family
        lines.extend([f"### {title}", "", "| Command | Description |",
                      "|---------|-------------|"])
        lines.extend("| `/{}` | {} |".format(name, desc.replace("|", "\\|"))
                     for name, desc in entries)
    return lines


def catalog_document(root: str = ".") -> str:
    return (
        "# Skills catalog\n\n"
        "<!-- Generated from skills/*/SKILL.md; run make skills-catalog. -->\n\n"
        + "\n".join(catalog_lines(root)) + "\n"
    )


def main(root: str = ".") -> None:
    for line in catalog_lines(root):
        print(line)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
