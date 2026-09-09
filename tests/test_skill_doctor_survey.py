"""Tests for scripts/skill-doctor-survey.py — all 7 clusterers and _resolve_harness_dir."""

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "skill_doctor_survey", SCRIPTS / "skill-doctor-survey.py"
)
sds = importlib.util.module_from_spec(spec)
sys.modules["skill_doctor_survey"] = sds
spec.loader.exec_module(sds)


# ── _resolve_harness_dir ──────────────────────────────────────────────────────


def test_resolve_harness_dir_env_var(monkeypatch, tmp_path):
    """HARNESS_DIR env var takes priority and is returned directly."""
    target = tmp_path / "custom_harness"
    target.mkdir()
    monkeypatch.setenv("HARNESS_DIR", str(target))
    result = sds._resolve_harness_dir()
    assert result == target


def test_resolve_harness_dir_worktree_git_file(monkeypatch, tmp_path):
    """Follows worktree .git file -> commondir -> real harness root."""
    monkeypatch.delenv("HARNESS_DIR", raising=False)

    # Build fake repo layout:
    #   tmp_path/
    #     fake_harness/
    #       scripts/                   (so __file__/../.. == fake_harness)
    #         skill-doctor-survey.py
    #       .git                       (text file: "gitdir: <worktree_git>")
    #     worktree_git/
    #       commondir                  (text: "../real_git")
    #     real_git/                    (the real gitdir)
    fake_harness = tmp_path / "fake_harness"
    scripts_dir = fake_harness / "scripts"
    scripts_dir.mkdir(parents=True)
    fake_script = scripts_dir / "skill-doctor-survey.py"
    fake_script.write_text("# placeholder")

    worktree_git = tmp_path / "worktree_git"
    worktree_git.mkdir()
    real_git = tmp_path / "real_git"
    real_git.mkdir()

    # .git file in fake_harness
    git_file = fake_harness / ".git"
    git_file.write_text(f"gitdir: {worktree_git}\n")

    # commondir in worktree_git points to real_git relative to worktree_git
    commondir = worktree_git / "commondir"
    commondir.write_text("../real_git")

    monkeypatch.setattr(sds, "__file__", str(fake_script))
    result = sds._resolve_harness_dir()
    # real_git.parent == tmp_path
    assert result == tmp_path.resolve()


def test_resolve_harness_dir_fallback_git_dir(monkeypatch, tmp_path):
    """Falls back to script_dir when .git is a directory (not a worktree file)."""
    monkeypatch.delenv("HARNESS_DIR", raising=False)

    fake_harness = tmp_path / "fake_harness"
    scripts_dir = fake_harness / "scripts"
    scripts_dir.mkdir(parents=True)
    fake_script = scripts_dir / "skill-doctor-survey.py"
    fake_script.write_text("# placeholder")
    # .git is a directory, not a file
    (fake_harness / ".git").mkdir()

    monkeypatch.setattr(sds, "__file__", str(fake_script))
    result = sds._resolve_harness_dir()
    assert result == fake_harness.resolve()


def test_resolve_harness_dir_fallback_no_git(monkeypatch, tmp_path):
    """Falls back to script_dir when .git is absent entirely."""
    monkeypatch.delenv("HARNESS_DIR", raising=False)

    fake_harness = tmp_path / "fake_harness"
    scripts_dir = fake_harness / "scripts"
    scripts_dir.mkdir(parents=True)
    fake_script = scripts_dir / "skill-doctor-survey.py"
    fake_script.write_text("# placeholder")

    monkeypatch.setattr(sds, "__file__", str(fake_script))
    result = sds._resolve_harness_dir()
    assert result == fake_harness.resolve()


# ── _cluster_budget_raises ────────────────────────────────────────────────────














# ── _cluster_dirty_tree ───────────────────────────────────────────────────────














# ── _cluster_watermark_redetection ───────────────────────────────────────────












# ── _cluster_umbrella_not_closed ──────────────────────────────────────────────














# ── _cluster_ticket_line_format ───────────────────────────────────────────────


def test_cluster_ticket_line_format_positive():
    """One matching commit is enough (threshold >=1)."""
    commits = [
        "abc1234 tolerate plain Ticket: format in merge script",
    ]
    result = sds._cluster_ticket_line_format(commits)
    assert result is not None
    assert result["signature"] == "ticket-line-format-mismatch"
    assert result["frequency"] == 1


def test_cluster_ticket_line_format_multiple():
    """Multiple matching commits increase frequency."""
    commits = [
        "abc1234 tolerate plain ticket: format in erg",
        "def5678 fix: plain ticket: line not accepted",
    ]
    result = sds._cluster_ticket_line_format(commits)
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_ticket_line_format_below_threshold():
    """No matching commits → None (empty list is below threshold of 1)."""
    commits = [
        "abc1234 fix: unrelated commit message",
        "def5678 chore: bump version",
    ]
    result = sds._cluster_ticket_line_format(commits)
    assert result is None


def test_cluster_ticket_line_format_empty():
    """Empty input → None."""
    assert sds._cluster_ticket_line_format([]) is None


def test_cluster_ticket_line_format_needs_ticket_and_keyword():
    """Must have 'ticket:' AND ('tolerate' OR 'plain') in the commit."""
    commits = [
        "abc1234 fix ticket: parsing bug",  # has ticket: but not tolerate/plain
        "def5678 tolerate bad input in parser",  # has tolerate but not ticket:
    ]
    result = sds._cluster_ticket_line_format(commits)
    assert result is None


# ── _cluster_max_turns ────────────────────────────────────────────────────────














# ── _cluster_crash_recovery ───────────────────────────────────────────────────












# ── Score and severity sanity checks ─────────────────────────────────────────


def test_score_equals_frequency_times_weight():
    """Verify score = frequency * severity_weight.

    It covered three clusterers until ticket 0882 removed the nightbeat journal
    they read from. The surviving clusterer carries the same contract, and the
    ratio is what this asserts -- so the check is narrower now, not weaker. Add
    an arm here whenever a clusterer is added.
    """
    severity_weight = {"high": 3, "medium": 2, "low": 1}

    commits = [
        "abc1234 repair: tolerate plain Ticket: line in erg-pr-merge",
        "def5678 repair: tolerate a plain Ticket: prefix on merge",
    ]
    r = sds._cluster_ticket_line_format(commits)
    assert r is not None, "fixture must produce a pattern, or this asserts nothing"
    assert r["score"] == r["frequency"] * severity_weight[r["severity"]]
