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


def test_cli_flags_present():
    src = (SCRIPTS / "trace-pr-join.py").read_text()
    for flag in ("--census", "--cache", "--owner", "--no-network"):
        assert flag in src, f"missing CLI flag {flag}"
    assert "ArgumentParser" in src
