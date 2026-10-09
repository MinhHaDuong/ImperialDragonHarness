"""Roar may exit its wrap-up worktree once the bundle is pushed and armed.

Waiting for the wrap-up PR's CI and auto-merge kept roar from finishing
(author decision, 2026-10-09). The pushed branch and open auto-merge PR are
the durable copy; the task branch still needs the merged-ancestry check.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
ROAR = re.sub(r"\s+", " ", (REPO / "skills" / "roar" / "SKILL.md").read_text())


def _bundle_exception() -> str:
    return ROAR.split("**Bundle exception.**", 1)[1].split("If fetch or verification", 1)[0]


def test_bundle_exit_needs_pushed_tip_and_armed_auto_merge():
    assert "Wait for confirmed integration before cleaning up" not in ROAR
    rule = _bundle_exception()
    assert "fresh fetch" in rule and "git rev-parse HEAD @{u}" in rule, (
        "the pushed-tip probe must follow a fetch, or @{u} can be stale"
    )
    assert "auto-merge armed" in rule and "autoMergeRequest" in rule, (
        "armed must be read back from the forge, not asserted"
    )


def test_bundle_exception_excludes_task_and_reused_branches():
    rule = _bundle_exception()
    assert "`roar-*` wrap-up branch this run created" in rule
    assert "never the task branch" in rule and "never a reused branch" in rule


def test_failed_bundle_is_surfaced_by_roar_not_molt():
    rule = _bundle_exception()
    assert "/molt" not in rule, "molt does not report open merge requests"
    assert "pending integration in step 11" in rule
    assert "step 10" in rule


def test_task_branch_still_needs_ancestry():
    assert "merge-base --is-ancestor HEAD origin/main" in ROAR
