#!/usr/bin/env python3
"""Derive the Claude Code adapter's hooks.json from settings.shared.json.

Ticket 0887. While the adapter is inert and the canonical settings file still
carries the hooks, the two must not drift: a hook added to one and not the
other is exactly the silent gap the adapter was built to close. So the plugin's
hooks.json is *derived*, never hand-edited, and `--check` fails when it is
stale -- the same generated-plus-drift-check idiom the skills catalog uses.

Translation, and all of it: a command naming a script under the harness
scripts/ directory becomes a call to the plugin's own launcher. Everything else
-- matchers, `if` filters, timeouts, event names, a command that names no
harness path such as `rtk hook claude` -- is carried through untouched.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHARED = REPO / "settings.shared.json"
DERIVED = REPO / "adapters" / "claude-code" / "hooks" / "hooks.json"

LAUNCHER = '"${CLAUDE_PLUGIN_ROOT}/bin/idh-hook"'
# `$HOME/.claude/scripts/x.sh a` and `python3 $HOME/.claude/scripts/x.py a`
HARNESS_SCRIPT = re.compile(
    r"^(?:python3\s+)?\$HOME/\.claude/scripts/(?P<name>[\w.-]+)(?P<rest>\s.*)?$"
)


def translate(command: str) -> str:
    m = HARNESS_SCRIPT.match(command.strip())
    if not m:
        return command
    return f"{LAUNCHER} {m.group('name')}{m.group('rest') or ''}"


def derive(shared: dict) -> dict:
    hooks = json.loads(json.dumps(shared["hooks"]))
    for blocks in hooks.values():
        for block in blocks:
            for hook in block.get("hooks", []):
                if "command" in hook:
                    hook["command"] = translate(hook["command"])
    return {"hooks": hooks}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when the derived file is stale, write nothing",
    )
    args = ap.parse_args()

    want = json.dumps(
        derive(json.loads(SHARED.read_text(encoding="utf-8"))),
        indent=2,
        ensure_ascii=False,
    ) + "\n"

    if args.check:
        have = DERIVED.read_text(encoding="utf-8") if DERIVED.exists() else ""
        if have != want:
            print(
                f"gen-claude-code-adapter-hooks: {DERIVED.relative_to(REPO)} is "
                "stale — run `make adapter-hooks`",
                file=sys.stderr,
            )
            return 1
        print("OK: Claude Code adapter hooks are in sync.")
        return 0

    DERIVED.parent.mkdir(parents=True, exist_ok=True)
    DERIVED.write_text(want, encoding="utf-8")
    print(f"wrote {DERIVED.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
