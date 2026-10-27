"""--capture-pr runs seats, extract and capture of one merged PR in a single call."""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "attribution_record.py"
BODY = """Summary.

```attribution
kind: review-attribution
pr: 1155 · merged pending · project: .agents
writer: step=execute · runtime=fixture · model=example/writer-v1 · effort=not-stated · route=sonnet · independence=not-stated
```
"""
SEAT = "seat: correctness · runtime=claude-code · family=anthropic · route=opus · model={model} · status: ran"


@pytest.fixture
def forge(monkeypatch):
    """A PR held in memory: gh reads it, the body append edits it, capture records what it receives."""
    spec = importlib.util.spec_from_file_location("attribution_record", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pr = {"state": "MERGED", "mergedAt": "2026-10-27T21:04:00Z", "body": BODY,
          "comments": "## /gaze result\n\nresult: REVIEWED\n" + SEAT.format(model="anthropic/example-opus") + "\n",
          "captured": []}

    def gh(*args, stdin=None):
        fields = args[args.index("--json") + 1]
        if fields == "comments":
            return pr["comments"]
        if fields == "body":
            return pr["body"]
        return json.dumps({key: pr[key] for key in fields.split(",")})

    def append_to_pr(number, line, project):
        pr["body"] = module.append_line(pr["body"], line, number, project)

    def capture_record(text, record, repository, audience):
        pr["captured"].append((text, audience))
        return "captured"

    monkeypatch.setattr(module, "gh", gh)
    monkeypatch.setattr(module, "append_to_pr", append_to_pr)
    monkeypatch.setattr(module, "capture_record", capture_record)
    return module, pr


def run(module, masked_evidence=None):
    args = argparse.Namespace(capture_pr=1155, capture=Path("project"), audience="public",
                              project=".agents", masked_evidence=masked_evidence)
    return module.capture_pr(args)


def test_merged_pr_is_captured_with_its_seats_and_merge_date(forge):
    module, pr = forge
    assert run(module) == 0
    [(text, audience)] = pr["captured"]
    assert audience == "public"
    assert "pr: 1155 · merged 2026-10-27 · project: .agents" in text
    assert "seat=correctness · runtime=claude-code · model=anthropic/example-opus" in text
    assert module.parse_record(text)["reviewers"]


def test_unmerged_pr_is_refused_before_any_edit(forge):
    module, pr = forge
    pr["state"], pr["mergedAt"] = "OPEN", None
    with pytest.raises(ValueError, match="not merged"):
        run(module)
    assert pr["body"] == BODY and not pr["captured"]


def test_seat_failure_captures_nothing_and_a_rerun_resumes(forge):
    module, pr = forge
    pr["comments"] = "## /gaze result\n\n" + SEAT.format(model="not observed") + "\n"
    assert run(module) == 1
    assert not pr["captured"]
    assert run(module, masked_evidence="memory/evidence/review-attribution-pr1155.md:3") == 0
    [(text, _)] = pr["captured"]
    assert text.count("seat=correctness") == 1
    assert "model-state=runtime-masked" in text


@pytest.mark.integration
def test_cli_requires_project_and_audience():
    result = subprocess.run([sys.executable, str(SCRIPT), "--capture-pr", "1155", "--capture", "x"],
                            text=True, capture_output=True, env=child_env())
    assert result.returncode == 2
    assert "--capture-pr needs --capture PROJECT and --audience" in result.stderr
