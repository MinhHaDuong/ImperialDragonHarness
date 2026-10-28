"""Roar may exit its wrap-up worktree once the bundle is pushed and armed.

Waiting for the wrap-up PR's CI and auto-merge kept roar from finishing
(author decision, 2026-10-09). The pushed branch and open auto-merge PR are
the durable copy; the task branch still needs the merged-ancestry check.

Since ticket 1098 these checks run in close-and-clean.sh's exit-check phase,
exercised behaviourally in tests/test_roar_close_and_clean.sh; these ratchets
keep the script's probes and the skill's ownership scope in place.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
ROAR = re.sub(r"\s+", " ", (REPO / "skills" / "roar" / "SKILL.md").read_text())
SCRIPT = (REPO / "skills" / "roar" / "close-and-clean.sh").read_text()


def _function(name: str) -> str:
    return SCRIPT.split(f"{name}() {{", 1)[1].split("\n}\n", 1)[0]


def _step9() -> str:
    return ROAR.split("9. **Exit worktree**", 1)[1].split("10. **Clean only", 1)[0]


def test_bundle_exit_needs_pushed_tip_and_armed_auto_merge():
    assert "Wait for confirmed integration before cleaning up" not in ROAR
    probe = _function("bundle_armed")
    assert "git ls-remote" in probe, "the pushed tip is read from the remote, never a stale @{u}"
    assert "forge_read_back" in probe and '"OPEN "*" queued"' in probe, \
        "armed must be read back from the forge adapter, not asserted"
    assert "gh pr view" not in SCRIPT, "the merge request is read through scripts/forge.py (ticket 1318)"


def test_bundle_exception_excludes_task_and_reused_branches():
    assert "`roar-*` wrap-up branch this run created" in _step9()
    assert "never the task branch or a reused branch" in _step9()
    assert '"$BUNDLE" == roar-*' in _function("exit_check")


def test_failed_bundle_is_surfaced_by_roar_not_molt():
    step9 = _step9()
    assert "in step 11" in step9 and "does not block" in step9
    # No later roar re-checks a bundle (ticket 1156 review): the text must not
    # promise one, and a gated bundle stays pending until it reads MERGED.
    assert "a later roar reports" not in step9
    assert "nothing re-checks" in step9 and "until it reads MERGED" in step9


def test_task_branch_still_needs_ancestry():
    assert 'merge-base --is-ancestor "$head" "$base_tip"' in _function("exit_check")


def test_gated_bundle_exit_reads_the_gate_record_and_fails_closed():
    probe = _function("bundle_armed")
    assert 'merge-gate.py' in probe and '"$gate" enabled' in probe and '"$gate" check' in probe
    assert "COULD-NOT-LOOK cannot read the base's merge-gate declaration" in probe
