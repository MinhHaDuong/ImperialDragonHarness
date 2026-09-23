#!/usr/bin/env python3
"""Atomic per-PR gate claim for /gaze (ticket 0852).

An interrupted run leaves its claim visible for manual investigation; it is
never silently stolen by a later run. Other PRs use independent directories.
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from uuid import uuid4


def lock_dir(primary_root: Path, pr: str) -> Path:
    if not re.fullmatch(r"[1-9][0-9]*", pr):
        raise ValueError("PR must be a positive decimal number")
    return primary_root / ".claude" / "worktrees" / ".gaze-gates" / f"pr-{pr}.lock"


def acquire(primary_root: Path, pr: str, review_tree: str) -> str:
    path = lock_dir(primary_root, pr)
    path.parent.mkdir(parents=True, exist_ok=True)
    session_id = str(uuid4())
    try:
        path.mkdir()
    except FileExistsError:
        try:
            holder = json.loads((path / "holder.json").read_text())
            detail = f"session={holder['session_id']} started={holder['started_at']}"
        except (OSError, ValueError, KeyError):
            detail = "holder metadata pending or unavailable"
        raise RuntimeError(f"gaze: gate already live for PR {pr}; {detail}") from None
    try:
        holder = {
            "session_id": session_id,
            "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "review_worktree_path": review_tree,
        }
        temp = path / "holder.json.tmp"
        temp.write_text(json.dumps(holder) + "\n")
        os.replace(temp, path / "holder.json")
    except Exception:
        temp.unlink(missing_ok=True)
        path.rmdir()
        raise
    return session_id


def release(primary_root: Path, pr: str, session_id: str) -> None:
    path = lock_dir(primary_root, pr)
    holder = json.loads((path / "holder.json").read_text())
    if holder["session_id"] != session_id:
        raise RuntimeError(f"gaze: refusing to release another gate's PR {pr} lock")
    (path / "holder.json").unlink()
    path.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("acquire", "release"))
    parser.add_argument("primary_root", type=Path)
    parser.add_argument("pr")
    parser.add_argument("value", help="review worktree path on acquire; session id on release")
    args = parser.parse_args()
    try:
        if args.action == "acquire":
            print(acquire(args.primary_root, args.pr, args.value))
        else:
            release(args.primary_root, args.pr, args.value)
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
