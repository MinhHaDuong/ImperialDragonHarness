#!/usr/bin/env python3
"""List Claude Code's native auto-memory notes for one project (smelt, ticket 1350).

Read-only: prints one tab-separated row per note (file, type, git blob sha,
description) so smelt can propose a disposition for the author. It writes and
deletes nothing. The store path is derived the way Claude Code names it:
the project's primary-checkout path (a linked worktree maps to it, via
git's common dir) with every non-alphanumeric character replaced by
a dash, under ``~/.claude/projects/<name>/memory``.

Usage: smelt_native_notes.py <project-repository> [--store DIR]
"""
import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path


def primary_checkout(path):
    """Primary checkout of the repository holding ``path`` (a worktree maps to it).

    A path outside any git repository is returned resolved, unchanged.
    """
    path = Path(path).resolve()
    r = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return path
    return Path(r.stdout.strip()).resolve().parent


def store_path(project, home=None):
    home = Path(home) if home else Path.home()
    return home / ".claude/projects" / re.sub(r"[^A-Za-z0-9]", "-", str(project)) / "memory"


def _front(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def _field(front, key):
    m = re.search(rf"^\s*{key}:\s*(.*)$", front, re.M)
    return m.group(1).strip() if m else ""


def list_notes(store):
    store = Path(store)
    if not store.is_dir():
        raise FileNotFoundError(f"native memory store not found: {store}")
    rows = []
    for p in sorted(store.glob("*.md")):
        if p.name == "MEMORY.md":
            continue
        data = p.read_bytes()
        front = _front(data.decode("utf-8", "replace"))
        rows.append({
            "file": p.name,
            "type": _field(front, "type"),
            "description": _field(front, "description"),
            "sha": hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest(),
        })
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", type=Path)
    ap.add_argument("--store", type=Path)
    a = ap.parse_args(argv)
    store = a.store or store_path(primary_checkout(a.project))
    try:
        rows = list_notes(store)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    print(f"# store: {store}  notes: {len(rows)}")
    for r in rows:
        print("\t".join((r["file"], r["type"], r["sha"][:8], r["description"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
