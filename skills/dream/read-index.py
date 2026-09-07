#!/usr/bin/env python3
"""
Read a project's memory index and file contents. Output JSON for Claude to reason over.
Pure I/O — no LLM calls, no Anthropic imports.
"""

import argparse
import json
import re
import sys
from pathlib import Path

MEMORY_BASE = Path.home() / ".claude" / "projects"


def main():
    parser = argparse.ArgumentParser(
        description="Read project memory index and return entries as JSON."
    )
    parser.add_argument("project", help="Directory name under ~/.claude/projects/")

    # Production project keys are directory slugs that begin with '-'
    # (e.g. -home-haduong--claude). Without a '--' separator argparse reads the
    # value as an option and exits 2 with a usage dump (ticket 0500). Insert the
    # separator unless the caller already did, or is asking for help.
    tokens = sys.argv[1:]
    if tokens and "--" not in tokens and not any(
        t in ("-h", "--help") for t in tokens
    ):
        tokens.insert(0, "--")
    args = parser.parse_args(tokens)

    memory_dir = MEMORY_BASE / args.project / "memory"

    if not memory_dir.exists():
        json.dump(
            {"error": f"No memory dir at {memory_dir}", "entries": []}, sys.stdout
        )
        sys.exit(1)

    index_path = memory_dir / "MEMORY.md"
    if not index_path.exists():
        json.dump(
            {"project": args.project, "memory_dir": str(memory_dir), "entries": []},
            sys.stdout,
        )
        return

    entries = []
    with open(index_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"-\s+\[([^\]]+)\]\(([^\)]+)\)\s*[—-]?\s*(.*)", line)
            if not match:
                continue
            title, filename, desc = match.group(1), match.group(2), match.group(3)
            filepath = memory_dir / filename
            content = filepath.read_text() if filepath.exists() else "(file missing)"
            entries.append(
                {
                    "filename": filename,
                    "title": title,
                    "desc": desc,
                    "path": str(filepath),
                    "content": content,
                }
            )

    json.dump(
        {
            "project": args.project,
            "memory_dir": str(memory_dir),
            "entries": entries,
        },
        sys.stdout,
        indent=2,
    )
    print()


if __name__ == "__main__":
    main()
