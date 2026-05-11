#!/usr/bin/env python3
"""Survey beat outcomes since last supervisor cycle.

Emits JSON: {since, watermark_ts, prs_to_merge, failures, journal_context}
  prs_to_merge: [{project, project_path, github_repo, ticket_id, pr_number, branch}]
  failures:     [{project, project_path, ticket_id, phase, outcome, ts, cost_usd, log_file}]
  journal_context: {project_name: [last-30 journal entries]}
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
FAILURE_OUTCOMES = {"fail", "budget", "timeout"}


def _expand(p: str) -> Path:
    return Path(p).expanduser()


def _load_projects() -> list[dict]:
    data = json.loads((HARNESS_DIR / "scripts" / "projects.json").read_text())
    return [
        {"path": _expand(p["path"]), **{k: v for k, v in p.items() if k != "path"}}
        for p in data
    ]


def _github_repo(project_path: Path) -> str | None:
    r = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        cwd=project_path,
    )
    if r.returncode != 0:
        return None
    url = r.stdout.strip().removesuffix(".git")
    if "github.com" in url:
        # handles both https://github.com/org/repo and git@github.com:org/repo
        return url.split("github.com/", 1)[-1].split("github.com:", 1)[-1]
    return None


def _parse_ts(ts_str: str) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _read_jsonl(path: Path, since: datetime | None = None) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since is not None:
            ts = _parse_ts(obj.get("ts") or obj.get("last_run_at") or "")
            if ts is not None and ts < since:
                continue
        rows.append(obj)
    return rows


def _watermark(projects: list[dict]) -> datetime:
    """Latest journal entry ts across all projects; defaults to 24h ago.

    Canonical journal path: <proj["path"]>/nightbeat-supervisor-journal.jsonl.
    For the harness project this resolves to $HARNESS_DIR/nightbeat-supervisor-journal.jsonl.
    The nightbeat-supervisor skill writes ALL entries there (not to logs/ subdirs).
    """
    latest: datetime | None = None
    for proj in projects:
        journal = proj["path"] / "nightbeat-supervisor-journal.jsonl"
        for entry in _read_jsonl(journal):
            ts = _parse_ts(entry.get("ts", ""))
            if ts and (latest is None or ts > latest):
                latest = ts
    return (
        latest
        if latest is not None
        else datetime.now(timezone.utc) - timedelta(hours=24)
    )


def _find_log_file(proj_name: str, failure_ts: str) -> str | None:
    """Return log file whose name-timestamp is closest to and <= failure_ts."""
    log_dir = HARNESS_DIR / "logs" / "nightbeat"
    if not log_dir.exists():
        return None
    candidates = sorted(log_dir.glob(f"*{proj_name}*"))
    if not candidates:
        return None
    failure_dt = _parse_ts(failure_ts)
    if failure_dt is None:
        return str(candidates[-1])
    best: Path | None = None
    for c in candidates:
        # Filename starts with YYYYMMDDTHHMMSSz e.g. 20260503T120323Z
        stem = c.stem[:15]  # 20260503T120323
        try:
            file_dt = datetime.strptime(stem, "%Y%m%dT%H%M%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if file_dt <= failure_dt:
            best = c
    return str(best) if best else str(candidates[0])


def _find_open_pr(project_path: Path, ticket_id: str, github_repo: str) -> dict | None:
    """Find an open PR for ticket_id via branch naming convention t{id}-*."""
    r = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", f"t{ticket_id}-*"],
        capture_output=True,
        text=True,
        cwd=project_path,
    )
    branches = [
        line.split("\t", 1)[1].removeprefix("refs/heads/")
        for line in r.stdout.strip().splitlines()
        if "\t" in line
    ]
    for branch in branches:
        pr_r = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                github_repo,
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "number,headRefName",
            ],
            capture_output=True,
            text=True,
        )
        if pr_r.returncode == 0:
            prs = json.loads(pr_r.stdout or "[]")
            if prs:
                return {"pr_number": prs[0]["number"], "branch": prs[0]["headRefName"]}
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--since", help="ISO timestamp override (default: last journal entry)"
    )
    parser.add_argument(
        "--outcomes",
        help="Path to beat-outcomes.jsonl (default: logs/beat-outcomes.jsonl)",
    )
    args = parser.parse_args()

    projects = _load_projects()

    since: datetime = (
        _parse_ts(args.since) or _watermark(projects)
        if args.since
        else _watermark(projects)
    )

    outcomes_path = (
        Path(args.outcomes)
        if args.outcomes
        else HARNESS_DIR / "logs" / "beat-outcomes.jsonl"
    )
    outcomes = _read_jsonl(outcomes_path, since=since)

    # Raid successes: {project -> [ticket_id, ...]}
    raid_success_tickets: dict[str, list[str]] = {}
    for e in outcomes:
        if e.get("phase") == "raid" and e.get("outcome") == "success":
            tid = e.get("ticket_id")
            if tid:
                raid_success_tickets.setdefault(e["project"], []).append(tid)

    prs_to_merge: list[dict] = []
    failures: list[dict] = []
    journal_context: dict[str, list] = {}

    for proj in projects:
        proj_path: Path = proj["path"]
        proj_name = proj_path.name
        github_repo = _github_repo(proj_path)

        # PRs to merge: find open PRs for each ticket that had a raid/success
        seen_tickets: set[str] = set()
        for ticket_id in raid_success_tickets.get(proj_name, []):
            if ticket_id in seen_tickets:
                continue
            seen_tickets.add(ticket_id)
            if github_repo is None:
                continue
            pr_info = _find_open_pr(proj_path, ticket_id, github_repo)
            if pr_info:
                prs_to_merge.append(
                    {
                        "project": proj_name,
                        "project_path": str(proj_path),
                        "github_repo": github_repo,
                        "ticket_id": ticket_id,
                        "pr_number": pr_info["pr_number"],
                        "branch": pr_info["branch"],
                    }
                )

        # Failures: phases with bad outcomes
        for e in outcomes:
            if e.get("project") != proj_name:
                continue
            if e.get("outcome") not in FAILURE_OUTCOMES:
                continue
            failures.append(
                {
                    "project": proj_name,
                    "project_path": str(proj_path),
                    "ticket_id": e.get("ticket_id"),
                    "phase": e.get("phase"),
                    "outcome": e.get("outcome"),
                    "ts": e.get("ts"),
                    "cost_usd": e.get("cost_usd"),
                    "log_file": _find_log_file(proj_name, e.get("ts", "")),
                }
            )

        # Journal context: last 30 entries
        context = _read_jsonl(proj_path / "nightbeat-supervisor-journal.jsonl")[-30:]
        if context:
            journal_context[proj_name] = context

    print(
        json.dumps(
            {
                "since": since.isoformat(),
                "watermark_ts": since.isoformat(),
                "prs_to_merge": prs_to_merge,
                "failures": failures,
                "journal_context": journal_context,
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
