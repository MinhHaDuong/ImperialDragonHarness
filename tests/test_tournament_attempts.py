"""Preserved attempts must not be hidden or counted twice by the report."""

import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "attempts", Path(__file__).parents[1] / "scripts/tournament-attempts.py"
)
attempts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(attempts)


def test_counts_archived_failure_once_and_uses_retained_tokens(tmp_path):
    success = {
        "ticket": "0001",
        "arm": "a",
        "attempt": 1,
        "finished": "2026-10-07T09:00Z",
        "verdict": "OK",
        "tokens": {"out_sum": 40},
    }
    failure = dict(
        success, finished="2026-10-06T09:00Z", verdict="DNF", tokens={"out_sum": 10}
    )
    for relative, row in [
        ("runs/0001-a/run.json", success),
        ("runs/0001-a/attempts/1/run.json", success),
        ("runs-void/earlier/0001-a/run.json", failure),
        ("runs-void/earlier/0001-a/attempts/1/run.json", failure),
    ]:
        p = tmp_path / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(row))
    snapshot = {"arms": {"a": {}}, "legs": {"a": {"0001": {}}}}
    attempts.annotate(snapshot, tmp_path)
    assert snapshot["arms"]["a"]["attempts_observed"] == 2
    assert snapshot["arms"]["a"]["output_tokens_mean"] == 40
