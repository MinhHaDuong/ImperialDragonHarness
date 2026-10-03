"""Guard: raid wave annotations must share one mergeable base commit.

Ticket 1016. The 2026-10-02 raid landed the same annotation patch as three
distinct commits (26c8ab73 native vs 635cf70c cherry-pick) because four
executors forked while parallel sessions advanced main — patch-equivalent
commits are not merge-equivalent. Phase 4 must therefore record WAVE_BASE as
the last annotation commit, every wave branch must fork from that exact SHA,
a mid-wave main advance rebases WAVE_BASE once onto the new main and then
moves each wave branch with git rebase --onto NEW_WAVE_BASE OLD_WAVE_BASE,
and the Phase 6 integration review must run git merge-tree pairwise on the
wave's PR heads. Text-grep only → fast tier, no marker.
"""

import re
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "raid" / "SKILL.md"


def _slice(start_hdr: str, end_hdr: str) -> str:
    """Return the SKILL.md text from start_hdr up to (not including) end_hdr."""
    text = SKILL.read_text()
    start = text.find(start_hdr)
    assert start != -1, f"{start_hdr!r} header missing"
    end = text.find(end_hdr, start)
    assert end != -1, f"{end_hdr!r} header missing (cannot bound the slice)"
    return text[start:end]


def _phase45() -> str:
    return _slice("## Phase 4: Verify feasibility", "## Phase 6")


def _phase5() -> str:
    return _slice("## Phase 5: Execute", "## Phase 6")


def _phase6() -> str:
    return _slice("## Phase 6", "## Phase 7: Merge")


def test_phase4_records_wave_base_as_last_annotation_commit():
    """Phase 4 must record WAVE_BASE after committing the annotations."""
    phase45 = _phase45()
    assert "Commit annotations." in phase45, (
        "Phase 4 must still end by committing its PASS/WARN/BLOCK annotations"
    )
    annotations = phase45.find("Commit annotations.")
    wave_base = phase45.find("WAVE_BASE")
    assert wave_base != -1, (
        "Phase 4 must record WAVE_BASE — the shared commit every wave branch forks from"
    )
    assert wave_base > annotations, (
        "WAVE_BASE must be recorded after the annotations are committed, so it is their last commit"
    )
    phase50 = phase45.find("## Phase 5.0")
    assert phase50 != -1, "Phase 5.0 (coordination PR) header missing"
    assert wave_base < phase50, (
        "WAVE_BASE must be recorded before Phase 5.0 branches any coordination PR"
    )
    pull = phase45.find("pull --rebase")
    assert pull != -1, (
        "Phase 4 must pull --rebase origin main before recording WAVE_BASE"
    )
    assert pull < wave_base, (
        "The pull --rebase must precede the WAVE_BASE recording"
    )


def test_phase5_branches_must_fork_from_wave_base():
    """Phase 5 must require every wave branch to fork from WAVE_BASE exactly."""
    phase5 = _phase5()
    wave_base = phase5.find("WAVE_BASE")
    assert wave_base != -1, (
        "Phase 5 must name WAVE_BASE — wave branches fork from that exact SHA, not from whatever main happens to be"
    )
    launch = phase5.find("launch agents")
    assert launch != -1, "Phase 5 launch-agents paragraph missing"
    assert wave_base < launch, (
        "The WAVE_BASE requirement must precede the launch-agents paragraph"
    )


def test_midwave_advance_rebases_wave_base_once_then_onto():
    """A mid-wave main advance replays WAVE_BASE once, then moves each branch --onto it."""
    phase5 = _phase5()
    assert "OLD_WAVE_BASE" in phase5 and "NEW_WAVE_BASE" in phase5, (
        "Phase 5 must name the old/new base pair of the mid-wave transition"
    )
    assert re.search(r"rebase[^.]*WAVE_BASE[^.]*onto the new main", phase5), (
        "Phase 5 must rebase the WAVE_BASE branch itself onto the new main first"
    )
    assert re.search(
        r"git -C <worktree-path> rebase --onto NEW_WAVE_BASE OLD_WAVE_BASE", phase5
    ), (
        "Each wave branch must move with git -C <worktree-path> rebase --onto "
        "NEW_WAVE_BASE OLD_WAVE_BASE inside its executor worktree, where the branch "
        "is already HEAD, so the shared annotation commits replay exactly once"
    )
    assert (
        "git rebase --onto NEW_WAVE_BASE OLD_WAVE_BASE <branch>" not in phase5
    ), (
        "The <branch>-argument form fails from the orchestrator checkout — the branch "
        "is already checked out in the executor worktree"
    )
    assert "never per-branch" in phase5, (
        "Phase 5 must forbid per-branch replays of the shared annotation commits"
    )
    assert "--force-with-lease" in phase5, (
        "Phase 5 must authorize the rewritten-SHA push explicitly with --force-with-lease, or executors stall"
    )


def test_phase6_merge_tree_pairwise_on_tickets():
    """The per-wave integration review must run merge-tree pairwise over tickets/."""
    phase6 = _phase6()
    assert "merge-tree" in phase6, (
        "Phase 6 per-wave review must run git merge-tree pairwise across wave PRs"
    )
    assert "pairwise" in phase6, (
        "The merge-tree check must be pairwise, not a single aggregate merge"
    )
    assert "tickets/" in phase6, (
        "The merge-tree check must cover the shared tickets/ files"
    )


def test_no_sidecar_mechanism():
    """The rejected sidecar option must not appear in the Phase 4-6 slice."""
    assert "sidecar" not in _phase45().lower(), (
        "The sidecar mechanism was rejected (option 2); annotations stay in the shared ticket files"
    )
