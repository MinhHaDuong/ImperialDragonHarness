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


def test_bundle_exit_needs_pushed_tip_and_armed_auto_merge():
    assert "Wait for confirmed integration before cleaning up" not in ROAR
    assert "auto-merge armed" in ROAR, "step 9b must accept an armed wrap-up PR"
    assert "matches its pushed upstream" in ROAR, (
        "step 9b must require the local tip to equal the pushed branch"
    )


def test_task_branch_still_needs_ancestry():
    assert "merge-base --is-ancestor HEAD origin/main" in ROAR
