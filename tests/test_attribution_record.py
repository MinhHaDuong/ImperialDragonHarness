"""Attribution capture preserves attempts and mechanical defect joins."""

import importlib.util
import json
import re
import sys
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
    document = (ROOT / "conception" / "2026-10-02-reviewer-attribution-design.md").read_text()
    section = document.split("### Valid capture example (synthetic fixture)")[1]
    template = section.split("```text\n")[1].split("```")[0]
    assert reader.parse_record(template) == reader.parse_record(RECORD)


def test_roar_requires_reviewed_merge_capture_and_visible_failure():
    roar = (ROOT / "skills" / "roar" / "runbooks" / "capture.md").read_text()
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
    runbook = ROOT / "skills" / "roar" / "runbooks" / "capture.md"
    capture = runbook.read_text().split("Validate the complete record before writing:")[1]
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
    result = subprocess.run([sys.executable, str(SCRIPT), "--capture", str(project), "--audience", "public"],
                            input=text, text=True, capture_output=True, env=child_env())
    assert result.returncode != 0
    assert "malformed" in result.stderr
    assert not list(project.glob("memory/journal/*/*"))


@pytest.mark.integration
def test_capture_round_trip_and_invalid_record_writes_nothing(tmp_path):
    project = tmp_path / "project"
    subprocess.run(["git", "init", "--quiet", str(project)], env=child_env(), check=True)
    command = [sys.executable, str(SCRIPT), "--capture", str(project), "--audience", "public"]
    captured = subprocess.run(command, input=RECORD, text=True, capture_output=True, env=child_env())
    assert captured.returncode == 0, captured.stderr
    entries = list(project.glob("memory/journal/*/*-review-attribution-pr1164.md"))
    assert len(entries) == 1
    parsed = subprocess.run([sys.executable, str(SCRIPT), str(entries[0])], text=True,
                            capture_output=True, env=child_env(), check=True)
    assert len(json.loads(parsed.stdout)["reviewers"]) == 3
    bad = subprocess.run(command, input=RECORD.replace("1164", "1165").replace(" · status: failed", ""),
                         text=True, capture_output=True, env=child_env())
    assert bad.returncode != 0
    assert not list(project.glob("memory/journal/*/*pr1165*"))


MASK = 'model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:3'


def test_typed_mask_preserves_facts_without_inventing_identity(reader):
    text = RECORD.replace('model=example/writer-v1', MASK).replace('model=example/reviewer-v1', MASK)
    parsed = reader.parse_record(text)
    assert reader.runtime_masked(parsed)
    assert 'model' not in parsed['writer']
    assert parsed['writer']['model-evidence'].endswith(':3')
    assert parsed['defect_labels'] == ['scripts/example.py:12']
    assert len(parsed['reviewers']) == 3


@pytest.mark.parametrize('mask', [
    'model-state=unknown · model-evidence=evidence.md:1',
    'model-state=runtime-masked',
    MASK + ' · model=example/writer-v1',
    MASK + ' · model-version=v1',
    'model-state=runtime-masked · model-evidence=../evidence.md:1',
    'model-state=runtime-masked · model-evidence=/evidence.md:1',
    'model-state=runtime-masked · model-evidence=evidence.md:0',
    'model=runtime-masked',
])
def test_mask_requires_exclusive_typed_evidence(reader, mask):
    with pytest.raises(ValueError):
        reader.parse_record(RECORD.replace('model=example/writer-v1', mask))


@pytest.mark.integration
def test_masked_capture_query_round_trip(tmp_path):
    project = tmp_path / 'project'
    subprocess.run(['git', 'init', '--quiet', str(project)], env=child_env(), check=True)
    text = RECORD.replace('model=example/writer-v1', MASK)
    captured = subprocess.run([sys.executable, str(SCRIPT), '--capture', str(project), '--audience', 'public'],
                              input=text, text=True, capture_output=True, env=child_env())
    assert captured.returncode == 0, captured.stderr
    queried = subprocess.run([sys.executable, str(ROOT / 'scripts/attribution_query.py'), str(project), '--json'],
                             text=True, capture_output=True, env=child_env(), check=True)
    data = json.loads(queried.stdout)
    assert data['records']['valid'] == data['records']['runtime_masked'] == 1
    assert data['records']['model_attributable'] == 0
    assert data['scores'] == data['pairs'] == []
    assert 'runtime-masked' in queried.stderr


