"""Roar's live wrap-up path preserves attribution after telemetry retirement."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_roar_uses_merged_fix_evidence_without_celebration_state():
    # The old live path moved out of SKILL.md into runbooks; the negative
    # assertions hold on every file that now carries or points at it.
    live_steps = (ROOT / "skills/roar/runbooks/sweep.md").read_text()
    paths = [ROOT / "skills/roar/SKILL.md", *sorted((ROOT / "skills/roar/runbooks").glob("*.md")),
             *sorted((ROOT / "skills/roar/references").glob("*.md"))]
    for path in paths:
        text = path.read_text()
        assert "log-celebration" not in text, path
        assert "roar-last-sha" not in text, path
        assert "When step 2 identifies" not in text, path
    assert "--fix-pr \"$FIX_PR\" --fix-commit \"$FIX_SHA\"" in live_steps
    assert "--merged-through \"$MERGED_THROUGH\"" in live_steps
    assert not (ROOT / "skills/roar/log-celebration").exists()


def test_roar_captures_typed_masks_with_evidence_and_explicit_limits():
    roar = (ROOT / "skills/roar/runbooks/capture.md").read_text()
    assert "model-state=runtime-masked · model-evidence=" in roar
    assert "whole PR game is excluded" in roar
    assert "Never use this state to cover unrelated missing facts" in roar
