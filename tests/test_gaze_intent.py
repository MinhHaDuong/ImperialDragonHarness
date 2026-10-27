"""Gaze by intention (ticket 1225): intent in, plan, execute, plan check, one record.

The orchestrator says what to verify and why; gaze plans the method, runs it once,
checks the plan against what ran and records one result. These tests pin the
mechanical parts: the plan check, the guidance's single home, the absence of
mechanical adherence and of the retired result lines.
"""

import importlib.util
import os
import re
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GAZE = ROOT / "skills" / "gaze"
PLAN = GAZE / "references" / "plan.md"

_spec = importlib.util.spec_from_file_location("seat_clock", ROOT / "scripts" / "seat_clock.py")
seat_clock = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seat_clock)
_spec = importlib.util.spec_from_file_location("panel_manifest_check", ROOT / "scripts" / "panel-manifest-check.py")
manifest_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(manifest_check)


def norm(text: str) -> str:
    return " ".join(text.split())


def gaze_texts() -> dict[Path, str]:
    return {p: p.read_text(encoding="utf-8") for p in sorted(GAZE.rglob("*.md"))}


def write_plan(panel: Path, manifest: str) -> None:
    panel.mkdir(parents=True, exist_ok=True)
    (panel / "manifest.txt").write_text(manifest, encoding="utf-8")
    past = time.time() - 30
    os.utime(panel / "manifest.txt", (past, past))


def report(panel: Path, item: str, first_line: str, body: str = "verdict: clear\n") -> None:
    (panel / f"{item}.md").write_text(f"{first_line}\n{body}", encoding="utf-8")


def worked_cases() -> dict[str, str]:
    """The fenced manifests of plan.md's worked cases, by their `##### ` heading."""
    text = PLAN.read_text(encoding="utf-8")
    cases = {}
    for block in text.split("\n##### ")[1:]:
        title = block.splitlines()[0].strip().lower()
        fence = re.search(r"```text\n(.*?)```", block, re.S)
        if fence:
            cases[title] = fence.group(1)
    return cases


# Intent in


def test_gaze_takes_a_free_text_intent_after_the_merge_request_number():
    skill = (GAZE / "SKILL.md").read_text(encoding="utf-8")
    hint = re.search(r"^argument-hint: (.*)$", skill, re.M).group(1)
    assert "<pr-number>" in hint and "verify" in hint and "because" in hint
    body = norm(skill)
    assert "the whole merge request against its ticket's exit criteria" in body


def test_force_approve_is_gone():
    for path, text in gaze_texts().items():
        assert "force-approve" not in text.lower() and "force_approve" not in text, path


# Plan


def test_the_cheapest_method_rule_has_one_home():
    rule = "cheapest method that settles the what"
    assert rule in norm(PLAN.read_text(encoding="utf-8")).lower()
    homes = []
    for top in ("skills", "rules", "agents", "profiles", "adapters"):
        for path in (ROOT / top).rglob("*.md"):
            with path.open(encoding="utf-8", errors="replace") as handle:  # raw file, no inlining
                raw = handle.read()
            if rule in norm(raw).lower():
                homes.append(path.relative_to(ROOT))
    assert homes == [PLAN.relative_to(ROOT)], homes


def test_a_small_intent_yields_a_one_worker_plan(tmp_path):
    cases = worked_cases()
    small = next(body for title, body in cases.items() if title.startswith("small intent"))
    assert manifest_check.check(small) == []
    items = [line for line in small.splitlines() if line.strip() and not line.startswith("#")]
    assert len(items) == 1, small
    panel = tmp_path / ".panel" / "7"
    write_plan(panel, small)
    name, _model, family, _reason = items[0].split("\t")
    report(panel, name, f"worker: model=some-model · family={family}")
    ok, lines = seat_clock.plan_check(panel)
    assert ok and lines[0] == "plan check: PASS", lines


def test_every_worked_case_is_a_valid_plan():
    cases = worked_cases()
    assert len(cases) >= 3, sorted(cases)
    for title, body in cases.items():
        assert manifest_check.check(body) == [], title
        assert re.search(r"^# intent: ", body, re.M), title
        assert re.search(r"^# budget: \d+m$", body, re.M), title


# Verify: the plan check


MANIFEST = (
    "# intent: verify the fix for finding 2 because it was blocking\n"
    "# budget: 10m\n"
    "correctness\tsmall-model\tanthropic\tthe fix is a few lines of logic\n"
    "redteam\tother-model\topenai\tthe fix touches a gate\n"
)


