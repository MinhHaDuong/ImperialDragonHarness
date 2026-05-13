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


def test_cluster_budget_raises_positive():
    """Two qualifying entries trigger a finding."""
    journal = [
        {
            "action": "repair",
            "note": "Raise budget cap for claude/hk",
            "project": "claude",
        },
        {
            "action": "repair",
            "note": "budget increase for chemin-de-voix",
            "project": "chemin",
        },
    ]
    result = sds._cluster_budget_raises(journal, [])
    assert result is not None
    assert result["signature"] == "budget-cap-repeated-raises"
    assert result["frequency"] == 2


def test_cluster_budget_raises_commit_deduplication():
    """Two commits with same message deduplicate to one; need a journal entry to reach >=2."""
    # Two commits with same message (different hashes) deduplicate to 1
    commits = [
        "abc1234 raise budget for beat.py",
        "def5678 raise budget for beat.py",  # same message, deduped
    ]
    journal = [
        {"action": "repair", "note": "budget adjustment", "project": "claude"},
    ]
    result = sds._cluster_budget_raises(journal, commits)
    # journal(1) + deduped_commit(1) = 2 → triggers
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_budget_raises_dedup_collapses_below_threshold():
    """Two commits with same message deduplicate; no journal entry → only 1 → None."""
    commits = [
        "abc1234 raise budget for beat.py",
        "def5678 raise budget for beat.py",
    ]
    result = sds._cluster_budget_raises([], commits)
    assert result is None


def test_cluster_budget_raises_below_threshold():
    """Only one entry → returns None."""
    journal = [
        {"action": "repair", "note": "budget raised once", "project": "claude"},
    ]
    result = sds._cluster_budget_raises(journal, [])
    assert result is None


def test_cluster_budget_raises_empty():
    """Empty inputs → None."""
    assert sds._cluster_budget_raises([], []) is None


def test_cluster_budget_raises_no_budget_keyword():
    """repair actions without 'budget' in note are ignored."""
    journal = [
        {"action": "repair", "note": "fix test failure", "project": "claude"},
        {"action": "repair", "note": "another repair, not budget", "project": "claude"},
    ]
    result = sds._cluster_budget_raises(journal, [])
    assert result is None


# ── _cluster_dirty_tree ───────────────────────────────────────────────────────


def test_cluster_dirty_tree_positive_english():
    """English 'local changes' pattern triggers a finding."""
    lines = [
        "error: cannot checkout branch: local changes would be overwritten",
        "error: cannot checkout ref: local changes detected",
    ]
    result = sds._cluster_dirty_tree(lines)
    assert result is not None
    assert result["signature"] == "dirty-tree-blocks-checkout"
    assert result["frequency"] == 2


def test_cluster_dirty_tree_positive_french():
    """French 'modifications locales' pattern triggers a finding."""
    lines = [
        "erreur: cannot checkout branche: modifications locales seraient écrasées",
        "erreur: cannot checkout ref: modifications locales détectées",
    ]
    result = sds._cluster_dirty_tree(lines)
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_dirty_tree_files_extracted():
    """Files mentioned after tab characters are extracted."""
    lines = [
        "error: cannot checkout branch: local changes\n\tsome/file.py",
        "error: cannot checkout ref: local changes\n\tother/path.go",
    ]
    result = sds._cluster_dirty_tree(lines)
    assert result is not None
    assert (
        "some/file.py" in result["dirty_files"]
        or "other/path.go" in result["dirty_files"]
    )


def test_cluster_dirty_tree_below_threshold():
    """Only one matching line → None."""
    lines = [
        "error: cannot checkout branch: local changes would be overwritten",
        "error: cannot checkout branch: unrelated issue",
    ]
    result = sds._cluster_dirty_tree(lines)
    assert result is None


def test_cluster_dirty_tree_empty():
    """Empty input → None."""
    assert sds._cluster_dirty_tree([]) is None


