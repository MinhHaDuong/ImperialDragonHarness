#!/usr/bin/env bash
# gen-skills-catalog.sh — Generate skills catalog from SKILL.md frontmatter
# Extracts name and description from each skills/*/SKILL.md file
# and outputs a sorted markdown table suitable for README.md

set -euo pipefail

SKILLS_DIR="${1:-.}/skills"

# Python script to extract YAML frontmatter
python3 << 'EOF'
import sys
import os
import re
from pathlib import Path

skills_dir = sys.argv[1] if len(sys.argv) > 1 else "./skills"

# Find all SKILL.md files
skill_files = sorted(Path(skills_dir).glob("*/SKILL.md"))

catalog = []

for skill_file in skill_files:
    try:
        content = skill_file.read_text()

        # Extract YAML frontmatter between --- markers
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            continue

        frontmatter = match.group(1)

        # Extract name field
        name_match = re.search(r'^name:\s*(\S+)', frontmatter, re.MULTILINE)
        if not name_match:
            continue
        name = name_match.group(1)

        # Extract description field (multi-line safe)
        # Matches: description: <text> until next field or end
        desc_match = re.search(
            r'^description:\s*(.+?)(?=\n\w+:|$)',
            frontmatter,
            re.MULTILINE | re.DOTALL
        )
        if not desc_match:
            continue

        description = desc_match.group(1).strip()
        # Clean up line breaks and extra whitespace in multi-line descriptions
        description = ' '.join(description.split())

        catalog.append((name, description))

    except Exception as e:
        print(f"Warning: Failed to parse {skill_file}: {e}", file=sys.stderr)

# Sort alphabetically by name
catalog.sort(key=lambda x: x[0])

# Emit markdown table rows
for name, description in catalog:
    # Escape pipes in description
    description = description.replace('|', '\\|')
    print(f"| `/{name}` | {description} |")

EOF