def test_plan_check_passes_when_every_item_reported_by_its_planned_family(tmp_path):
    panel = tmp_path / "p"
    write_plan(panel, MANIFEST)
    report(panel, "correctness", "worker: model=m1 · family=anthropic")
    report(panel, "redteam", "worker: model=m2 · family=openai")
    ok, lines = seat_clock.plan_check(panel)
    assert ok, lines
    assert lines[0] == "plan check: PASS"


def test_a_plan_item_that_did_not_run_fails_the_plan_check(tmp_path):
    panel = tmp_path / "p"
    write_plan(panel, MANIFEST)
    report(panel, "correctness", "worker: model=m1 · family=anthropic")
    ok, lines = seat_clock.plan_check(panel)
    assert not ok
    assert lines[0].startswith("plan check: FAIL")
    assert "redteam: no report" in lines[0]


def test_a_worker_of_another_family_is_a_named_deviation(tmp_path):
    panel = tmp_path / "p"
    write_plan(panel, MANIFEST)
    report(panel, "correctness", "worker: model=m1 · family=anthropic")
    report(panel, "redteam", "worker: model=m3 · family=anthropic")
    ok, lines = seat_clock.plan_check(panel)
    assert ok, lines
    assert lines[0].startswith("plan check: PASS with deviations")
    assert "redteam: family anthropic, planned openai" in lines[0]


def test_a_worker_that_does_not_name_its_family_is_a_deviation(tmp_path):
    panel = tmp_path / "p"
    write_plan(panel, MANIFEST)
    report(panel, "correctness", "verdict: clear")
    report(panel, "redteam", "worker: model=m2 · family=openai")
    ok, lines = seat_clock.plan_check(panel)
    assert ok
    assert "correctness: names no family" in lines[0]


def test_a_script_item_needs_no_family(tmp_path):
    panel = tmp_path / "p"
    write_plan(panel, "# intent: verify x because y\n# budget: 5m\nregression\tscript\tnone\told and new code\n")
    report(panel, "regression", "1 passed on new, 1 failed on old")
    ok, lines = seat_clock.plan_check(panel)
    assert ok and lines[0] == "plan check: PASS", lines


def test_a_failed_plan_check_never_reads_as_reviewed():
    text = norm("\n".join(gaze_texts().values()))
    assert "`plan check: FAIL` never goes with REVIEWED" in text
    assert "panel_integrity" not in text and "panel integrity:" not in text


# Gaze runs no mechanical adherence


def test_gaze_launches_no_verify_adherence():
    for path, text in gaze_texts().items():
        for marker in ("/verify-adherence", "\"verify-adherence\"", "adherence-seat", "adherence_verdict", "Agent A"):
            assert marker not in text, (path, marker)
    output = (GAZE / "references" / "output.md").read_text(encoding="utf-8")
    assert not re.search(r"^adherence:", output, re.M)


def test_verify_gate_reads_adherence_from_the_gate_record():
    gate = (ROOT / "skills" / "verify-gate" / "SKILL.md").read_text(encoding="utf-8")
    assert "--adherence-from" not in gate
    assert "adherence" in norm(gate) and "gate record" in norm(gate)
    script = (ROOT / "scripts" / "merge-gate.py").read_text(encoding="utf-8")
    assert "adherence-from" not in script and "adherence_from" not in script


# Retired machinery


def test_retired_lines_and_files_are_gone():
    assert not (GAZE / "references" / "battery.md").exists()
    for top in ("skills", "agents", "profiles"):
        for path in (ROOT / top).rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in ("battery:", "review_groups:", "multi_ticket:", "panel_integrity:", "One retry"):
                assert line not in text, (path, line)


def test_gaze_is_one_pass():
    text = norm((GAZE / "SKILL.md").read_text(encoding="utf-8"))
    assert "One pass, no recursion" in text
    assert "no worker launches a further review" in text


# Callers pass an intent and keep no fixed gaze round loop


@pytest.mark.parametrize("skill", ["hunt", "raid", "merge"])
def test_callers_send_a_narrower_intent_not_a_fixed_round_loop(skill):
    text = norm((ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8"))
    assert "narrower intent" in text, skill
    assert "up to 3 rounds" not in text and "round 3 still has findings" not in text


def test_detached_gaze_passes_the_intent_verbatim():
    text = norm((ROOT / "skills" / "raid" / "references" / "detached-gaze.md").read_text(encoding="utf-8"))
    assert "intent" in text and "verbatim" in text
