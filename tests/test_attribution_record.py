"""Attribution capture preserves attempts and mechanical defect joins."""

import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "attribution_record.py"
RECORD = """kind: review-attribution
pr: 1164 · merged 2026-10-03 · project: .agents
writer: runtime=fixture · model=example/writer-v1 · effort=standard
reviewer: seat=correctness-round1 · runtime=fixture · model=example/reviewer-v1 · status: ran
  finding: verifiable · scripts/example.py:12 · adopted: yes
reviewer: seat=regression-round3 · runtime=fixture · model=example/reviewer-v1 · status: ran
  finding: verifiable · scripts/example.py:12 · adopted: no
reviewer: seat=external-round3 · runtime=fixture · model=example/external-v1 · status: failed
"""


@pytest.fixture
def reader():
    spec = importlib.util.spec_from_file_location("attribution_record", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shared_anchor_and_separate_attempts(reader):
    record = reader.parse_record(RECORD)
    assert len(record["reviewers"]) == 3
    assert record["reviewers"][0]["findings"][0]["anchor"] == "scripts/example.py:12"
    assert record["reviewers"][1]["findings"][0]["anchor"] == "scripts/example.py:12"
    assert record["reviewers"][2]["status"] == "failed"
    assert record["defect_labels"] == ["scripts/example.py:12"]


@pytest.mark.parametrize("old,new", [
    ("kind: review-attribution", "kind: ordinary"),
    ("pr: 1164", "pr: zero"),
    ("merged 2026-10-03", "merged 2026-99-03"),
    (" · effort=standard", ""),
    ("model=example/writer-v1", "model=alias"),
    ("model=example/writer-v1", "model=example/unknown"),
    (" · status: failed", ""),
    ("status: failed", "status: ok"),
    ("scripts/example.py:12", "../example.py:12"),
    ("scripts/example.py:12", "/example.py:12"),
    ("scripts/example.py:12", "scripts/./example.py:12"),
    ("scripts/example.py:12", "scripts/example.py:0"),
    ("adopted: yes", "adopted: maybe"),
])
def test_malformed_required_facts_fail_loud(reader, old, new):
    with pytest.raises(ValueError):
        reader.parse_record(RECORD.replace(old, new))


@pytest.mark.parametrize("fact", ["finding", "defect-confirmed"])
def test_malformed_optional_fact_separator_fails_loud(reader, fact):
    text = RECORD.replace("  finding:", "  finding :") if fact == "finding" else RECORD + (
        "defect-confirmed : scripts/missed.py:31 · source: post-merge-fix · pr: 1200\n")
    with pytest.raises(ValueError, match="line .*malformed"):
        reader.parse_record(text)


@pytest.mark.parametrize("order", [(0, 2, 1), (1, 0, 2), (2, 0, 1)])
def test_header_order_is_canonical(reader, order):
    lines = [line for line in RECORD.splitlines(keepends=True) if not line.startswith("  finding:")]
    text = lines[0] + "".join(lines[index + 1] for index in order) + "".join(lines[4:])
    with pytest.raises(ValueError, match="line .*order"):
        reader.parse_record(text)


def test_no_reviewers_and_same_attempt_duplicate_fail(reader):
    with pytest.raises(ValueError):
        reader.parse_record(RECORD.split("reviewer:")[0])
    finding = "  finding: verifiable · scripts/example.py:12 · adopted: yes\n"
    with pytest.raises(ValueError, match="duplicate"):
        reader.parse_record(RECORD.replace(finding, finding + finding))


def test_context_is_opaque_and_post_merge_events_repeat(reader):
    assert reader.parse_record(RECORD + "\nContext: prose A\n") == reader.parse_record(RECORD + "\nUnrelated prose B\n")
    event = "defect-confirmed: scripts/missed.py:31 · source: post-merge-fix · pr: 1200\n"
    parsed = reader.parse_record(RECORD.replace("adopted: yes", "adopted: no") + event * 2)
    assert len(parsed["defect_confirmed"]) == 2
    assert parsed["defect_labels"] == ["scripts/missed.py:31"]


def test_revision_and_skipped_attempt_survive(reader):
    parsed = reader.parse_record(RECORD.replace("status: failed", "status: skipped").replace(
        "model=example/external-v1", "model=example/external-v1 · model-version=revision-123"))
    assert parsed["reviewers"][2]["model-version"] == "revision-123"
    assert parsed["reviewers"][2]["status"] == "skipped"


def test_canonical_template_parses_verbatim(reader):
    document = (ROOT / "docs" / "2026-10-02-reviewer-attribution-design.md").read_text()
    section = document.split("### Valid capture example (synthetic fixture)")[1]
    template = section.split("```text\n")[1].split("```")[0]
    assert reader.parse_record(template) == reader.parse_record(RECORD)


def test_roar_requires_reviewed_merge_capture_and_visible_failure():
    roar = (ROOT / "skills" / "roar" / "SKILL.md").read_text()
    capture = roar.split("**Capture review attribution for every reviewed merged PR**")[1]
    assert "attribution_record.py\" --capture" in capture
    assert "capture failure" in capture
    assert "step 11" in capture
    assert "never from" in capture


@pytest.mark.integration
def test_roar_capture_command_works_in_fresh_unrelated_shell(tmp_path):
    project = tmp_path / "unrelated-project"
    subprocess.run(["git", "init", "--quiet", str(project)], env=child_env(), check=True)
    skill = ROOT / "skills" / "roar" / "SKILL.md"
    capture = skill.read_text().split("Validate the complete record before writing:")[1]
    command = next(command for command in re.findall(r"`([^`]+)`", capture)
                   if 'attribution_record.py" --capture' in command)
    command = command.replace("<loaded-SKILL.md>", str(skill))
    environment = child_env()
    environment.pop("IDH_ROOT", None)
    environment["PROJECT_REPO"] = str(project)
    result = subprocess.run(["bash", "--noprofile", "--norc", "-c", command], cwd=project,
                            input=RECORD, text=True, capture_output=True, env=environment)
    assert result.returncode == 0, result.stderr
    assert len(list(project.glob("memory/journal/*/*-review-attribution-pr1164.md"))) == 1


@pytest.mark.integration
@pytest.mark.parametrize("fact", ["finding", "defect-confirmed"])
def test_malformed_optional_facts_never_capture(tmp_path, fact):
    project = tmp_path / "project"
    subprocess.run(["git", "init", "--quiet", str(project)], env=child_env(), check=True)
    text = RECORD.replace("  finding:", "  finding :") if fact == "finding" else RECORD + (
        "defect-confirmed : scripts/missed.py:31 · source: post-merge-fix · pr: 1200\n")
    result = subprocess.run(["python3", str(SCRIPT), "--capture", str(project), "--audience", "public"],
                            input=text, text=True, capture_output=True, env=child_env())
    assert result.returncode != 0
    assert "malformed" in result.stderr
    assert not list(project.glob("memory/journal/*/*"))


@pytest.mark.integration
def test_capture_round_trip_and_invalid_record_writes_nothing(tmp_path):
    project = tmp_path / "project"
    subprocess.run(["git", "init", "--quiet", str(project)], env=child_env(), check=True)
    command = ["python3", str(SCRIPT), "--capture", str(project), "--audience", "public"]
    captured = subprocess.run(command, input=RECORD, text=True, capture_output=True, env=child_env())
    assert captured.returncode == 0, captured.stderr
    entries = list(project.glob("memory/journal/*/*-review-attribution-pr1164.md"))
    assert len(entries) == 1
    parsed = subprocess.run(["python3", str(SCRIPT), str(entries[0])], text=True,
                            capture_output=True, env=child_env(), check=True)
    assert len(json.loads(parsed.stdout)["reviewers"]) == 3
    bad = subprocess.run(command, input=RECORD.replace("1164", "1165").replace(" · status: failed", ""),
                         text=True, capture_output=True, env=child_env())
    assert bad.returncode != 0
    assert not list(project.glob("memory/journal/*/*pr1165*"))
