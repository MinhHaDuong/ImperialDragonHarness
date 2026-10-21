"""Contract regression tests; the separate live acceptance proves execution."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/verify-adherence/SKILL.md"


@pytest.mark.parametrize("requirement", [
    "Include existing conventional `rules/`", "AGENTS.md", "deleted rule files", "status: ran | skipped | delegated | unavailable | invalid",
    "completion_evidence:", "Inline analysis does not count", "must not create findings", "blocking semantic finding → adherence: FAIL",
])
def test_semantic_execution_contract(requirement):
    semantic = SKILL.read_text().split("### 3. Semantic subagent")[1]
    assert requirement in semantic


def test_frozen_live_acceptance_record():
    """Checks this retained run, not execution of any future skill version."""
    evidence = json.loads((ROOT / "docs/adherence-semantic/evidence.json").read_text())
    accepted = evidence["accepted_run"]
    assert evidence["loaded_skill"]["sha256"] == hashlib.sha256(evidence["loaded_skill"]["source"].encode()).hexdigest()
    assert accepted["adherence"] == "FAIL"
    assert accepted["mechanical_runner"]["exit_status"] == 0
    assert accepted["semantic_review"]["status"] == "ran"
    assert accepted["semantic_review"]["worker_id"] != evidence["outer"]["worker_id"]
    assert accepted["semantic_review"]["launch_evidence"]
    assert accepted["semantic_review"]["completion_evidence"]
    finding = accepted["semantic_findings"][0]
    assert finding["severity"] == "blocking"
    assert (finding["file"], finding["line"]) == ("scripts/check-tree.sh", 3)
    assert finding["suggested_test"]
    worker = [json.loads(line) for line in (ROOT / "docs/adherence-semantic/worker.jsonl").read_text().splitlines()]
    completed = next(record for record in worker if record.get("kind") == "accepted_worker_result")
    assert completed["is_error"] is False
    assert completed["session_id"] == accepted["semantic_review"]["worker_id"]
    assert completed["uuid"] == accepted["semantic_review"]["completion_evidence"]["result_uuid"]
    actual_report = completed["result"]
    assert "blocking" in actual_report and "suggested_test" in actual_report
