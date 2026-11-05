#!/usr/bin/env python3
"""Recognise ignored setup copies that are safe to remove with a worktree."""

import argparse
import filecmp
import os
from pathlib import Path
import subprocess


def disposable(tree: Path, relative: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(tree), "worktree", "list", "--porcelain", "-z"],
        capture_output=True, check=False,
    )
    first = result.stdout.split(b"\0", 1)[0]
    if result.returncode or not first.startswith(b"worktree "):
        return False
    primary = Path(os.fsdecode(first[len(b"worktree "):])).resolve()
    if primary == tree.resolve():
        return False
    try:
        includes = (primary / ".worktreeinclude").read_text().splitlines()
    except (OSError, UnicodeError):
        return False
    paths = set()
    for line in includes:
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or any(c in name for c in "*?[]"):
            return False
        paths.add(path.as_posix())
    links = {".venv", ".dvc/cache"}
    allowed = paths | links
    root = tree / relative.rstrip("/")
    if not root.exists() and not root.is_symlink():
        return False

    def check(path: Path) -> bool:
        name = path.relative_to(tree).as_posix()
        counterpart = primary / name
        # The apparent primary copy may itself point into the tree being
        # deleted. In that case it is not an independent surviving copy.
        if counterpart.exists() and counterpart.resolve().is_relative_to(tree.resolve()):
            return False
        if path.is_symlink():
            return name in allowed and counterpart.exists() and path.resolve() == counterpart.resolve()
        if path.is_file():
            return name in paths and counterpart.is_file() and filecmp.cmp(path, counterpart, shallow=False)
        if path.is_dir():
            if not any(item.startswith(name + "/") for item in allowed):
                return False
            children = list(path.iterdir())
            return bool(children) and all(check(child) for child in children)
        return False

    try:
        return check(root)
    except (OSError, RuntimeError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path)
    parser.add_argument("path")
    args = parser.parse_args()
    raise SystemExit(0 if disposable(args.tree, args.path) else 1)


if __name__ == "__main__":
    main()
