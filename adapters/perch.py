#!/usr/bin/env python3
"""Make one canonical ``perch`` skill discoverable by Claude Code, Codex and Pi.

Ticket 0802, second attempt. The provider-neutral destination is
``$HOME/.agents/skills`` -- not a name this pilot invents, but the user-level
Agent Skills root that Codex and Pi both document and both scan. This module
*creates* it; the first attempt only asserted it, and the two harnesses the
pilot exists to reach had nothing to find.

Three decisions, each one a defect of PR #780 turned around:

**The neutral home is built.** ``install codex`` / ``install pi`` create
``$HOME/.agents/skills/perch`` as a symlink onto this repository's
``skills/perch``. Both harnesses follow a symlinked skill directory, so the
Markdown body stays canonical and live -- no copy, no build step.

**The version gate is a floor, not an allowlist.** An exact-match list of
supported versions goes stale on every upstream release, and PR #780's already
refused two of the three CLIs installed nine days later. A minimum plus a probe
widens with upstream instead. Unknown, unparseable or absent: refuse, never
silently accept.

**A target that already resolves to the canonical source is success.** In this
installation the harness repository *is* ``$HOME/.claude``, so
``$HOME/.claude/skills/perch`` and the canonical source are the same directory.
That is the goal state for Claude Code, reached with nothing installed; PR #780
read it as a collision and refused its own skill as an unmanaged entry.

One hand-ported slice. No generator, no workflow DSL, no second copy of the
prose. Usage::

    adapters/perch.py status
    adapters/perch.py install codex
    adapters/perch.py uninstall codex
    adapters/perch.py check-version pi
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
INVENTORY_PATH = HERE / "pilot-support.json"
SLICE = "perch"

HARNESSES = ("claude", "codex", "pi")

# Claude Code reads only its own skills root; Codex and Pi both read the
# provider-neutral one. That split is the whole adapter surface of this slice.
NEUTRAL_HARNESSES = ("codex", "pi")

# The only frontmatter duplication this slice observed: all three harnesses
# require exactly these two fields, and the canonical body already carries
# them. Nothing else is promoted to core (ticket action 7).
SHARED_REQUIRED_FIELDS = ("name", "description")

BIN_ENV = {
    "claude": "PERCH_CLAUDE_BIN",
    "codex": "PERCH_CODEX_BIN",
    "pi": "PERCH_PI_BIN",
}

SEMVER = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")


class Refusal(RuntimeError):
    """A fail-closed pilot decision, shown without a traceback."""


# --- the canonical body -------------------------------------------------


def canonical_source() -> Path:
    """The one live skill directory. Everything else points at it."""
    source = (REPO / "skills" / SLICE).resolve()
    if not (source / "SKILL.md").is_file():
        raise Refusal(f"canonical {SLICE} skill missing at {source}/SKILL.md")
    return source


def frontmatter(path: Path) -> dict:
    """The YAML frontmatter of a SKILL.md, as a mapping."""
    import yaml

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise Refusal(f"{path} has no frontmatter")
    _, _, rest = text.partition("---\n")
    block, sep, _ = rest.partition("\n---")
    if not sep:
        raise Refusal(f"{path} has an unterminated frontmatter block")
    return yaml.safe_load(block) or {}


# --- the evidence inventory ---------------------------------------------


def inventory() -> dict:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def policy(harness: str) -> dict:
    for entry in inventory()["versions"]:
        if entry["harness"] == harness:
            return entry
    raise Refusal(f"no version policy recorded for {harness}")


# --- version policy: a floor plus a probe -------------------------------


def parse_version(text: str) -> tuple[int, int, int]:
    match = SEMVER.search(text)
    if not match:
        raise Refusal(f"no semantic version in {text!r}; refusing to guess one")
    return tuple(int(part) for part in match.groups())


def _probe(harness: str) -> str:
    executable = os.environ.get(BIN_ENV[harness], harness)
    try:
        done = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal(f"could not run {executable!r} --version: {exc}") from exc
    return done.stdout + done.stderr


def check_version(harness: str, supplied: str | None = None) -> str:
    """The version in use, or a Refusal. Never a silent pass."""
    if harness not in BIN_ENV:
        raise Refusal(f"unknown harness {harness!r}")
    raw = supplied if supplied is not None else _probe(harness)
    found = parse_version(raw)
    floor_text = policy(harness)["minimum_version"]
    if found < parse_version(floor_text):
        raise Refusal(
            f"{harness} {'.'.join(str(n) for n in found)} is below the pilot "
            f"minimum {floor_text}; refusing to install"
        )
    return ".".join(str(number) for number in found)


# --- where each harness looks -------------------------------------------


def _home() -> Path:
    return Path(os.path.expanduser("~"))


def neutral_home() -> Path:
    """The provider-neutral Agent Skills root Codex and Pi both scan."""
    return _home() / ".agents"


def target_path(harness: str) -> Path:
    if harness == "claude":
        return _home() / ".claude" / "skills" / SLICE
    if harness in NEUTRAL_HARNESSES:
        return neutral_home() / "skills" / SLICE
    raise Refusal(f"unknown harness {harness!r}")


def _is_canonical(target: Path) -> bool:
    try:
        return target.resolve() == canonical_source()
    except OSError:
        return False


def _holds_another_copy(target: Path) -> bool:
    """Is this a live ``perch`` skill that simply is not *our* checkout's?

    The case is ordinary rather than exotic: run from a git worktree, the
    canonical source is the worktree's ``skills/perch`` while the Claude
    skills root still holds the primary checkout's. Refusing is right --
    pointing a live skills root at a throwaway worktree is not an
    improvement -- but the refusal has to say which situation it is, or it
    reads as the unmanaged-entry collision that closed PR #780.
    """
    manifest = target / "SKILL.md"
    if target.is_symlink() or not manifest.is_file():
        return False
    try:
        return frontmatter(manifest).get("name") == SLICE
    except (Refusal, OSError):
        return False


def status(harness: str) -> dict:
    target = target_path(harness)
    present = os.path.lexists(target) and _is_canonical(target)
    if not present:
        if not os.path.lexists(target):
            projection = "absent"
        elif _holds_another_copy(target):
            projection = "other-checkout"
        else:
            projection = "unmanaged"
    elif target.is_symlink():
        projection = "symlink"
    else:
        # The harness checkout already sits where this harness looks: the
        # canonical directory is the installed one. Nothing to project.
        projection = "none"
    return {
        "harness": harness,
        "slice": SLICE,
        "target": str(target),
        "source": str(canonical_source()),
        "installed": present,
        "projection": projection,
    }


# --- install / uninstall ------------------------------------------------


def install(harness: str, version: str | None = None) -> str:
    source = canonical_source()
    target = target_path(harness)

    if os.path.lexists(target):
        if _is_canonical(target):
            return (
                f"{harness}: {SLICE} already discoverable at {target} "
                f"(projection: {status(harness)['projection']})"
            )
        if _holds_another_copy(target):
            raise Refusal(
                f"{target} already holds a {SLICE} skill from another checkout; "
                f"this one is {source}. Run install from that checkout, or "
                f"remove the entry deliberately first"
            )
        raise Refusal(f"{target} exists and is not the canonical {SLICE}")

    checked = check_version(harness, supplied=version)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source, target_is_directory=True)
    return f"{harness} {checked}: installed {target} -> {source}"


def _prune_empty(directory: Path) -> None:
    """Give back exactly the directories the install created, no more."""
    home = _home().resolve()
    while directory != home and home in directory.resolve().parents:
        try:
            directory.rmdir()
        except OSError:
            return
        directory = directory.parent


def uninstall(harness: str) -> str:
    target = target_path(harness)
    if not os.path.lexists(target):
        return f"{harness}: {SLICE} is not installed at {target}"
    if not target.is_symlink():
        if _is_canonical(target):
            return (
                f"{harness}: {target} is the canonical {SLICE} skill, not a "
                f"pilot artifact; nothing removed"
            )
        raise Refusal(f"{target} is not the managed {SLICE} link")
    if not _is_canonical(target):
        raise Refusal(f"{target} is not the managed {SLICE} link")
    target.unlink()
    _prune_empty(target.parent)
    return f"{harness}: removed {target}"


# --- CLI ----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    probe = commands.add_parser("check-version", help="floor-and-probe gate")
    probe.add_argument("harness", choices=HARNESSES)
    probe.add_argument("--version", help="check this text instead of running the CLI")

    for name, help_text in (
        ("install", "make the canonical skill discoverable"),
        ("uninstall", "give back exactly what install created"),
        ("status", "where each harness looks, and what is there"),
    ):
        child = commands.add_parser(name, help=help_text)
        child.add_argument("harness", nargs="?", choices=HARNESSES)
        if name == "install":
            child.add_argument("--version", help="skip the probe with this version")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    targets = [args.harness] if args.harness else list(HARNESSES)
    try:
        if args.command == "check-version":
            for harness in targets:
                print(f"{harness}: {check_version(harness, args.version)}")
        elif args.command == "install":
            for harness in targets:
                print(install(harness, version=args.version))
        elif args.command == "uninstall":
            for harness in targets:
                print(uninstall(harness))
        else:
            for harness in targets:
                print(json.dumps(status(harness), indent=2))
    except Refusal as exc:
        print(f"perch pilot: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
