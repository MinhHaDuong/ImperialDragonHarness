#!/usr/bin/env python3
"""Make one canonical ``perch`` skill discoverable by Claude Code, Codex and Pi.

Ticket 0802, second attempt. The provider-neutral destination is
``$HOME/.agents/skills`` — not a name this pilot invents, but the user-level
Agent Skills root that Codex and Pi both document and both scan. This module
*creates* it; the first attempt only asserted it, and the two harnesses the
pilot exists to reach had nothing to find.

Three decisions, each one a defect of PR #780 turned around:

**The neutral home is built.** ``install codex`` / ``install pi`` create
``$HOME/.agents/skills/perch`` as a symlink onto this repository's
``skills/perch``. Both harnesses follow a symlinked skill directory, so the
Markdown body stays canonical and live — no copy, no build step.

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

# SKILL.md frontmatter extraction has exactly one definition in this repo
# (ticket 0531, after three copies of the `---`-block parser had diverged).
# A fourth copy here would sit outside the ratchet that keeps it unique.
sys.path.insert(0, str(REPO / "scripts"))
import skill_frontmatter  # noqa: E402
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
    """The YAML frontmatter of a SKILL.md, as a mapping, or a Refusal.

    The parsing itself belongs to ``scripts/skill_frontmatter``: one
    definition, ratcheted by an adherence test. All this adds is the
    translation into this module's refusal contract — a missing fence,
    invalid YAML, or a block that parses to something other than a mapping
    are all "this is not a skill I can read", shown without a traceback.
    """
    try:
        return skill_frontmatter.load(path)
    except skill_frontmatter.FrontmatterError as exc:
        raise Refusal(str(exc)) from exc


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
    """The first ``major.minor.patch`` in *text*, or a Refusal.

    Pre-release and build metadata are deliberately ignored: ``0.85.1-rc.1``
    compares equal to ``0.85.1``. The floor asks whether a release carries the
    behaviour this pilot needs, and a candidate for it does; reading the
    identifier would tighten the gate in the one direction that helps nobody.
    """
    match = SEMVER.search(text)
    if not match:
        raise Refusal(f"no semantic version in {text!r}; refusing to guess one")
    return tuple(int(part) for part in match.groups())


def _probe(harness: str) -> str:
    executable = os.environ.get(f"PERCH_{harness.upper()}_BIN", harness)
    try:
        done = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
            # Strict decoding would raise UnicodeDecodeError, which is neither
            # OSError nor SubprocessError: the refusal contract leaked a raw
            # traceback at exit 1 instead of the documented exit 2.
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise Refusal(f"could not run {executable!r} --version: {exc}") from exc
    # parse_version takes the FIRST semver it is handed, so handing it a whole
    # stream lets a banner line ahead of the real answer flip the floor — a
    # decoy "node 20.11.0" made codex 0.154.0 read as 20.11.0, which clears a
    # 0.154.0 minimum. Narrow to one line, and refuse when the output offers
    # more than one candidate: an ambiguous answer is an unknown version, and
    # this module does not pass unknown versions.
    for stream in (done.stdout, done.stderr):
        candidates = [line for line in stream.splitlines() if SEMVER.search(line)]
        if len(candidates) == 1:
            return candidates[0]
        if candidates:
            raise Refusal(
                f"{executable!r} --version offered {len(candidates)} version-like "
                f"lines; refusing to pick one"
            )
    return done.stdout + done.stderr


def check_version(harness: str, supplied: str | None = None) -> str:
    """The version in use, or a Refusal. Never a silent pass."""
    if harness not in HARNESSES:
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
    skills root still holds the primary checkout's. Refusing is right:
    pointing a live skills root at a throwaway worktree is no
    improvement. But the refusal has to say which situation it is, or
    it reads as the unmanaged-entry collision that closed PR #780.
    """
    manifest = target / "SKILL.md"
    if target.is_symlink() or not manifest.is_file():
        return False
    try:
        return frontmatter(manifest).get("name") == SLICE
    except (Refusal, OSError):
        return False


def _is_dangling_link(target: Path) -> bool:
    """A link of ours whose target went away, typically a moved checkout.

    Unlinking one destroys no data, so naming this state is what makes it
    removable. Calling it "unmanaged" reads as "a third party put it there"
    and leaves an entry nothing can clean up.
    """
    if not target.is_symlink() or target.exists():
        return False
    # A bare basename match would adopt any dangling link happening to be
    # called perch. Require the shape install writes: <checkout>/skills/perch.
    return Path(os.readlink(target)).parts[-2:] == ("skills", SLICE)