def test_cluster_dirty_tree_missing_cannot_checkout():
    """'modifications locales' without 'cannot checkout' is not matched."""
    lines = [
        "warning: modifications locales présentes",
        "warning: modifications locales présentes aussi",
    ]
    result = sds._cluster_dirty_tree(lines)
    assert result is None


# ── _cluster_watermark_redetection ───────────────────────────────────────────


def test_cluster_watermark_redetection_already_repaired():
    """'already repaired' keyword triggers a finding."""
    journal = [
        {"note": "This was already repaired last cycle"},
        {"note": "Entry already repaired by previous run"},
    ]
    result = sds._cluster_watermark_redetection(journal)
    assert result is not None
    assert result["signature"] == "watermark-redetection-loop"
    assert result["frequency"] == 2


def test_cluster_watermark_redetection_keyword_variety():
    """Different triggering keywords all count."""
    journal = [
        {"note": "watermark mismatch detected"},
        {"note": "re-detect loop detected in journal"},
    ]
    result = sds._cluster_watermark_redetection(journal)
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_watermark_redetection_case_insensitive():
    """Keyword matching is case-insensitive."""
    journal = [
        {"note": "WATERMARK issue found"},
        {"note": "Already Repaired this pattern"},
    ]
    result = sds._cluster_watermark_redetection(journal)
    assert result is not None


def test_cluster_watermark_redetection_below_threshold():
    """Only one matching entry → None."""
    journal = [
        {"note": "watermark mismatch detected"},
        {"note": "unrelated note"},
    ]
    result = sds._cluster_watermark_redetection(journal)
    assert result is None


def test_cluster_watermark_redetection_empty():
    """Empty input → None."""
    assert sds._cluster_watermark_redetection([]) is None


# ── _cluster_umbrella_not_closed ──────────────────────────────────────────────


def test_cluster_umbrella_not_closed_from_journal():
    """Journal entries with umbrella + open/closed/never closed trigger a finding."""
    journal = [
        {"note": "umbrella ticket still open after children done"},
        {"note": "umbrella was never closed"},
    ]
    result = sds._cluster_umbrella_not_closed(journal, [])
    assert result is not None
    assert result["signature"] == "umbrella-not-auto-closed"
    assert result["frequency"] == 2


def test_cluster_umbrella_not_closed_from_log_lines():
    """Log lines with umbrella + closed contribute to events."""
    log_lines = [
        "umbrella ticket 0099 not closed after children merged",
        "umbrella 0100 never closed",
    ]
    result = sds._cluster_umbrella_not_closed([], log_lines)
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_umbrella_not_closed_mixed_sources():
    """Journal and log lines are combined to reach threshold."""
    journal = [{"note": "umbrella ticket open despite children closed"}]
    log_lines = ["umbrella 0042 closed improperly"]
    result = sds._cluster_umbrella_not_closed(journal, log_lines)
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_umbrella_not_closed_below_threshold():
    """Only one event total → None."""
    journal = [{"note": "umbrella never closed"}]
    result = sds._cluster_umbrella_not_closed(journal, [])
    assert result is None


def test_cluster_umbrella_not_closed_empty():
    """Empty inputs → None."""
    assert sds._cluster_umbrella_not_closed([], []) is None


def test_cluster_umbrella_not_closed_umbrella_without_status():
    """'umbrella' without open/closed/never closed doesn't match."""
    journal = [
        {"note": "created umbrella structure"},
        {"note": "umbrella design pattern used"},
    ]
    result = sds._cluster_umbrella_not_closed(journal, [])
    assert result is None


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


def test_cluster_max_turns_from_journal():
    """Journal entries with max-turns trigger a finding."""
    journal = [
        {"note": "hit max-turns limit on ticket 0042"},
        {"note": "agent exited due to max_turns exhaustion"},
    ]
    result = sds._cluster_max_turns(journal, [])
    assert result is not None
    assert result["signature"] == "max-turns-exhaustion"
    assert result["frequency"] == 2


