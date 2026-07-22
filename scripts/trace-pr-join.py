#!/usr/bin/env python3
"""Forge join for the trace-economics study — ticket 0244 (H4 + quality baseline).

Reads the census CSV's `pr_numbers` column (main agents only), maps each
project to its GitHub repo, and fetches per-PR diff size and review
outcome (merged flag, REROLL/ESCALATE mentions in comments) via the gh
CLI. Results are cached to a committed CSV so the analysis re-runs
offline (`--no-network` uses cache only; missing PRs stay blank rather
than failing the run).

The fetch layer is the only network code in the study; the statistics
themselves stay zero-LLM and offline.
"""

import argparse
import csv
import json
import logging
import re
import subprocess
from pathlib import Path

log = logging.getLogger("trace-pr-join")

OWNER_DEFAULT = "MinhHaDuong"
CACHE_FIELDS = [
    "repo",
    "pr",
    "additions",
    "deletions",
    "merged",
    "reroll_mentions",
    "escalate_mentions",
]


def project_to_repo(project: str) -> str | None:
    """Map an encoded project dir name to its repo name."""
    if project == "-home-haduong--claude":
        return "ImperialDragonHarness"
    m = re.fullmatch(r"-home-haduong-([\w-]+)", project)
    return m.group(1) if m else None


def collect_pairs(rows: list[dict]) -> list[tuple[str, int]]:
    """Unique (repo, pr) pairs from main-agent census rows, input order kept."""
    pairs: list[tuple[str, int]] = []
    for r in rows:
        if r.get("agent_id") != "main" or not r.get("pr_numbers"):
            continue
        repo = project_to_repo(r["project"])
        if repo is None:
            continue
        for n in str(r["pr_numbers"]).split(";"):
            pair = (repo, int(n))
            if pair not in pairs:
                pairs.append(pair)
    return pairs


def gh_fetch_pr(owner: str, repo: str, n: int) -> dict:
    """Fetch one PR's stats via gh REST (GraphQL avoided: intermittently 401s)."""
    pr = json.loads(
        subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/pulls/{n}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    comments = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/issues/{n}/comments", "--paginate"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {
        "repo": repo,
        "pr": n,
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "merged": bool(pr.get("merged")),
        "reroll_mentions": comments.count("REROLL"),
        "escalate_mentions": comments.count("ESCALATE"),
    }


def build_join(pairs: list[tuple[str, int]], cache: dict, fetcher) -> dict:
    """Resolve every pair from cache, then fetcher; fetch failures yield a
    blank row (merged='') so the join never silently drops a PR.

    A cached row left blank by a prior failed fetch (merged in (None, ''))
    is re-fetched on this run and overwritten; a resolved row is kept as is."""
    out = dict(cache)
    for repo, n in pairs:
        cached = out.get((repo, n))
        if cached is not None and cached.get("merged") not in (None, ""):
            continue  # resolved row — keep, never re-fetch
        try:
            out[(repo, n)] = fetcher(repo, n)
        except Exception as e:  # noqa: BLE001 — any fetch failure is non-fatal
            log.warning("fetch failed for %s#%d: %s", repo, n, e)
            out[(repo, n)] = {
                "repo": repo,
                "pr": n,
                "additions": "",
                "deletions": "",
                "merged": "",
                "reroll_mentions": "",
                "escalate_mentions": "",
            }
    return out


def load_cache(path: Path) -> dict:
    cache: dict = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                cache[(r["repo"], int(r["pr"]))] = {
                    **r,
                    "pr": int(r["pr"]),
                }
    return cache


def main() -> None:
    parser = argparse.ArgumentParser(description="Join census PR numbers to forge stats.")
    parser.add_argument("--census", type=Path, required=True, help="Per-agent census CSV")
    parser.add_argument("--cache", type=Path, required=True, help="Join cache CSV (read+write)")
    parser.add_argument("--owner", default=OWNER_DEFAULT, help="Forge owner/org")
    parser.add_argument(
        "--no-network", action="store_true", help="Resolve from cache only, fetch nothing"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with open(args.census, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    pairs = collect_pairs(rows)
    cache = load_cache(args.cache)

    if args.no_network:
        missing = [p for p in pairs if p not in cache]
        if missing:
            log.warning("%d PRs not in cache (listed, not fetched): %s", len(missing), missing)
        joined = {p: cache[p] for p in pairs if p in cache}
    else:
        joined = build_join(pairs, cache, lambda r, n: gh_fetch_pr(args.owner, r, n))

    # Finding 3: always persist the UNION so previously accumulated rows
    # not in the current census are retained; cache only grows.
    union = {**cache, **joined}
    with open(args.cache, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CACHE_FIELDS, extrasaction="ignore")
        w.writeheader()
        for key in sorted(union):
            w.writerow(union[key])
    log.info("join: %d pairs, %d resolved, cache %s", len(pairs), len(union), args.cache)


if __name__ == "__main__":
    main()
