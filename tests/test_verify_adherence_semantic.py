"""Check the frozen live acceptance record of the semantic adherence phase."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_live_acceptance_record():
    """Checks this retained run, not execution of any future skill version."""
    evidence = json.loads((ROOT / "conception/adherence-semantic/evidence.json").read_text())
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
    worker = [json.loads(line) for line in (ROOT / "conception/adherence-semantic/worker.jsonl").read_text().splitlines()]
    completed = next(record for record in worker if record.get("kind") == "accepted_worker_result")
    assert completed["is_error"] is False
    assert completed["session_id"] == accepted["semantic_review"]["worker_id"]
    assert completed["uuid"] == accepted["semantic_review"]["completion_evidence"]["result_uuid"]
    actual_report = completed["result"]
    assert "blocking" in actual_report and "suggested_test" in actual_report
