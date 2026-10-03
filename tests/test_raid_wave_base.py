"""Guard: raid wave annotations must share one mergeable base commit.

Ticket 1016. The 2026-10-02 raid landed the same annotation patch as three
distinct commits (26c8ab73 native vs 635cf70c cherry-pick) because four
executors forked while parallel sessions advanced main — patch-equivalent
commits are not merge-equivalent. Phase 4 must therefore record WAVE_BASE as
the last annotation commit, every wave branch must fork from that exact SHA,
a mid-wave main advance is one collective wave rebase, and the Phase 6
integration review must run git merge-tree pairwise over tickets/. Text-grep
only → fast tier, no marker.
"""

from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "raid" / "SKILL.md"


def _phase45() -> str:
    """Return the text from Phase 4 through the end of Phase 5."""
    text = SKILL.read_text()
    start = text.find("## Phase 4: Verify feasibility")
    assert start != -1, "Phase 4 (Verify feasibility) header missing"
    end = text.find("## Phase 6", start)
    assert end != -1, "Phase 6 header missing (cannot bound the Phase 4-5 slice)"
    return text[start:end]


def _phase5() -> str:
    """Return the text of Phase 5 (Execute), up to Phase 6."""
    text = SKILL.read_text()
    start = text.find("## Phase 5: Execute")
    assert start != -1, "Phase 5 (Execute) header missing"
    end = text.find("## Phase 6", start)
    assert end != -1, "Phase 6 header missing (cannot bound Phase 5)"
    return text[start:end]


def _phase6() -> str:
    """Return the text of Phase 6, up to Phase 7."""
    text = SKILL.read_text()
    start = text.find("## Phase 6")
    assert start != -1, "Phase 6 header missing"
    end = text.find("## Phase 7: Merge", start)
    assert end != -1, "Phase 7 (Merge) header missing (cannot bound Phase 6)"
    return text[start:end]


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


def test_midwave_advance_is_one_collective_rebase_with_authorized_push():
    """A mid-wave main advance rebases all wave branches together, force-with-lease."""
    phase5 = _phase5()
    assert "once" in phase5, (
        "Phase 5 must state the mid-wave rebase happens once, not per branch"
    )
    assert "together" in phase5, (
        "Phase 5 must state the collective rebase rebases all wave branches together"
    )
    assert "never per-branch" in phase5, (
        "Phase 5 must forbid per-branch rebases of the shared annotation commit"
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
