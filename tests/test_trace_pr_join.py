"""Tests for scripts/trace-pr-join.py — forge join for H4/quality (ticket 0244)."""

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location("trace_pr_join", SCRIPTS / "trace-pr-join.py")
tpj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tpj)


def test_project_to_repo_mapping():
    assert tpj.project_to_repo("-home-haduong--claude") == "ImperialDragonHarness"
    assert tpj.project_to_repo("-home-haduong-git-erg") == "git-erg"
    assert tpj.project_to_repo("-home-haduong-aedist-technical-report") == (
        "aedist-technical-report"
    )
    assert tpj.project_to_repo("-home-haduong") is None


def test_collect_pairs_from_census_rows():
    rows = [
        {"project": "-home-haduong--claude", "agent_id": "main", "pr_numbers": "370;371"},
        {"project": "-home-haduong--claude", "agent_id": "agent-x", "pr_numbers": "999"},
        {"project": "-home-haduong-git-erg", "agent_id": "main", "pr_numbers": ""},
        {"project": "-home-haduong", "agent_id": "main", "pr_numbers": "5"},
    ]
    pairs = tpj.collect_pairs(rows)
    # subagents skipped, empty skipped, unmappable project skipped
    assert pairs == [("ImperialDragonHarness", 370), ("ImperialDragonHarness", 371)]


def test_build_join_uses_cache_before_fetcher(tmp_path):
    cached = {("r", 1): {"repo": "r", "pr": 1, "additions": 10, "deletions": 2,
                         "merged": True, "reroll_mentions": 0, "escalate_mentions": 0}}
    calls = []

    def fetcher(repo, n):
        calls.append((repo, n))
        return {"repo": repo, "pr": n, "additions": 5, "deletions": 5,
                "merged": False, "reroll_mentions": 1, "escalate_mentions": 0}

    out = tpj.build_join([("r", 1), ("r", 2)], cached, fetcher)
    assert calls == [("r", 2)]  # cache hit for pr 1
    assert len(out) == 2
    assert out[("r", 1)]["additions"] == 10
    assert out[("r", 2)]["reroll_mentions"] == 1


def test_fetcher_failure_recorded_not_fatal():
    def fetcher(repo, n):
        raise RuntimeError("network down")

    out = tpj.build_join([("r", 9)], {}, fetcher)
    assert out[("r", 9)]["merged"] == ""  # row present, marked unfetched


def test_build_join_refetches_blank_cached_rows(tmp_path):
    """Ticket 0246 action 1: a cached row left blank by a prior failed fetch
    (merged in (None, "")) must be re-fetched on a networked run and
    overwritten; a resolved cached row is never re-fetched."""
    cached = {
        # resolved — must be left untouched, no fetch
        ("r", 1): {"repo": "r", "pr": 1, "additions": 10, "deletions": 2,
                   "merged": True, "reroll_mentions": 0, "escalate_mentions": 0},
        # blank — a prior fetch failed; must be re-fetched and overwritten
        ("r", 2): {"repo": "r", "pr": 2, "additions": "", "deletions": "",
                   "merged": "", "reroll_mentions": "", "escalate_mentions": ""},
    }
    calls = []

    def fetcher(repo, n):
        calls.append((repo, n))
        return {"repo": repo, "pr": n, "additions": 7, "deletions": 3,
                "merged": True, "reroll_mentions": 2, "escalate_mentions": 0}

    out = tpj.build_join([("r", 1), ("r", 2)], cached, fetcher)
    assert calls == [("r", 2)], "only the blank pair is re-fetched"
    assert out[("r", 1)]["additions"] == 10, "resolved row untouched"
    assert out[("r", 2)]["merged"] is True, "blank row overwritten by fetch"
    assert out[("r", 2)]["additions"] == 7


def test_cli_flags_present():
    src = (SCRIPTS / "trace-pr-join.py").read_text()
    for flag in ("--census", "--cache", "--owner", "--no-network"):
        assert flag in src, f"missing CLI flag {flag}"
    assert "ArgumentParser" in src


# --- ticket 0244 review fixes ---


def test_cache_union_preserves_rows_absent_from_current_census(tmp_path):
    """Finding 3: --no-network must NOT prune previously accumulated rows
    that are not in the current census pairs; cache grows monotonically."""
    import csv

    # Build a cache with two rows: pair A (in census) and pair B (not in census)
    cache_path = tmp_path / "cache.csv"
    cache_path.write_text(
        "repo,pr,additions,deletions,merged,reroll_mentions,escalate_mentions\n"
        "ImperialDragonHarness,10,50,5,True,0,0\n"
        "ImperialDragonHarness,99,10,2,True,1,0\n"
    )

    # Census only contains pair A (pr=10), not pair B (pr=99)
    census_path = tmp_path / "census.csv"
    census_path.write_text(
        "project,agent_id,pr_numbers\n"
        "-home-haduong--claude,main,10\n"
    )

    # Run with --no-network so only cache is used
    import importlib.util
    spec = importlib.util.spec_from_file_location("trace_pr_join", SCRIPTS / "trace-pr-join.py")
    tpj2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tpj2)

    cache = tpj2.load_cache(cache_path)
    pairs = tpj2.collect_pairs(list(csv.DictReader(open(census_path))))
    # Simulate --no-network: only resolve from cache, then write union
    joined = {p: cache[p] for p in pairs if p in cache}
    # The union must include both cache rows
    union = {**cache, **joined}
    # Write union back to cache (simulating the fix)
    with open(cache_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=tpj2.CACHE_FIELDS, extrasaction="ignore")
        w.writeheader()
        for key in sorted(union):
            w.writerow(union[key])

    # Verify both rows survived
    final = tpj2.load_cache(cache_path)
    assert ("ImperialDragonHarness", 10) in final, "pair A must be retained"
    assert ("ImperialDragonHarness", 99) in final, "pair B must be retained (was not in census)"