def status(harness: str) -> dict:
    target = target_path(harness)
    present = os.path.lexists(target) and _is_canonical(target)
    if not present:
        if not os.path.lexists(target):
            projection = "absent"
        elif _holds_another_copy(target):
            projection = "other-checkout"
        elif _is_dangling_link(target):
            projection = "dangling"
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

    # Probe before anything else, the already-discoverable path included.
    # "already discoverable" is a support claim about *this* CLI, not a bare
    # report, and the module promises never to pass an unknown version
    # silently. status() is the read-only report, and it probes nothing.
    checked = check_version(harness, supplied=version)

    if os.path.lexists(target):
        if _is_canonical(target):
            return (
                f"{harness} {checked}: {SLICE} already discoverable at {target} "
                f"(projection: {status(harness)['projection']})"
            )
        if _holds_another_copy(target):
            raise Refusal(
                f"{target} already holds a {SLICE} skill from another checkout; "
                f"this one is {source}. Run install from that checkout, or "
                f"remove the entry deliberately first"
            )
        if _is_dangling_link(target):
            raise Refusal(
                f"{target} is a {SLICE} link whose target is gone, probably a "
                f"moved checkout; run uninstall {harness} first"
            )
        raise Refusal(f"{target} exists and is not the canonical {SLICE}")

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        # Building the skills root is an OS call like any other, so it owes
        # the same contract as the rest: a plain file where the neutral home
        # should be raises NotADirectoryError, which is neither a Refusal nor
        # anything main() catches, and the CLI exited 1 with a traceback.
        raise Refusal(f"could not create {target.parent}: {exc}") from exc
    try:
        target.symlink_to(source, target_is_directory=True)
    except FileExistsError as exc:
        # Another install won the race between lexists and symlink_to.
        raise Refusal(f"{target} appeared while installing; refusing to race") from exc
    return f"{harness} {checked}: installed {target} -> {source}"


def prune_root(harness: str) -> Path:
    """The highest directory uninstall may remove for this harness.

    For Codex and Pi that is the neutral home, which install may have created.
    For Claude Code it is the skills root: ``$HOME/.claude`` is that harness's
    own configuration directory and never this pilot's to remove.
    """
    if harness in NEUTRAL_HARNESSES:
        return neutral_home()
    return target_path(harness).parent


def _prune_empty(start: Path, stop: Path) -> None:
    """Remove each directory the removal left empty, up to and including *stop*.

    ``rmdir`` fails closed on a directory holding anything, so a neutral home
    with someone else's skill in it survives untouched. An *empty* directory
    that install happened not to create goes too: nothing on disk tells the two
    apart, and the README says as much rather than claiming otherwise.
    """
    # Walking through a symlinked ancestor would rmdir outside $HOME
    # entirely. Refuse the whole prune rather than reason about each step.
    for directory in (start, stop):
        if directory.is_symlink() or any(p.is_symlink() for p in directory.parents):
            return
    current = start
    while True:
        try:
            current.rmdir()
        except OSError:
            return
        if current == stop:
            return
        current = current.parent


def _unlink(target: Path) -> None:
    """Removing something already gone is a success, not a traceback."""
    try:
        target.unlink()
    except FileNotFoundError:
        return


def sharing_target(harness: str) -> tuple[str, ...]:
    """Every harness that reads the directory this one reads.

    Codex and Pi share the neutral home, so removing perch for one removes it
    for the other. The CLI spells them as separate verbs, so the message has
    to say which harnesses a removal actually reaches.
    """
    target = target_path(harness)
    return tuple(other for other in HARNESSES if target_path(other) == target)


def uninstall(harness: str) -> str:
    target = target_path(harness)
    reached = ", ".join(sharing_target(harness))
    if not os.path.lexists(target):
        return f"{harness}: {SLICE} is not installed at {target}"
    if not target.is_symlink():
        if _is_canonical(target):
            return (
                f"{harness}: {target} is the canonical {SLICE} skill, not a "
                f"pilot artifact; nothing removed"
            )
        raise Refusal(f"{target} is not the managed {SLICE} link")
    if _is_dangling_link(target):
        _unlink(target)
        _prune_empty(target.parent, prune_root(harness))
        return f"{reached}: removed {target}, a link whose target no longer exists"
    if not _is_canonical(target):
        raise Refusal(f"{target} is not the managed {SLICE} link")
    _unlink(target)
    _prune_empty(target.parent, prune_root(harness))
    return f"{reached}: removed {target}"


# --- CLI ----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    probe = commands.add_parser("check-version", help="floor-and-probe gate")
    probe.add_argument("harness", choices=HARNESSES)
    probe.add_argument("--version", help="check this text instead of running the CLI")

    for name, help_text in (
        ("install", "make the canonical skill discoverable"),
        ("uninstall", "remove the link, then what it leaves empty"),
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
