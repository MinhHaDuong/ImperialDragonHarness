#!/usr/bin/env python3
"""Replace the ## Status section of STATE.md with fresh git + erg output."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_HEADING = "## Status"


def _repo_root() -> Path:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(
            "WARNING: git rev-parse timed out, falling back to script parent",
            file=sys.stderr,
        )
        return Path(__file__).parent.parent
    if r.returncode == 0:
        return Path(r.stdout.strip())
    return Path(__file__).parent.parent  # fallback: script is in scripts/ of project


def run(cmd, repo_root: Path):
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=repo_root, timeout=30
        ).stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"WARNING: command timed out: {cmd}", file=sys.stderr)
        sys.exit(1)


def get_commits(repo_root: Path, n=5):
    return run(["git", "log", "--oneline", f"-{n}"], repo_root).splitlines()


def get_tickets(repo_root: Path):
    """Return (ready_count, blocked_count) from erg.

    `erg ready` lists only ready (unblocked, open) tickets; `erg list` lists
    all open tickets. Neither item carries a `ready` flag, so blocked is
    derived as open minus ready.
    """
    tickets_dir = repo_root / "tickets"
    erg_bin = tickets_dir / "erg"
    if not erg_bin.exists():
        print(f"ERROR: erg binary not found at {erg_bin}", file=sys.stderr)
        sys.exit(1)
    try:
        ready = json.loads(
            run([str(erg_bin), "ready", str(tickets_dir), "--json"], repo_root)
        )
        open_tickets = json.loads(
            run([str(erg_bin), "list", str(tickets_dir), "--json"], repo_root)
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: erg query failed: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    ready_count = len(ready)
    blocked_count = max(len(open_tickets) - ready_count, 0)
    return ready_count, blocked_count


def format_status(ready_count, blocked_count, commits):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    lines = [STATUS_HEADING, f"<!-- generated {now} -->", ""]

    # Summary counts only — full list via: erg ready tickets/
    if ready_count or blocked_count:
        summary = (
            f"**Tickets:** {ready_count} ready · {blocked_count} blocked"
            " — `erg ready tickets/` for full list"
        )
        lines.append(summary)

    if commits:
        lines.append("**Recent commits:**")
        for c in commits:
            lines.append(f"  {c}")

    return lines


def split_at_status(text):
    """Return (preamble, tail) split at the first ## Status heading.

    tail includes everything from the Status heading onward so callers can
    inspect sections that follow (Blockers, Next actions, Incident, etc.).
    preamble is everything strictly before the Status heading.
    """
    idx = text.find(f"\n{STATUS_HEADING}")
    if idx == -1:
        return text.rstrip(), ""
    return text[:idx], text[idx + 1 :]


def _next_section_idx(text, start):
    """Return index of the next ## heading after start, or len(text) if none."""
    m = re.search(r"^## ", text[start:], re.MULTILINE)
    if m:
        return start + m.start()
    return len(text)


def refresh_last_updated(preamble, date_str):
    pat = re.compile(r"^Last updated:.*$", re.MULTILINE)
    if pat.search(preamble):
        return pat.sub(f"Last updated: {date_str}", preamble)
    print(
        "WARNING: 'Last updated:' line not found in STATE.md preamble — add it manually.",
        file=sys.stderr,
    )
    return preamble


def main(repo_root: Path | None = None):
    parser = argparse.ArgumentParser(
        description="Replace the ## Status section of STATE.md with fresh git + erg output."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="Path to the repository root (default: auto-detect via git rev-parse)",
    )
    args = parser.parse_args()

    if repo_root is None:
        repo_root = args.path if args.path is not None else _repo_root()

    state_file = repo_root / "STATE.md"
    if not state_file.exists():
        print(f"ERROR: {state_file} not found", file=sys.stderr)
        sys.exit(1)

    text = state_file.read_text()
    preamble, tail = split_at_status(text)

    # tail starts with "## Status\n..."; find where Status body ends
    # (i.e. where the next ## heading begins) so we can preserve everything after it.
    status_end = _next_section_idx(tail, len(STATUS_HEADING) + 1)
    tail_after_status = tail[status_end:]  # sections after ## Status (may be empty)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    preamble = refresh_last_updated(preamble, today)

    commits = get_commits(repo_root)
    ready_count, blocked_count = get_tickets(repo_root)
    status_lines = format_status(ready_count, blocked_count, commits)

    new_text = (
        preamble.rstrip()
        + "\n\n"
        + "\n".join(status_lines)
        + ("\n\n" + tail_after_status.lstrip() if tail_after_status.strip() else "\n")
    )
    state_file.write_text(new_text)

    total = len(new_text.splitlines())
    print(f"STATE.md refreshed — {len(status_lines)} status lines, {total} total.")
    if total > 40:
        print(
            f"WARNING: {total} lines exceeds 40-line cap — trim the hand-edited sections."
        )


if __name__ == "__main__":
    main()