def test_cluster_max_turns_from_log_lines():
    """Log lines with max-turns contribute to events."""
    log_lines = [
        "outcome=aborted reason=max-turns",
        "max_turns reached in pick-ticket phase",
    ]
    result = sds._cluster_max_turns([], log_lines)
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_max_turns_mixed_sources():
    """Journal and log lines are combined to reach threshold."""
    journal = [{"note": "max-turns exhaustion in raid"}]
    log_lines = ["beat aborted: max_turns exceeded"]
    result = sds._cluster_max_turns(journal, log_lines)
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_max_turns_underscore_variant():
    """Both 'max-turns' and 'max_turns' are recognized."""
    journal = [
        {"note": "max_turns was reached"},
        {"note": "max-turns limit hit"},
    ]
    result = sds._cluster_max_turns(journal, [])
    assert result is not None
    assert result["frequency"] == 2


def test_cluster_max_turns_below_threshold():
    """Only one event → None."""
    journal = [{"note": "max-turns reached once"}]
    result = sds._cluster_max_turns(journal, [])
    assert result is None


def test_cluster_max_turns_empty():
    """Empty inputs → None."""
    assert sds._cluster_max_turns([], []) is None


# ── _cluster_crash_recovery ───────────────────────────────────────────────────


def test_cluster_crash_recovery_positive():
    """Two crash recovery log lines trigger a finding."""
    log_lines = [
        "beat: crash recovery initiated after unexpected exit",
        "Beat crash recovery: restoring state from checkpoint",
    ]
    result = sds._cluster_crash_recovery(log_lines)
    assert result is not None
    assert result["signature"] == "beat-crash-recovery"
    assert result["frequency"] == 2


def test_cluster_crash_recovery_case_insensitive():
    """'Crash Recovery' (mixed case) is matched."""
    log_lines = [
        "CRASH RECOVERY: beat restarted",
        "Crash Recovery detected in supervisor",
    ]
    result = sds._cluster_crash_recovery(log_lines)
    assert result is not None


def test_cluster_crash_recovery_below_threshold():
    """Only one matching line → None."""
    log_lines = [
        "beat: crash recovery initiated",
        "unrelated log line about something else",
    ]
    result = sds._cluster_crash_recovery(log_lines)
    assert result is None


def test_cluster_crash_recovery_empty():
    """Empty input → None."""
    assert sds._cluster_crash_recovery([]) is None


def test_cluster_crash_recovery_no_match():
    """Lines without 'crash recovery' are ignored."""
    log_lines = [
        "error: beat failed with non-zero exit",
        "abort: max-turns reached",
        "warning: dirty tree detected",
    ]
    result = sds._cluster_crash_recovery(log_lines)
    assert result is None


# ── Score and severity sanity checks ─────────────────────────────────────────


def test_score_equals_frequency_times_weight():
    """Verify score = frequency * severity_weight for each clusterer."""
    severity_weight = {"high": 3, "medium": 2, "low": 1}

    # budget_raises: medium
    journal = [
        {"action": "repair", "note": "budget raised", "project": "p"},
        {"action": "repair", "note": "budget raised again", "project": "p"},
        {"action": "repair", "note": "budget raised third", "project": "p"},
    ]
    r = sds._cluster_budget_raises(journal, [])
    assert r["score"] == r["frequency"] * severity_weight[r["severity"]]

    # crash_recovery: low
    lines = [
        "crash recovery step 1",
        "crash recovery step 2",
        "crash recovery step 3",
    ]
    r = sds._cluster_crash_recovery(lines)
    assert r["score"] == r["frequency"] * severity_weight[r["severity"]]

    # watermark_redetection: high
    journal_wm = [
        {"note": "watermark issue"},
        {"note": "watermark detected again"},
    ]
    r = sds._cluster_watermark_redetection(journal_wm)
    assert r["score"] == r["frequency"] * severity_weight[r["severity"]]
