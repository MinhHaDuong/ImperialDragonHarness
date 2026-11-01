#!/usr/bin/env python3
"""Render the harness agents for Pi's subagent extension (ticket 1426).

agents/*.md are the runtime-neutral shells, written with Claude Code tool
names. Pi's subagent extension passes a frontmatter ``tools:`` list to the
child as ``--tools a,b`` and Pi keeps only the names its registry knows,
case-sensitively: ``Read`` is dropped without a warning, so a shell copied
verbatim launches a child with no tools. This script writes one Pi rendering
per shell into adapters/pi/agents/, which `idh install` projects into
~/.pi/agent/agents (adapters/projections.json). Only ``tools:`` changes;
name, description and body travel verbatim, and no ``model:`` is added: an
unpinned Pi child inherits the dispatcher's model, as an unpinned Claude
child inherits the session's.

tests/test_pi_agents.py fails when a committed rendering differs from what
this script writes; rerun it after editing agents/*.md.
"""

import argparse
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Claude Code tool -> Pi tools. Pi 1.4.0 built-ins: read, bash, edit, write,
# grep, find, ls (dist/core/tools/index.js); `subagent` is the extension's
# tool. Skill maps to nothing: Pi lists skills in the system prompt and the
# child opens SKILL.md with read.
TOOL_MAP = {
    "Read": ["read"],
    "Grep": ["grep"],
    "Glob": ["find", "ls"],
    "Bash": ["bash"],
    "Write": ["write"],
    "Edit": ["edit"],
    "Agent": ["subagent"],
    "Skill": [],
}
# A shell with no tools: line gets every tool on Claude Code; on Pi it would
# get Pi's default set, which lacks grep, find, ls and subagent.
ALL_TOOLS = "Read, Grep, Glob, Bash, Edit, Write, Agent"
PROVENANCE = (
    "<!-- Generated from agents/{name} by scripts/render-pi-agents.py "
    "(ticket 1426): edit the source, then rerun. -->\n"
)


def pi_tools(claude: str | None) -> list[str]:
    """Map a Claude ``tools:`` value to the Pi tool list, order kept, duplicates dropped."""
    out: list[str] = []
    for name in (claude or ALL_TOOLS).split(","):
        name = name.strip()
        if name not in TOOL_MAP:
            raise ValueError(f"no Pi mapping for Claude tool {name!r}: add it to TOOL_MAP")
        out += [t for t in TOOL_MAP[name] if t not in out]
    return out


def render(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    front, fence, body = text[4:].partition("\n---\n")
    if not text.startswith("---\n") or not fence:
        raise ValueError(f"{source}: no frontmatter fenced by --- lines")
    lines = front.splitlines()
    claude = next((ln.partition(":")[2].strip() for ln in lines if ln.startswith("tools:")), None)
    kept = [ln for ln in lines if not ln.startswith(("tools:", "model:"))]
    kept.append("tools: " + ", ".join(pi_tools(claude)))
    return "---\n" + "\n".join(kept) + "\n---\n\n" + PROVENANCE.format(name=source.name) + body.lstrip("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=REPO / "agents")
    parser.add_argument("--output", type=Path, default=REPO / "adapters" / "pi" / "agents")
    parser.add_argument("--check", action="store_true", help="exit 1 when a rendering is stale; write nothing")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sources = sorted(args.source.glob("*.md"))
    wanted = {s.name: render(s) for s in sources}
    stale = [n for n, t in wanted.items() if not (args.output / n).is_file() or (args.output / n).read_text(encoding="utf-8") != t]
    extra = sorted(p.name for p in args.output.glob("*.md") if p.name not in wanted)
    if args.check:
        for n in stale + extra:
            logging.error("stale: %s", args.output / n)
        return 1 if stale or extra else 0
    args.output.mkdir(parents=True, exist_ok=True)
    for n in stale:
        (args.output / n).write_text(wanted[n], encoding="utf-8")
        logging.info("wrote %s", args.output / n)
    for n in extra:
        (args.output / n).unlink()
        logging.info("removed %s (no source)", args.output / n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
