"""Roar's live wrap-up path preserves attribution after telemetry retirement."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_roar_uses_merged_fix_evidence_without_celebration_state():
    roar = (ROOT / "skills/roar/SKILL.md").read_text()
    live_steps = roar.split("## Reflect and update", 1)[1].split("## Bundle and fast track", 1)[0]
    assert "log-celebration" not in live_steps
    assert "roar-last-sha" not in live_steps
    assert "When step 2 identifies" not in live_steps
    assert "--fix-pr \"$FIX_PR\" --fix-commit \"$FIX_SHA\"" in live_steps
    assert "--merged-through \"$MERGED_THROUGH\"" in live_steps
    assert not (ROOT / "skills/roar/log-celebration").exists()