def test_pr1211_preserves_all_original_attempts_and_draft(reader):
    draft = (ROOT / "memory/pending-capture-pr1211.md.txt").read_text().split("\n\nResolution (1038", 1)[0]
    text = (ROOT / "memory/journal/2026/2026-10-06-review-attribution-pr1211.md").read_text()
    parsed = reader.parse_record(text)
    assert len(parsed["reviewers"]) == 15
    assert reader.runtime_masked(parsed)
    assert all(attempt["status"] == "ran" for attempt in parsed["reviewers"])
    normalized = draft.replace("finding: blocker", "finding: verifiable")
    assert [line for line in text.splitlines() if line.startswith("  finding:")] == [
        line for line in normalized.splitlines() if line.startswith("  finding:")]
    assert "HOME-clobber incident" in text
    assert text.count("#pullrequestreview-") == 3


# ── Per-PR attribution block (ticket 1149) ───────────────────────────────────
BLOCK_BODY = """Summary.

```attribution
kind: review-attribution
pr: 1149 · merged pending · project: .agents
writer: step=plan · runtime=fixture · model=example/planner-v1 · effort=not-stated · route=opus · independence=not-stated
writer: step=execute · runtime=fixture · model-state=runtime-masked · model-evidence=docs/evidence.md:3 · effort=not-stated · route=sonnet · independence=not-stated
reviewer: step=review · seat=correctness · runtime=fixture · model=example/reviewer-v1 · effort=medium · route=opus · independence=cross-family · status: ran
  finding: verifiable · scripts/example.py:12 · adopted: yes
reviewer: step=gate · seat=gate · runtime=fixture · model=example/gate-v1 · effort=not-stated · route=opus · independence=same-family · status: ran
```
"""


def run_pr_body(body):
    return subprocess.run([sys.executable, str(SCRIPT), "--pr-body"], input=body, text=True,
                          capture_output=True, env=child_env())


def test_pr_body_block_parses_strict_with_steps_and_masked_writer(reader):
    record = reader.parse_pr_body(BLOCK_BODY)
    assert record["merged"] == "pending"
    assert record["writer"]["step"] == "execute"
    assert [w["step"] for w in record["steps"]] == ["plan", "execute"]
    assert reader.runtime_masked(record)
    assert [r["step"] for r in record["reviewers"]] == ["review", "gate"]
    result = run_pr_body(BLOCK_BODY)
    assert (result.returncode, result.stdout) == (0, "ok\n")


def test_pr_body_without_block_is_missing_not_ok():
    result = run_pr_body("Summary only.\n")
    assert (result.returncode, result.stdout) == (1, "missing\n")


@pytest.mark.parametrize("old,new", [
    (" · effort=medium", ""),
    (" · route=opus · independence=cross-family", " · independence=cross-family"),
    (" · independence=same-family", ""),
    ("step=review · ", ""),
    ("independence=same-family", "independence=maybe"),
    ("effort=medium", "effort=not stated"),
    ("step=gate", "step=plan"),
    ("step=execute", "step=plan"),
    ("merged pending", "merged soon"),
])
def test_pr_body_strict_rejects_incomplete_lines(reader, old, new):
    assert old in BLOCK_BODY
    with pytest.raises(ValueError):
        reader.parse_pr_body(BLOCK_BODY.replace(old, new))
    assert run_pr_body(BLOCK_BODY.replace(old, new)).stdout.startswith("invalid: ")


