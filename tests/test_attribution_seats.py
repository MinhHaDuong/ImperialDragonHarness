"""The gaze result's seat list becomes the PR body's reviewer lines (ticket 1155)."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "attribution_record.py"
sys.path.insert(0, str(SCRIPT.parent))  # the script imports forge and review_notes from its own directory
BODY = """Summary.

```attribution
kind: review-attribution
pr: 1155 · merged pending · project: .agents
writer: step=execute · runtime=fixture · model=example/writer-v1 · effort=not-stated · route=sonnet · independence=not-stated
```
"""
RESULT = """## /gaze result

result: REVIEWED
seat: correctness · runtime=claude-code · family=anthropic · route=opus · model=anthropic/example-opus · status: ran
seat: security · runtime=codex · family=openai · route=gpt · model=openai/example-gpt · status: failed
seat: prose · runtime=pi · family=qwen · route=qwen · model=qwen/example-qwen · status: skipped
"""
EXPECTED = [
    "reviewer: step=review · seat=correctness · runtime=claude-code · model=anthropic/example-opus"
    " · effort=not-stated · route=opus · independence=not-stated · status: ran",
    "reviewer: step=review · seat=security · runtime=codex · model=openai/example-gpt"
    " · effort=not-stated · route=gpt · independence=not-stated · status: failed",
    "reviewer: step=review · seat=prose · runtime=pi · model=qwen/example-qwen"
    " · effort=not-stated · route=qwen · independence=not-stated · status: skipped",
]


@pytest.fixture
def reader():
    spec = importlib.util.spec_from_file_location("attribution_record", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_seats(tmp_path, result, body, *extra):
    path = tmp_path / "result.md"
    path.write_text(result)
    return subprocess.run([sys.executable, str(SCRIPT), "--seats", str(path), *extra], input=body,
                          text=True, capture_output=True, env=child_env())


def reviewer_lines(body):
    return [line for line in body.splitlines() if line.startswith("reviewer: ")]


def test_listed_seats_are_reproduced_exactly(tmp_path, reader):
    """Positive control: an independently listed review comes back line for line."""
    result = run_seats(tmp_path, RESULT, BODY)
    assert result.returncode == 0, result.stderr
    assert reviewer_lines(result.stdout) == EXPECTED
    assert [r["seat"] for r in reader.parse_pr_body(result.stdout)["reviewers"]] == [
        "correctness", "security", "prose"]


def test_seat_already_appended_by_gaze_is_not_duplicated(tmp_path):
    body = BODY.replace("\n```\n", "\n" + EXPECTED[0] + "\n```\n")
    result = run_seats(tmp_path, RESULT, body)
    assert result.returncode == 0, result.stderr
    assert reviewer_lines(result.stdout) == EXPECTED


def test_seat_in_body_but_missing_from_list_is_a_capture_failure(tmp_path):
    stray = EXPECTED[0].replace("seat=correctness", "seat=performance")
    body = BODY.replace("\n```\n", "\n" + stray + "\n```\n")
    result = run_seats(tmp_path, RESULT, body)
    assert result.returncode == 1
    assert "capture failure" in result.stderr and "performance" in result.stderr
    assert reviewer_lines(result.stdout) == [stray, *EXPECTED]


def test_result_without_a_seat_list_is_a_capture_failure(tmp_path):
    result = run_seats(tmp_path, "## /gaze result\n\nresult: REVIEWED\ntelemetry: agents=6\n", BODY)
    assert result.returncode == 1
    assert "capture failure" in result.stderr and "no seat" in result.stderr


def test_unobserved_model_needs_masked_evidence(tmp_path, reader):
    unobserved = RESULT.replace("model=anthropic/example-opus", "model=not observed")
    result = run_seats(tmp_path, unobserved, BODY)
    assert result.returncode == 1
    assert "capture failure" in result.stderr and "correctness" in result.stderr
    assert reviewer_lines(result.stdout) == EXPECTED[1:]
    masked = run_seats(tmp_path, unobserved, BODY, "--masked-evidence", "docs/evidence.md:3")
    assert masked.returncode == 0, masked.stderr
    assert reviewer_lines(masked.stdout)[0] == EXPECTED[0].replace(
        "model=anthropic/example-opus",
        "model-state=runtime-masked · model-evidence=docs/evidence.md:3")
    reader.parse_pr_body(masked.stdout)


def test_multi_word_role_is_one_seat(tmp_path, reader):
    result = run_seats(tmp_path, RESULT.replace("seat: correctness", "seat: Red team"), BODY)
    assert result.returncode == 0, result.stderr
    assert reviewer_lines(result.stdout)[0] == EXPECTED[0].replace("seat=correctness", "seat=Red team")
    assert reader.parse_pr_body(result.stdout)["reviewers"][0]["seat"] == "Red team"


def test_invalid_seat_identity_fails_that_seat_only(tmp_path):
    result = run_seats(tmp_path, RESULT.replace("model=anthropic/example-opus", "model=anthropic/unknown"), BODY)
    assert result.returncode == 1
    assert "capture failure: seat correctness" in result.stderr
    assert reviewer_lines(result.stdout) == EXPECTED[1:]


def test_failures_are_logged_when_the_body_has_no_block(tmp_path):
    result = run_seats(tmp_path, "## /gaze result\n\ntelemetry: agents=6\n", "Summary.\n")
    assert result.returncode == 1
    assert "no seat" in result.stderr
    blockless = run_seats(tmp_path, RESULT.replace("model=anthropic/example-opus", "model=not observed"),
                          "Summary.\n")
    assert blockless.returncode == 1
    assert "capture failure: seat correctness" in blockless.stderr
    assert "--pr and --project" in blockless.stderr


def test_bad_masked_evidence_fails_that_seat_only(tmp_path):
    unobserved = RESULT.replace("model=anthropic/example-opus", "model=not observed")
    result = run_seats(tmp_path, unobserved, BODY, "--masked-evidence", "../x:3")
    assert result.returncode == 1
    assert "capture failure: seat correctness" in result.stderr
    assert reviewer_lines(result.stdout) == EXPECTED[1:]


# --- ticket 1301: --seats-pr reads the review's notes answers, not the PR comments ----------------

def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


@pytest.fixture
def seats_pr(tmp_path, monkeypatch, reader):
    """A local repo (no remote) whose notes may hold PR 1155's review, and a PR in memory whose
    comments hold a different, stale seat list: a reader of comments would pick the wrong seat."""
    import argparse
    import review_notes as rn
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    (repo / "f.txt").write_text("base\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    _git(repo, "switch", "-qc", "feature")
    (repo / "f.txt").write_text("change\n")
    _git(repo, "commit", "-qam", "change")
    monkeypatch.chdir(repo)
    pr = {"state": "OPEN", "body": BODY, "comment_reads": 0,
          "comments": "## /gaze result\n\nresult: REVIEWED\n" + RESULT.split("\n")[3].replace(
              "seat: correctness", "seat: stale-comment") + "\n"}

    class Forge:
        def comments(self, ref, reviews=True):
            pr["comment_reads"] += 1
            return [{"body": pr["comments"]}]

        def resolve(self, ref):
            return {"state": pr["state"], "body": pr["body"]}

    def append_to_pr(number, line, project):
        pr["body"] = reader.append_line(pr["body"], line, number, project)

    monkeypatch.setattr(reader, "forge_for", lambda number: Forge())
    monkeypatch.setattr(reader, "append_to_pr", append_to_pr)

    def review(text):
        rid = rn.open_review(str(repo), "feature", "main", unit="pr:1155")
        rn.add(str(repo), "answer", rid, {"run_id": "gz-1", "result": "REVIEWED", "seats": "panel",
                                          "coverage": {"scope": "full"}, "text": text})
        return rid

    args = argparse.Namespace(seats=None, seats_pr=1155, masked_evidence=None, project=".agents", pr=None)
    return pr, review, args


def test_seats_pr_reads_notes_answers_not_comments(seats_pr, reader):
    pr, review, args = seats_pr
    review(RESULT)
    assert reader.append_seats(args) == 0
    assert reviewer_lines(pr["body"]) == EXPECTED
    assert "stale-comment" not in pr["body"] and pr["comment_reads"] == 0


def test_seats_pr_open_pr_without_review_refuses_no_comment_fallback(seats_pr, reader):
    pr, _, args = seats_pr
    with pytest.raises(ValueError, match="no review on notes"):
        reader.append_seats(args)
    assert pr["body"] == BODY and pr["comment_reads"] == 0


def test_seat_line_as_gaze_emits_it_is_captured(seats_pr, reader):
    """PRs #1852 and #1855: gaze writes a bare model beside its family, and the body may already
    hold a hand-typed reviewer line no parser accepts; neither stops the seats being captured."""
    pr, review, args = seats_pr
    pr["body"] = BODY.replace("\n```\n", "\nreviewer: step=review · runtime=codex · model=openai/x"
                              " · effort=not-stated · route=r · independence=cross-family\n```\n")
    review("## /gaze result\n\nresult: REVIEWED\n"
           "seat: red team reviewer · runtime=codex · family=openai · route=headless · model=gpt-6.1-sol"
           " · status: ran\n")
    assert reader.append_seats(args) == 1  # the malformed body line is reported, not fatal
    assert ("reviewer: step=review · seat=red team reviewer · runtime=codex · model=openai/gpt-6.1-sol"
            " · effort=not-stated · route=headless · independence=not-stated · status: ran") in pr["body"]
