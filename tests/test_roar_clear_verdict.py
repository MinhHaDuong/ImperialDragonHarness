"""Roar step 11 ends with a /clear verdict whose "pending" covers every
pending item roar reports, while an armed, read-back bundle does not block it
(ticket 1083, /gaze round 1)."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
ROAR = re.sub(r"\s+", " ", (REPO / "skills" / "roar" / "SKILL.md").read_text())


def _step11() -> str:
    return ROAR.split("11. **Report**", 1)[1].split("Note: STATE.md", 1)[0]


def test_verdict_is_clear_never_compact():
    s = _step11()
    assert "safe to `/clear`" in s and "never `/compact`" in s


def test_pending_includes_capture_and_kept_work():
    s = _step11()
    for item in ("pending capture", "capture branch", "kept worktree", "close claim"):
        assert item in s, item


def test_armed_bundle_does_not_block_clear():
    s = _step11()
    assert "auto-merge" in s and "does not block" in s


def test_no_stale_step3_sweep_reference():
    assert "step-3 sweep" not in ROAR
    doc = (REPO / "docs" / "2026-10-06-attribution-integration.md").read_text()
    assert "Roar step 3 invokes" not in doc
