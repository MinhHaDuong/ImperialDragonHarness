"""Ticket 0990: raid Phase 6 must obtain a real /gaze verdict per PR.

The 2026-09-29 and 2026-10-02 raids launched Phase 6 as background agents one
level below the raid orchestration and got no verdict from any run (PRs
#1060/#1061, #1129-#1132): child sessions do not inherit the agent connector,
so /gaze could neither run its reviewer panel nor its gate, and both PRs
merged on author decision with Phase 6 contributing only escalations. Phase 6
must prescribe a launch shape the harness honours — the orchestrator runs
/gaze itself, or a detached headless non-interactive CLI session whose verdict
returns by artifact polling — and a REROLL bump/fix must land its commits on
the PR branch, never on main mid-wave. Phase 4 must also see the /gaze
un-reviewable breaker while splitting is still cheap. Text-grep only → fast
tier, no marker.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAID = ROOT / "skills" / "raid" / "SKILL.md"


def _slice(start_hdr: str, end_hdr: str) -> str:
    """Return the raid SKILL.md text from start_hdr up to end_hdr."""
    text = RAID.read_text()
    start = text.find(start_hdr)
    assert start != -1, f"{start_hdr!r} header missing"
    end = text.find(end_hdr, start)
    assert end != -1, f"{end_hdr!r} header missing (cannot bound the slice)"
    return text[start:end]


def _phase6() -> str:
    return _slice("## Phase 6", "## Phase 7: Merge")


def _per_ticket() -> str:
    phase6 = _phase6()
    head, sep, _ = phase6.partition("**Per-wave:**")
    assert sep, "Phase 6 per-wave header missing (cannot bound the per-ticket part)"
    return head


def _phase4() -> str:
    return _slice("## Phase 4: Verify feasibility", "## Phase 5.0")


def test_phase6_gaze_launch_returns_a_verdict():
    """Phase 6 must prescribe a launch shape that yields a real verdict.

    `background agents` is the launch shape the harness could not honour:
    a raid is itself an agent orchestration and child sessions lack the agent
    connector, so a backgrounded /gaze ran no panel and no gate.
    """
    per_ticket = _per_ticket()
    assert "background agents" not in per_ticket, (
        "Phase 6 still prescribes background agents for per-ticket /gaze — "
        "the nesting defect (PRs #1060/#1061, #1129-#1132): child sessions "
        "lack the agent connector, so the run yields no verdict"
    )
    norm = re.sub(r"\s+", " ", per_ticket)
    # A launch shape the harness honours: orchestrator-run /gaze, or a
    # detached headless non-interactive CLI session (1017's contract).
    orchestrator_run = "orchestrator" in norm and "/gaze" in norm
    detached = "headless" in norm and "non-interactive" in norm
    assert orchestrator_run or detached, (
        "Phase 6 must name an orchestrator-run /gaze or a detached headless "
        "non-interactive CLI session as the per-ticket launch shape"
    )
    # The verdict returns by artifact polling, never by spawn exit status.
    assert "artifact" in norm and "poll" in norm, (
        "Phase 6 must observe the verdict by artifact polling, not by "
        "trusting the spawn's return value"
    )
    assert "exit status" in norm, (
        "Phase 6 must state the spawn exit status is never the signal — "
        "a spawn can return success while the child never registered"
    )
    # A REROLL bump/fix commits on the PR branch, never on main mid-wave.
    assert "PR branch" in per_ticket, (
        "Phase 6 must keep a REROLL bump/fix on the PR branch — commits "
        "landing on main mid-wave are unreviewable and unmergeable"
    )
    # The detached session is pinned to the PR's worktree, and the polled
    # verdict is freshness-bound to the branch tip (round-2 review: an
    # unpinned cwd or a stale artifact would land fixes on main or accept a
    # verdict over an outdated head).
    assert "cwd pinned" in norm and "PR's worktree" in norm, (
        "Phase 6 must pin the detached gaze session's cwd to the PR's worktree"
    )
    assert "ruled_tip_sha" in norm and "branch tip" in norm, (
        "Phase 6 must accept the polled verdict only when its ruled_tip_sha "
        "matches the branch tip — a stale artifact from a prior round must "
        "not read as the current verdict"
    )


def test_phase6_launch_reason_cites_the_nesting_defect():
    """The reason line must cite the observed failures and 1017's contract."""
    norm = re.sub(r"\s+", " ", _per_ticket())
    assert "#1060" in norm and "#1132" in norm, (
        "Phase 6's reason must cite the observed nesting failures "
        "(PRs #1060/#1061, #1129-#1132)"
    )
    assert "1017" in norm, (
        "Phase 6 must cite ticket 1017's detached-seat contract for the "
        "fallback launch shape"
    )


def test_phase4_flags_planned_pr_size():
    """Phase 4 must compare each planned PR's file count with the /gaze breaker.

    The 15-file breaker fired only at gaze phase 1 on PR #1060 — after the
    wave was already executed. Phase 4 must see it while splitting is still
    cheap: WARN plus a proposed split before Phase 5 spawns executors.
    """
    phase4 = _phase4()
    norm = re.sub(r"\s+", " ", phase4)
    # A planned-PR file-count bullet, referencing the breaker (not restating
    # its mechanics) and the section that owns the threshold.
    assert "un-reviewable" in norm, (
        "Phase 4 must reference the /gaze un-reviewable breaker for planned-PR sizing"
    )
    assert "skills/gaze/SKILL.md" in norm, (
        "Phase 4 must reference the breaker where it lives — skills/gaze/SKILL.md — "
        "not restate its mechanics"
    )
    assert "WARN" in norm and "split" in norm, (
        "Phase 4 must prescribe WARN plus a proposed split for a planned PR "
        "reaching the breaker"
    )
    assert "before Phase 5" in norm, (
        "The WARN + split must be proposed before Phase 5 spawns executors — "
        "the breaker is cheap to act on at planning time only"
    )
    # The restated "(N+ files" number must equal the rules/workflow.md
    # threshold — catches restated-and-drifted (PR #1060 hit 16 files against
    # a breaker nobody in Phases 3-4 compared with).
    m = re.search(r"\((\d+)\+ files", norm)
    assert m, "Phase 4's size bullet must carry its (N+ files) number so drift is pinnable"
    workflow = (ROOT / "rules" / "workflow.md").read_text()
    discipline = workflow.split("# Ticket discipline for multi-PR work", 1)[1]
    discipline = discipline.split("# Compaction", 1)[0]
    w = re.search(r"(\d+)\+ files", discipline)
    assert w, "rules/workflow.md Ticket discipline section lost its N+ files threshold"
    assert m.group(1) == w.group(1), (
        f"Phase 4's restated threshold ({m.group(1)}+ files) drifted from "
        f"rules/workflow.md's ({w.group(1)}+ files)"
    )
    # The authoritative breaker lives in gaze phase 1 Setup — pin all three
    # statements of the threshold to one number.
    gaze = (ROOT / "skills" / "gaze" / "SKILL.md").read_text()
    setup = gaze.split("### 1. Setup", 1)[1].split("### 2–4.", 1)[0]
    breaker = re.search(r"pr_files\s*>=\s*(\d+)", setup)
    assert breaker, "gaze setup lost its pr_files un-reviewable breaker"
    assert m.group(1) == breaker.group(1), (
        f"Phase 4's restated threshold ({m.group(1)}+ files) drifted from "
        f"gaze's breaker (pr_files >= {breaker.group(1)})"
    )
