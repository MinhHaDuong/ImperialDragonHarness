"""Gaze's adherence verdict merge (ticket 1173).

The adherence seat cannot launch a worker, so gaze runs verify-adherence in
the seat with ``semantic=caller`` and launches the phase-3 semantic worker
itself. ``scripts/adherence_verdict.py`` folds the two returns into the one
verdict gaze reads. These tests are the positive control: an instruction
file in the diff with no completed semantic worker must FAIL, never PASS.
They assert on the structured fields only (``adherence``,
``semantic_review``, ``semantic_findings``), never on prose.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "adherence_verdict.py"
BATTERY = REPO / "skills" / "gaze" / "references" / "battery.md"
ADHERENCE = REPO / "skills" / "verify-adherence" / "SKILL.md"

_spec = importlib.util.spec_from_file_location("adherence_verdict", SCRIPT)
av = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(av)

IDENTITY = {
    "worker_id": "agent-abc123",
    "route": "runtime subagent",
    "launch_evidence": "Agent call agent-abc123",
    "completion_evidence": ".panel/9/adherence-semantic.md",
}


def seat(status="delegated", applicable=True, adherence="PASS", mech=None,
         sources=("AGENTS.md",)):
    return {
        "adherence": adherence,
        "escalation": None,
        "semantic_review": {
            "applicable": applicable,
            "status": status,
            "reason": "diff touches AGENTS.md",
            "rule_sources": list(sources),
        },
        "mechanical_failures": list(mech or []),
        "semantic_findings": [],
        "untested_rules": [],
    }


def worker(findings=None, reviewed=None):
    return {
        "reviewed_rules": reviewed if reviewed is not None else [
            {"rule_section": "AGENTS.md#Skills catalog",
             "evidence": "skills-catalog.md regenerated in the diff"}],
        "semantic_findings": list(findings or []),
    }


BLOCKING = {
    "rule_section": "rules/git.md#Branch and commit",
    "concern": "commit bundles two changes",
    "file": "AGENTS.md", "line": 3, "severity": "blocking",
    "suggested_test": "assert one ticket per commit",
}


# --- positive control: the skipped phase must fail ----------------------

def test_instruction_file_without_worker_fails():
    out = av.merge(seat(), None, ["AGENTS.md"], {})
    assert out["adherence"] == "FAIL"
    assert out["escalation"] == "adherence-infrastructure"
    assert out["semantic_review"]["status"] == "unavailable"


def test_seat_cannot_waive_the_phase_for_an_instruction_file():
    """A seat that declares the phase inapplicable does not discharge it
    when a conventional instruction file is in the diff."""
    s = seat(status="skipped", applicable=False, sources=())
    for path in ("CLAUDE.md", "rules/git.md", ".claude/rules/x.md",
                 "sub/AGENTS.md"):
        out = av.merge(s, None, [path], {})
        assert out["adherence"] == "FAIL", path
        assert out["semantic_review"]["applicable"] is True, path


def test_declared_rule_source_in_diff_requires_the_phase():
    s = seat(status="skipped", applicable=False,
             sources=("skills/gaze/SKILL.md",))
    out = av.merge(s, None, ["skills/gaze/SKILL.md"], {})
    assert out["adherence"] == "FAIL"


def test_worker_without_launch_identity_fails():
    out = av.merge(seat(), worker(), ["AGENTS.md"], {})
    assert out["adherence"] == "FAIL"
    assert out["semantic_review"]["status"] == "unavailable"


# --- the run phase passes ------------------------------------------------

def test_completed_worker_passes_and_records_identity():
    out = av.merge(seat(), worker(), ["AGENTS.md"], IDENTITY)
    assert out["adherence"] == "PASS"
    assert out["escalation"] is None
    sr = out["semantic_review"]
    assert sr["status"] == "ran"
    assert sr["worker_id"] == "agent-abc123"
    assert sr["completion_evidence"] == IDENTITY["completion_evidence"]
    assert sr["model"] == "unavailable"


def test_blocking_finding_fails_without_escalation():
    out = av.merge(seat(), worker([BLOCKING]), ["AGENTS.md"], IDENTITY)
    assert out["adherence"] == "FAIL"
    assert out["escalation"] is None
    assert out["semantic_findings"] == [BLOCKING]


def test_nit_finding_passes():
    nit = dict(BLOCKING, severity="nit")
    out = av.merge(seat(), worker([nit]), ["AGENTS.md"], IDENTITY)
    assert out["adherence"] == "PASS"


@pytest.mark.parametrize("bad", [
    worker(reviewed=[]),
    worker([dict(BLOCKING, severity="major")]),
    worker([dict(BLOCKING, suggested_test="")]),
    worker([{k: v for k, v in BLOCKING.items() if k != "line"}]),
    {"semantic_findings": []},
])
def test_malformed_worker_report_is_invalid(bad):
    out = av.merge(seat(), bad, ["AGENTS.md"], IDENTITY)
    assert out["adherence"] == "FAIL"
    assert out["escalation"] == "adherence-infrastructure"
    assert out["semantic_review"]["status"] == "invalid"


# --- paths that do not need the phase ------------------------------------

def test_code_only_diff_passes_without_worker():
    s = seat(status="skipped", applicable=False, sources=("AGENTS.md",))
    out = av.merge(s, None, ["scripts/foo.py"], {})
    assert out["adherence"] == "PASS"
    assert out["semantic_review"]["status"] == "skipped"


def test_seat_that_ran_the_phase_itself_needs_no_worker():
    s = seat(status="ran")
    s["semantic_review"].update(worker_id="w1", launch_evidence="x",
                                completion_evidence="y")
    out = av.merge(s, None, ["AGENTS.md"], {})
    assert out["adherence"] == "PASS"


def test_mechanical_failure_stops_before_the_phase():
    s = seat(status="skipped", adherence="FAIL",
             mech=[{"test_or_grep": "t", "rule_ref": "r", "file": "f",
                    "line": 1}])
    out = av.merge(s, None, ["AGENTS.md"], {})
    assert out["adherence"] == "FAIL"
    assert out["escalation"] is None


# --- CLI and the launch wiring -------------------------------------------

@pytest.mark.integration
def test_cli_exit_codes(tmp_path):
    seat_file = tmp_path / "adherence.md"
    seat_file.write_text("verdict:\n\n```yaml\n" + yaml.safe_dump(seat())
                         + "```\n")
    base = [sys.executable, str(SCRIPT), "--seat", str(seat_file),
            "--changed", "AGENTS.md"]
    fail = subprocess.run(base, capture_output=True, text=True,
                          env=child_env())
    assert fail.returncode == 1, fail.stderr
    assert yaml.safe_load(fail.stdout)["adherence"] == "FAIL"

    worker_file = tmp_path / "adherence-semantic.md"
    worker_file.write_text(yaml.safe_dump(worker()))
    ok = subprocess.run(
        base + ["--worker", str(worker_file),
                "--worker-id", IDENTITY["worker_id"],
                "--route", IDENTITY["route"],
                "--launch-evidence", IDENTITY["launch_evidence"],
                "--completion-evidence", IDENTITY["completion_evidence"]],
        capture_output=True, text=True, env=child_env())
    assert ok.returncode == 0, ok.stderr
    assert yaml.safe_load(ok.stdout)["semantic_review"]["status"] == "ran"


def test_gaze_launches_the_seat_with_semantic_caller():
    """The Agent A invocation hands phase 3 to gaze, and gaze folds the
    returns through the merge script."""
    battery = BATTERY.read_text(encoding="utf-8")
    block = battery.split("**Agent A — adherence**", 1)[1].split(
        "**Native `/review` and `/simplify`**", 1)[0]
    assert ('Skill(skill: "verify-adherence", args: "<branch> '
            'worktree=$primary_root/.claude/worktrees/review-<pr-number> '
            'semantic=caller")') in block
    assert "$IDH_ROOT/scripts/adherence_verdict.py" in block


def test_verify_adherence_declares_semantic_caller():
    text = ADHERENCE.read_text(encoding="utf-8")
    front = text.split("---", 2)[1]
    assert "semantic=caller" in yaml.safe_load(front)["argument-hint"]
    assert "status: ran | skipped | delegated | unavailable | invalid" in text
