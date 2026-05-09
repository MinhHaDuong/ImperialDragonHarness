#!/usr/bin/env python3
"""Replace the ## Status section of STATE.md with fresh git + erg output."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _repo_root() -> Path:
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if r.returncode == 0:
        return Path(r.stdout.strip())
    return Path(__file__).parent.parent  # fallback: script is in scripts/ of project


REPO_ROOT = _repo_root()
STATE_FILE = REPO_ROOT / "STATE.md"
TICKETS_DIR = REPO_ROOT / "tickets"
ERG_BIN = TICKETS_DIR / "erg"
STATUS_HEADING = "## Status"
MAX_STATUS_LINES = 20


def run(cmd):
    return subprocess.run(
        cmd, capture_output=True, text=True, check=True, cwd=REPO_ROOT
    ).stdout.strip()


def get_commits(n=5):
    return run(["git", "log", "--oneline", f"-{n}"]).splitlines()


def get_tickets():
    return json.loads(run([str(ERG_BIN), "ready", str(TICKETS_DIR), "--json"]))


def format_status(tickets, commits):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    ready = [t for t in tickets if t["ready"]]
    blocked = [t for t in tickets if not t["ready"]]

    lines = [STATUS_HEADING, f"<!-- generated {now} -->", ""]

    if ready:
        lines.append(f"**Ready ({len(ready)}):**")
        for t in ready:
            lines.append(f"  `{t['id']}` {t['title']}")

    if blocked:
        lines.append(f"**Blocked ({len(blocked)}):**")
        for t in blocked:
            deps = " ".join(f"→{b['id']}" for b in t["blocked_by"])
            lines.append(f"  `{t['id']}` {t['title']} ({deps})")

    if commits:
        lines.append("**Recent commits:**")
        for c in commits:
            lines.append(f"  {c}")

    return lines


def split_at_status(text):
    """Return (preamble, discarded) split at the first ## Status heading."""
    idx = text.find(f"\n{STATUS_HEADING}")
    if idx == -1:
        return text.rstrip(), None
    return text[:idx], text[idx + 1 :]


def refresh_last_updated(preamble, date_str):
    pat = re.compile(r"^Last updated:.*$", re.MULTILINE)
    if pat.search(preamble):
        return pat.sub(f"Last updated: {date_str}", preamble)
    return preamble


def main():
    if not STATE_FILE.exists():
        print(f"ERROR: {STATE_FILE} not found", file=sys.stderr)
        sys.exit(1)

    text = STATE_FILE.read_text()
    preamble, _ = split_at_status(text)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    preamble = refresh_last_updated(preamble, today)

    commits = get_commits()
    tickets = get_tickets()
    status_lines = format_status(tickets, commits)

    if len(status_lines) > MAX_STATUS_LINES:
        status_lines = status_lines[:MAX_STATUS_LINES]
        status_lines.append(f"<!-- truncated to {MAX_STATUS_LINES} lines -->")

    new_text = preamble.rstrip() + "\n\n" + "\n".join(status_lines) + "\n"
    STATE_FILE.write_text(new_text)

    total = len(new_text.splitlines())
    print(f"STATE.md refreshed — {len(status_lines)} status lines, {total} total.")
    if total > 40:
        print(
            f"WARNING: {total} lines exceeds 40-line cap — trim the hand-edited sections."
        )


if __name__ == "__main__":
    main()
