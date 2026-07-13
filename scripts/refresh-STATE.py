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


def get_commits(repo_root: Path, n=3):
    # --first-parent: merge-level history — one line per landed PR in
    # merge-commit repos, far more work per line than raw commits.
    return run(
        ["git", "log", "--oneline", "--first-parent", f"-{n}"], repo_root
    ).splitlines()


def get_head_sha(repo_root: Path):
    return run(["git", "rev-parse", "--short", "HEAD"], repo_root)


def get_tickets(repo_root: Path):
    """Return ticket orientation from erg: counts, awaiting-author, next picks.

    `erg ready` lists only ready (unblocked, open) tickets; `erg list` lists
    all open tickets. Neither item carries a `ready` flag, so blocked is
    derived as open minus ready. Awaiting = open tickets labeled needs-human.
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
    return {
        "ready": ready_count,
        "blocked": max(len(open_tickets) - ready_count, 0),
        "awaiting": sum(
            1 for t in open_tickets if "needs-human" in (t.get("labels") or [])
        ),
        "next": [(t["id"], t["title"]) for t in ready[:2]],
    }


def _gh_json(args, repo_root: Path):
    """Run a forge-CLI command returning JSON; None when unavailable.

    Absence of the CLI, a missing remote, auth failure, or a timeout all
    degrade to None — the caller omits the line rather than failing the refresh.
    """
    try:
        r = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root,
            timeout=30,
        )
        return json.loads(r.stdout)
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ):
        return None


def get_in_flight(repo_root: Path):
    """One-phrase summary of open merge requests, or None when unknowable."""
    prs = _gh_json(
        ["pr", "list", "--state", "open", "--json", "number,createdAt,isDraft"],
        repo_root,
    )
    if prs is None:
        return None
    if not prs:
        return "no open PRs"
    drafts = sum(1 for p in prs if p["isDraft"])
    oldest = min(prs, key=lambda p: p["createdAt"])
    created = datetime.fromisoformat(oldest["createdAt"].replace("Z", "+00:00"))
    age_days = (datetime.now(timezone.utc) - created).days
    s = f"{len(prs)} open PR{'s' if len(prs) > 1 else ''}"
    if drafts:
        s += f" ({drafts} draft)"
    return f"{s}, oldest #{oldest['number']} {age_days}d"


def get_ci(repo_root: Path):
    """Latest CI conclusion on main, or None when unknowable."""
    runs = _gh_json(
        ["run", "list", "--branch", "main", "--limit", "1", "--json", "conclusion"],
        repo_root,
    )
    if not runs:
        return None
    return runs[0].get("conclusion") or "in progress"


def _truncate(title, width=48):
    return title if len(title) <= width else title[: width - 1] + "…"


def format_status(tickets, commits, head_sha=None, in_flight=None, ci=None):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    anchor = f" · as of {head_sha}" if head_sha else ""
    lines = [STATUS_HEADING, f"<!-- generated {now}{anchor} -->", ""]

    # Summary counts only — full list via: erg ready tickets/
    if tickets["ready"] or tickets["blocked"]:
        summary = (
            f"**Tickets:** {tickets['ready']} ready · {tickets['blocked']} blocked"
        )
        if tickets["awaiting"]:
            summary += f" · {tickets['awaiting']} awaiting author"
        summary += " — `erg ready tickets/` for full list"
        lines.append(summary)
        if tickets["next"]:
            picks = " · ".join(
                f"{tid} {_truncate(title)}" for tid, title in tickets["next"]
            )
            lines.append(f"  next: {picks}")

    flight_bits = [b for b in (in_flight, f"CI main: {ci}" if ci else None) if b]
    if flight_bits:
        lines.append(f"**In flight:** {' · '.join(flight_bits)}")

    if commits:
        lines.append("**Recent (first-parent):**")
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

    if tail:
        heading_line = tail.splitlines()[0]
        if heading_line.rstrip() != STATUS_HEADING:
            print(
                f"ERROR: custom Status heading {heading_line!r} — hand-maintained "
                "section; refusing to overwrite. Rename it to exactly "
                f"'{STATUS_HEADING}' to opt in to machine refresh.",
                file=sys.stderr,
            )
            sys.exit(2)
    else:
        print(f"NOTE: no '{STATUS_HEADING}' heading found — appending a generated one.")

    # tail starts with "## Status\n..."; find where Status body ends
    # (i.e. where the next ## heading begins) so we can preserve everything after it.
    status_end = _next_section_idx(tail, len(STATUS_HEADING) + 1)
    tail_after_status = tail[status_end:]  # sections after ## Status (may be empty)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    preamble = refresh_last_updated(preamble, today)

    status_lines = format_status(
        get_tickets(repo_root),
        get_commits(repo_root),
        head_sha=get_head_sha(repo_root),
        in_flight=get_in_flight(repo_root),
        ci=get_ci(repo_root),
    )

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
