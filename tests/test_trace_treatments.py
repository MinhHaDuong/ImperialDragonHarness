"""Tests for scripts/trace-treatments.py (ticket 1170): treatment follow-up."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from child_env import child_env  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "trace_treatments", ROOT / "scripts" / "trace-treatments.py"
)
tt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tt)

MERGE = "2026-10-10"
BASELINE = {"2026-10-08": 20, "2026-10-09": 20, "2026-10-10": 20}


def _daily(first, counts, cls="no_such_tool"):
    from datetime import date, timedelta

    start = date.fromisoformat(first)
    return [
        {"date": (start + timedelta(days=i)).isoformat(), "errors_by_cause": {cls: n}}
        for i, n in enumerate(counts)
    ]


def test_class_stops_on_merge_date_reads_improved():
    t = {"id": "1", "cls": "no_such_tool", "baseline": BASELINE, "merge": MERGE}
    r = tt.evaluate(t, _daily("2026-10-11", [0] * 8))
    assert r["verdict"] == "improved"
    assert (r["days_before"], r["days_after"]) == (3, 8)
    assert r["rate_before"] == 20 and r["rate_after"] == 0


def test_class_that_does_not_stop_reads_unchanged():
    t = {"id": "1", "cls": "no_such_tool", "baseline": BASELINE, "merge": MERGE}
    r = tt.evaluate(t, _daily("2026-10-11", [20, 18, 22, 19, 21, 20, 20, 19]))
    assert r["verdict"] == "unchanged"


def test_class_that_rises_reads_worse():
    t = {"id": "1", "cls": "no_such_tool", "baseline": BASELINE, "merge": MERGE}
    r = tt.evaluate(t, _daily("2026-10-11", [40] * 8))
    assert r["verdict"] == "worse"


def test_fewer_than_seven_days_after_is_too_few_days():
    t = {"id": "1", "cls": "no_such_tool", "baseline": BASELINE, "merge": MERGE}
    r = tt.evaluate(t, _daily("2026-10-11", [0] * 6))
    assert r["verdict"] == "too_few_days"
    assert tt.evaluate(t, _daily("2026-10-11", [0] * 7))["verdict"] == "improved"


def test_no_days_after_merge_is_unmeasured():
    t = {"id": "1", "cls": "no_such_tool", "baseline": BASELINE, "merge": MERGE}
    # days on or before the merge date do not count as after
    r = tt.evaluate(t, _daily("2026-10-01", [0] * 10))
    assert r["verdict"] == "unmeasured"


def test_no_baseline_is_unmeasured_never_improved():
    t = {"id": "1", "cls": "no_such_tool", "baseline": {}, "merge": MERGE}
    r = tt.evaluate(t, _daily("2026-10-11", [0] * 10))
    assert r["verdict"] == "unmeasured"


def test_no_merge_date_or_unknown_class_is_unmeasured():
    d = _daily("2026-10-11", [0] * 10)
    assert (
        tt.evaluate(
            {"id": "1", "cls": "no_such_tool", "baseline": BASELINE, "merge": None}, d
        )["verdict"]
        == "unmeasured"
    )
    assert (
        tt.evaluate(
            {"id": "1", "cls": "bogus", "baseline": BASELINE, "merge": MERGE}, d
        )["verdict"]
        == "unmeasured"
    )


def test_zero_baseline_and_zero_after_is_unchanged():
    t = {
        "id": "1",
        "cls": "worktree_guard",
        "baseline": {"2026-10-09": 0},
        "merge": MERGE,
    }
    r = tt.evaluate(t, _daily("2026-10-11", [0] * 8, "worktree_guard"))
    assert r["verdict"] == "unchanged"


def test_parse_declared_fields_only():
    text = (
        "%erg 0.1\nTitle: x\n\n--- body ---\n## Treatment\n"
        "Treats: no_such_tool\nBaseline: 2026-10-20=26 2026-10-21=14\n"
        "This fixes the worktree_guard errors, prose is never read.\n"
    )
    cls, base = tt.parse_treatment(text)
    assert cls == "no_such_tool"
    assert base == {"2026-10-20": 26, "2026-10-21": 14}
    assert tt.parse_treatment("Title: plain\nthe no_such_tool class\n") == (None, {})


def test_repo_declares_the_three_treatments():
    found = {t["id"]: t["cls"] for t in tt.find_treatments(ROOT, ref=None)}
    assert found["1167"] == "no_such_tool"
    assert found["1166"] == "worktree_guard"
    assert found["1168"] == "write_outside_worktree"


@pytest.mark.integration
def test_merge_date_from_git_history(tmp_path):
    def git(*a):
        subprocess.run(
            ["git", "-C", str(tmp_path), *a],
            check=True,
            capture_output=True,
            env=child_env(),
        )

    git("init", "-q", "-b", "main")
    (tmp_path / "tickets/closed").mkdir(parents=True)
    f = tmp_path / "tickets/closed/0007-x.erg"
    f.write_text("a\n")
    git("add", ".")
    env = {
        "GIT_COMMITTER_DATE": "2026-10-05T12:00:00+00:00",
        "GIT_AUTHOR_DATE": "2026-10-05T12:00:00+00:00",
    }
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-qm",
            "add",
        ],
        check=True,
        env={**child_env(), **env},
    )
    assert (
        tt.merge_date(tmp_path, "tickets/closed/0007-x.erg", ref="HEAD") == "2026-10-05"
    )
    assert tt.merge_date(tmp_path, "tickets/closed/none.erg", ref="HEAD") is None
