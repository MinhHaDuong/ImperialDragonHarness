#!/usr/bin/env python3
"""Project the canonical perch skill into Claude Code for ticket 0802.

The provider-neutral installation target is ``~/.agents``.  Codex and Pi read
``~/.agents/skills/perch`` directly; only Claude Code needs a discovery link.
This intentionally remains a one-skill pilot rather than an adapter framework.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INVENTORY = HERE / "pilot-support.json"
TARGET = Path(".claude/skills/perch")
BIN_ENV = {
    "claude": "CLAUDE_BIN",
    "codex": "CODEX_BIN",
    "pi": "PI_BIN",
}


class Refusal(RuntimeError):
    """A fail-closed pilot decision that should be shown without a traceback."""


def _inventory() -> dict:
    return json.loads(INVENTORY.read_text())


def _policy(harness: str) -> dict:
    for policy in _inventory()["versions"]:
        if policy["harness"] == harness:
            return policy
    raise Refusal(f"no version policy for {harness}; refusing support check")


def _extract_version(output: str) -> str:
    match = re.search(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)", output)
    if not match:
        raise Refusal(
            f"could not parse semantic version from {output!r}; refusing support check"
        )
    return match.group(1)


def _probe_version(harness: str) -> str:
    executable = os.environ.get(BIN_ENV[harness], harness)
    try:
        result = subprocess.run(
            [executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Refusal(
            f"could not run {executable!r} --version; refusing support check"
        ) from exc
    return _extract_version(result.stdout + result.stderr)


def check_version(harness: str, supplied: str | None = None) -> str:
    version = _extract_version(supplied) if supplied is not None else _probe_version(harness)
    allowed = _policy(harness)["supported_versions"]
    if version not in allowed:
        rendered = ", ".join(allowed)
        raise Refusal(
            f"unsupported {harness} version {version}; expected one of "
            f"{rendered}; refusing support check"
        )
    return version


def _canonical_skill() -> Path:
    source = (HERE.parent / "skills" / "perch").resolve()
    skill = source / "SKILL.md"
    if not skill.is_file():
        raise Refusal(f"canonical perch skill missing at {skill}; refusing support check")
    return source


def _target() -> Path:
    return Path.home() / TARGET


def install(harness: str) -> None:
    if harness != "claude":
        raise Refusal(
            f"{harness} needs no perch adapter; it discovers ~/.agents/skills directly"
        )
    version = check_version(harness)
    source = _canonical_skill()
    target = _target()
    if os.path.lexists(target):
        if target.is_symlink() and target.resolve() == source:
            print(f"perch already installed for {harness} {version}: {target}")
            return
        raise Refusal(f"{target} exists; refusing to replace an unmanaged entry")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source, target_is_directory=True)
    print(f"installed perch for {harness} {version}: {target} -> {source}")


def uninstall(harness: str) -> None:
    if harness != "claude":
        raise Refusal(
            f"{harness} has no perch adapter; the canonical skill is not removed"
        )
    source = _canonical_skill()
    target = _target()
    if not os.path.lexists(target):
        print(f"perch is not installed for {harness}: {target}")
        return
    if not target.is_symlink() or target.resolve() != source:
        raise Refusal(f"{target} is not the managed perch link; refusing to remove it")
    target.unlink()
    print(f"removed perch adapter for {harness}: {target}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check-version")
    check.add_argument("harness", choices=tuple(BIN_ENV))
    check.add_argument("--version", help="check supplied output instead of running the CLI")

    for command in ("install", "uninstall"):
        child = commands.add_parser(command)
        child.add_argument("harness", choices=tuple(BIN_ENV))
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "check-version":
            version = check_version(args.harness, args.version)
            print(f"supported {args.harness} version: {version}")
        elif args.command == "install":
            install(args.harness)
        else:
            uninstall(args.harness)
    except Refusal as exc:
        print(f"perch adapter: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