def test_pr_body_requires_exactly_one_closed_block(reader):
    with pytest.raises(ValueError, match="2 attribution blocks"):
        reader.parse_pr_body(BLOCK_BODY + BLOCK_BODY)
    with pytest.raises(ValueError, match="never closed"):
        reader.parse_pr_body(BLOCK_BODY.rsplit("```", 1)[0])


def test_lenient_mode_keeps_old_records_and_refuses_pending(reader):
    assert reader.parse_record(RECORD)["steps"] == [reader.parse_record(RECORD)["writer"]]
    with pytest.raises(ValueError):
        reader.parse_record(RECORD.replace("merged 2026-10-03", "merged pending"))
    with pytest.raises(ValueError, match="distinct step"):
        reader.parse_record(RECORD.replace("\nreviewer", "\nwriter: runtime=x · model=a/b · effort=low\nreviewer", 1))


def test_canonical_template_is_not_strict_valid(reader):
    with pytest.raises(ValueError):
        reader.parse_record(RECORD, strict=True)


# ── Writers append the block, roar extracts it (ticket 1151) ─────────────────
PLAN = ("writer: step=plan · runtime=fixture · model=example/planner-v1 · effort=not-stated"
        " · route=opus · independence=not-stated")
EXECUTE = ("writer: step=execute · runtime=fixture · model=example/writer-v1 · effort=not-stated"
           " · route=sonnet · independence=not-stated")
REVIEW = ("reviewer: step=review · seat=correctness · runtime=fixture · model=example/reviewer-v1"
          " · effort=not-stated · route=opus · independence=cross-family · status: ran")
GATE = ("reviewer: step=gate · seat=gate · runtime=fixture · model=example/gate-v1"
        " · effort=not-stated · route=opus · independence=same-family · status: ran")


def run_append(body, line, *extra):
    return subprocess.run([sys.executable, str(SCRIPT), "--append", line, *extra], input=body,
                          text=True, capture_output=True, env=child_env())


def test_append_creates_closed_plain_block_when_absent(reader):
    result = run_append("Summary.\n", PLAN, "--pr", "1151", "--project", ".agents")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines.count("```attribution") == 1 and lines.count("```") == 1
    assert "kind: review-attribution" in lines
    assert "pr: 1151 · merged pending · project: .agents" in lines
    assert lines.index(PLAN) < lines.index("```")
    assert result.stdout.startswith("Summary.\n")


def test_append_without_block_needs_pr_and_project():
    result = run_append("Summary.\n", PLAN)
    assert result.returncode == 1 and "--pr" in result.stderr


def test_append_into_existing_block_keeps_one_block_and_order(reader):
    body = run_append("Summary.\n", PLAN, "--pr", "1151", "--project", ".agents").stdout
    for line in (EXECUTE, REVIEW, GATE):
        body = run_append(body, line).stdout
    assert body.count("```attribution") == 1
    record = reader.parse_pr_body(body)
    assert [w["step"] for w in record["steps"]] == ["plan", "execute"]
    assert [r["step"] for r in record["reviewers"]] == ["review", "gate"]
    assert run_pr_body(body).stdout == "ok\n"


def test_append_writer_after_reviewers_lands_before_them(reader):
    body = run_append("", PLAN, "--pr", "9", "--project", "p").stdout
    for line in (REVIEW, GATE):
        body = run_append(body, line).stdout
    after = run_append(body, EXECUTE)
    assert after.returncode == 0, after.stderr
    lines = after.stdout.splitlines()
    assert lines.index(PLAN) < lines.index(EXECUTE) < lines.index(REVIEW) < lines.index(GATE)
    record = reader.parse_pr_body(after.stdout)
    assert [w["step"] for w in record["steps"]] == ["plan", "execute"]
    assert [r["step"] for r in record["reviewers"]] == ["review", "gate"]


def test_append_multiline_reviewer_with_finding(reader):
    body = run_append("", PLAN, "--pr", "9", "--project", "p").stdout
    body = run_append(body, EXECUTE).stdout
    finding = "  finding: verifiable · scripts/example.py:12 · adopted: yes"
    body = run_append(body, REVIEW + "\n" + finding).stdout
    assert reader.parse_pr_body(body)["reviewers"][0]["findings"][0]["adopted"] is True


