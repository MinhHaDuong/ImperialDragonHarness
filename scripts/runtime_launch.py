#!/usr/bin/env python3
"""The `launch` verb of runtime.py (ticket 1313): can a worker be launched here, and through which door.

    runtime.py can launch.subagent
    runtime.py can launch.headless.<door>     # door: claude-code (or claude), codex, pi, ...

`can` answers "configured", never "available": the answer comes from `skills/route/routes.json`
`launch_doors` and `shutil.which` of the headless template's program. A subagent door is
configured where the runtime has one: Claude Code and Codex yes, Pi core no (its subagent
extension is not core). Pinning the model on every launch stays the caller's duty
(`rules/claude-code.md` § Subagent levers); `gaze_seat.py` is the one code path that renders
a headless door, so `run` here launches nothing and answers NOOP.
"""

import json
import os
import shlex
import shutil
from pathlib import Path

import runtime

NAME = "launch"
DEFAULT_MODE = "subagent"
ROUTES = Path(__file__).resolve().parents[1] / "skills" / "route" / "routes.json"
ALIASES = {"claude": "claude-code"}
NO_SUBAGENT = {"pi": "Pi core has no subagents"}


def register(sub) -> None:
    p = sub.add_parser(NAME, help="launch a worker (can-only: see `can launch.subagent`)")
    p.add_argument("mode", nargs="?", default=DEFAULT_MODE)


def doors(routes: Path = ROUTES) -> dict:
    return json.loads(routes.read_text(encoding="utf-8")).get("launch_doors", {})


def can(rt: str, mode: str, env, routes: Path = ROUTES) -> str | None:
    """None when `launch.<mode>` is configured, else the reason it is not."""
    kind, _, door = mode.partition(".")
    try:
        table = doors(routes)
    except (OSError, ValueError) as exc:
        return f"routes.json unreadable: {exc}"
    if kind == "subagent":
        if rt in NO_SUBAGENT:
            return NO_SUBAGENT[rt]
        entry = table.get(ALIASES.get(rt, rt))
        if not isinstance(entry, dict) or "subagent" not in entry:
            return f"no subagent door configured for {rt}"
        return None
    if kind == "headless" and door:
        entry = table.get(ALIASES.get(door, door))
        if not isinstance(entry, dict) or "headless" not in entry:
            return f"no headless door {door!r} in routes.json"
        program = shlex.split(entry["headless"]["template"])[0]
        if not shutil.which(program, path=env.get("PATH", os.defpath)):
            return f"{program} is not on PATH"
        return None
    return f"no launch mode {mode!r} (subagent|headless.<door>)"


def run(args, rt: str) -> int:
    return runtime.noop(f"launch {args.mode}", rt,
                        "launching stays with gaze_seat.py and the Agent tool; use `can launch.<mode>`")
