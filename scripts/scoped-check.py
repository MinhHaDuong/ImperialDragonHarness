#!/usr/bin/env python3
"""Run the targets a project diff can affect, falling back to its full gate."""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path


TARGET = re.compile(r"^[A-Za-z0-9_.-]+$")
BRANCH = re.compile(r"^[A-Za-z0-9_./-]+$")
SOURCE_SUFFIXES = {
    ".bash", ".c", ".cc", ".cjs", ".cpp", ".cs", ".dart", ".ex",
    ".exs", ".fish", ".go", ".h", ".hpp", ".hs", ".ipynb", ".java",
    ".jl", ".js", ".jsx", ".kt", ".lua", ".mjs", ".php", ".pl",
    ".ps1", ".py", ".r", ".rb", ".rs", ".scala", ".sh", ".sql",
    ".swift", ".ts", ".tsx", ".zsh",
}
SOURCE_NAMES = {"Makefile", "Dockerfile", "Containerfile", "Jenkinsfile", "Rakefile", "Gemfile", "CMakeLists.txt"}


def _string(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError(f"invalid {label}")
    return value


def _list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError(f"invalid {label}")
    return value


def load_map(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("check map must be an object")
    _string(data.get("default_branch"), BRANCH, "default_branch")
    _string(data.get("full_target"), TARGET, "full_target")
    targets = _list(data.get("targets"), "targets")
    if len(set(targets)) != len(targets) or not all(TARGET.fullmatch(item) for item in targets):
        raise ValueError("invalid or duplicate target")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("invalid rules")
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("invalid rule")
        paths = _list(rule.get("paths"), "rule paths")
        selected = _list(rule.get("targets"), "rule targets")
        if not all(path and not path.startswith("/") for path in paths):
            raise ValueError("invalid rule path")
        if not set(selected) <= set(targets):
            raise ValueError("rule names an undeclared target")
    return data


def changed_paths(base: str) -> set[str] | None:
    diff = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", "-z", base, "--"],
        capture_output=True, check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        capture_output=True, check=False,
    )
    if diff.returncode or untracked.returncode:
        return None
    changed = {os.fsdecode(name) for name in diff.stdout.split(b"\0") if name}
    # Review panels create these while synthesizing a review. They are not
    # part of the PR diff; a staged copy still appears in `changed` above.
    scratch = (".panel/", "build/panel-head/")
    other = {
        os.fsdecode(name) for name in untracked.stdout.split(b"\0") if name
        and not os.fsdecode(name).startswith(scratch)
    }
    return changed | other


def select_targets(data: dict, paths: set[str] | None) -> tuple[list[str], list[str]]:
    targets = data["targets"]
    if not paths:
        return [data["full_target"]], []
    if any(Path(path).suffix.lower() in SOURCE_SUFFIXES or Path(path).name in SOURCE_NAMES
           for path in paths):
        return [data["full_target"]], []
    selected: set[str] = set()
    for path in paths:
        matched = False
        for rule in data["rules"]:
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in rule["paths"]):
                selected.update(rule["targets"])
                matched = True
        if not matched:
            return [data["full_target"]], []
    return [target for target in targets if target in selected], [
        target for target in targets if target not in selected
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=".idh-checks.json", help="project path-to-target map")
    parser.add_argument("--dry-run", action="store_true", help="select and report without running make")
    args = parser.parse_args()
    try:
        data = load_map(Path(args.map))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"cannot use check map: {exc}")
    base = f"origin/{data['default_branch']}"
    paths = changed_paths(base)
    selected, skipped = select_targets(data, paths)
    print(f"selected: {' '.join(selected)}", flush=True)
    if paths is None:
        print(f"diff unavailable against {base}; running full gate", flush=True)
    result = 0
    try:
        if not args.dry_run:
            try:
                result = subprocess.run(["make", *selected], check=False).returncode
            except OSError as exc:
                print(f"cannot run make: {exc.strerror}", file=sys.stderr)
                result = 127
    finally:
        print(f"skipped: {' '.join(skipped) if skipped else 'none'}", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
