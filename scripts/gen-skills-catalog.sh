#!/usr/bin/env bash
# gen-skills-catalog.sh — Generate skills catalog from SKILL.md frontmatter
# Extracts name and description from each skills/*/SKILL.md file
# and outputs a sorted markdown table suitable for README.md

set -euo pipefail

# Exported, not passed as argv: the python below is a quoted heredoc on stdin,
# so it has no $1. The previous version read sys.argv[1] and silently fell
# back to ./skills, which made the directory argument dead code.
export SKILLS_DIR="${1:-.}/skills"

# The frontmatter is parsed as YAML, not pattern-matched. A regex that pulls
# `description:` out and strips the surrounding quotes accepts a document
# PyYAML rejects, so its "all clear" is indistinguishable from "I could not
# look" — that is how four unparseable SKILL.md files went unnoticed
# (ticket 0515). A quoted value also has to come out *unquoted* here, and a
# textual extraction gets that wrong in the other direction: it copies the
# quotes straight into the README table.
python3 << 'EOF'
import os
import re
import sys
from pathlib import Path

import yaml

skills_dir = os.environ["SKILLS_DIR"]

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)

catalog = []

for skill_file in sorted(Path(skills_dir).glob("*/SKILL.md")):
    match = FRONTMATTER.match(skill_file.read_text())
    if not match:
        continue

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        print(f"Warning: {skill_file}: invalid YAML frontmatter: {exc}", file=sys.stderr)
        continue

    if not isinstance(meta, dict):
        continue

    name, description = meta.get("name"), meta.get("description")
    if not isinstance(name, str) or not isinstance(description, str):
        continue

    # Collapse the line breaks of a folded/multi-line description into one row.
    catalog.append((name, " ".join(description.split())))

catalog.sort(key=lambda entry: entry[0])

for name, description in catalog:
    # Escape pipes so a description cannot open a new table column
    print("| `/{}` | {} |".format(name, description.replace("|", "\\|")))
EOF