def test_append_refuses_unclosed_or_duplicate_block(reader):
    assert run_append(BLOCK_BODY.rsplit("```", 1)[0], GATE).returncode == 1
    assert run_append(BLOCK_BODY + BLOCK_BODY, GATE).returncode == 1


@pytest.mark.integration
def test_extract_swaps_pending_for_merge_date_and_feeds_capture(reader):
    result = subprocess.run([sys.executable, str(SCRIPT), "--extract", "--merged", "2026-10-21"],
                            input=BLOCK_BODY, text=True, capture_output=True, env=child_env())
    assert result.returncode == 0, result.stderr
    assert "merged 2026-10-21" in result.stdout and "pending" not in result.stdout
    assert result.stdout.startswith("kind: review-attribution\n")
    assert reader.parse_record(result.stdout)["merged"] == "2026-10-21"


@pytest.mark.integration
@pytest.mark.parametrize("body,args", [
    ("no block\n", ["--merged", "2026-10-21"]),
    (BLOCK_BODY, ["--merged", "soon"]),
    (BLOCK_BODY.replace("step=execute", "step=plan"), ["--merged", "2026-10-21"]),
])
def test_extract_fails_loud(body, args):
    result = subprocess.run([sys.executable, str(SCRIPT), "--extract", *args], input=body,
                            text=True, capture_output=True, env=child_env())
    assert result.returncode == 1 and result.stdout == ""


def gh_stub(tmp_path, drop):
    """A gh whose PR body lives in a file; the first `drop` PATCHes are silently lost."""
    store = tmp_path / "body"
    store.write_text("Summary.\n")
    stub = tmp_path / "bin" / "gh"
    stub.parent.mkdir()
    stub.write_text(f"""#!/usr/bin/env bash
if [[ "$*" == *PATCH* ]]; then
  echo patch >> {tmp_path}/patches
  if (( $(wc -l < {tmp_path}/patches) <= {drop} )); then cat >/dev/null; echo '{{}}'; exit 0; fi
  jq -r .body > {store}; echo '{{}}'
else jq -Rs '{{body: .}}' {store}; fi
""")
    stub.chmod(0o755)
    return store, stub.parent


def run_append_pr(bin_dir, line):
    env = child_env() | {"PATH": f"{bin_dir}:{child_env()['PATH']}"}
    return subprocess.run([sys.executable, str(SCRIPT), "--append-pr", "1151", "--append", line,
                           "--project", ".agents"], text=True, capture_output=True, env=env)


def test_append_pr_reads_back(tmp_path):
    store, bin_dir = gh_stub(tmp_path, drop=0)
    assert run_append_pr(bin_dir, PLAN).returncode == 0
    assert PLAN in store.read_text()


def test_append_pr_retries_once_when_write_is_lost(tmp_path):
    store, bin_dir = gh_stub(tmp_path, drop=1)
    result = run_append_pr(bin_dir, PLAN)
    assert result.returncode == 0, result.stderr
    assert PLAN in store.read_text()
    assert (tmp_path / "patches").read_text().count("patch") == 2


def test_append_pr_fails_loud_when_both_writes_are_lost(tmp_path):
    store, bin_dir = gh_stub(tmp_path, drop=2)
    result = run_append_pr(bin_dir, PLAN)
    assert result.returncode == 1 and "lost" in result.stderr
    assert (tmp_path / "patches").read_text().count("patch") == 2


def test_skills_wire_the_helper_modes():
    roar = (ROOT / "skills" / "roar" / "runbooks" / "capture.md").read_text()
    assert "--extract" in roar and "gh pr view" in roar
    raid = (ROOT / "skills" / "raid" / "SKILL.md").read_text()
    assert "--append-pr" in raid
    gaze = (ROOT / "skills" / "gaze" / "SKILL.md").read_text()
    assert "--append-pr" in gaze
