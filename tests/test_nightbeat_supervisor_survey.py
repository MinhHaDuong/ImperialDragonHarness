"""Tests for nightbeat-supervisor-survey.py — branch filtering."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "nightbeat_supervisor_survey", SCRIPTS / "nightbeat-supervisor-survey.py"
)
nbs = importlib.util.module_from_spec(spec)
sys.modules["nightbeat_supervisor_survey"] = nbs
spec.loader.exec_module(nbs)


def _mock_gh_pr_list(prs: list[dict]):
    """Return a mock for subprocess.run that returns the given PR list."""

    class FakeResult:
        returncode = 0
        stdout = json.dumps(prs)

    return FakeResult()


def test_skips_open_ticket_creation_branches():
    prs = [
        {"number": 133, "headRefName": "open-0130-0131"},
        {"number": 134, "headRefName": "t0130-extract-helpers"},
        {"number": 135, "headRefName": "open-0042"},
    ]
    with patch("subprocess.run", return_value=_mock_gh_pr_list(prs)):
        results = nbs._list_open_prs(Path("/tmp"), "owner/repo")
    assert len(results) == 1
    assert results[0]["pr_number"] == 134
    assert results[0]["ticket_id"] == "0130"
    assert results[0]["branch"] == "t0130-extract-helpers"


def test_keeps_regular_ticket_branches():
    prs = [
        {"number": 10, "headRefName": "t0099-fix-parser"},
        {"number": 11, "headRefName": "t0100-add-tests"},
    ]
    with patch("subprocess.run", return_value=_mock_gh_pr_list(prs)):
        results = nbs._list_open_prs(Path("/tmp"), "owner/repo")
    assert len(results) == 2
    ticket_ids = {r["ticket_id"] for r in results}
    assert ticket_ids == {"0099", "0100"}


def test_empty_when_all_are_ticket_creation():
    prs = [
        {"number": 50, "headRefName": "open-0200"},
        {"number": 51, "headRefName": "open-0201-0202"},
    ]
    with patch("subprocess.run", return_value=_mock_gh_pr_list(prs)):
        results = nbs._list_open_prs(Path("/tmp"), "owner/repo")
    assert results == []
