#!/usr/bin/env python3
"""Read-only check: are the allow rules that rule-mandated git acts need present?

Ticket 1331. The auto-mode classifier refuses `rules/git.md`'s own acts (a
rebased force-push, `git branch -D` on a superseded branch) as "Git Destructive"
despite a blanket `Bash` allow. These narrow rules, which the author adds to the
live `~/.claude/settings.json`, settle it. This script never edits that file.

Exit 0: all present. 1: some missing (listed). 2: could not read the settings
(missing, unreadable, malformed): says nothing about the rules.

Left to the classifier on purpose: `git update-ref -d` (refused as
"Self-Modification" even with a rule), force-push without lease, `reset --hard`.
"""

import json
import os
import sys
from pathlib import Path

REQUIRED = (
    "Bash(git push --force-with-lease:*)",
    "Bash(git push origin --force-with-lease:*)",
    "Bash(git branch -D:*)",
    "Bash(git push origin --delete:*)",
)


def check(path: Path) -> tuple[int, list[str]]:
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("settings is not an object")
        allow = data.get("permissions", {}).get("allow", [])
        if not isinstance(allow, list):
            raise ValueError("permissions.allow is not a list")
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return 2, []
    missing = [r for r in REQUIRED if r not in allow]
    return (1 if missing else 0), missing


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path(os.path.expanduser("~/.claude/settings.json"))
    code, missing = check(path)
    if code == 2:
        print(f"could not read allow rules from {path}: result unknown")
    elif code == 1:
        print(f"missing {len(missing)} of {len(REQUIRED)} allow rules in {path}:")
        for r in missing:
            print(f"  {r}")
    else:
        print(f"all {len(REQUIRED)} allow rules present in {path}")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
