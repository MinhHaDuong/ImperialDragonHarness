"""Phase 0: the Claude dry-run mapping preserves every current model pin."""

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("model_policy", ROOT / "scripts/model_policy.py")
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)

PIN = re.compile(r"\bmodel\s*[:=]\s*['\"`]?\b(sonnet|opus|haiku|fable)\b", re.I)

# All present skill-body launch pins, in source order. A new, removed, or changed
# pin must be reviewed here. The semantic level is independent of the live text.
BODY_LEVELS = {
    "gaze": ("standard", "standard", "strong"),
    "hunt": ("strong",),
    "raid": ("standard", "cheap", "standard", "strong", "standard",
             "standard", "standard", "cheap", "standard", "strong", "standard"),
    "release": ("standard",),
    "review-pr": ("standard",),
    "review-pr-prose": ("standard", "standard"),
    "verify-adherence": ("standard",),
}

# Frontmatter controls the skill or fork itself, not its spawned children.
FRONTMATTER_MODELS = {
    "gaze": "sonnet", "healthcheck": "sonnet", "molt": "sonnet",
    "raid": "claude-sonnet-5", "review-pr": "sonnet",
    "review-pr-prose": "sonnet", "trace-doctor": "sonnet",
    "verify-adherence": "sonnet", "verify-gate": "sonnet",
}
FRONTMATTER_EFFORTS = {
    "healthcheck": ("economy", "low"),
    "molt": ("economy", "low"),
    "raid": ("intensive", "high"),
    "trace-doctor": ("standard", "medium"),
}


def _parts(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    return (parts[1], parts[2]) if text.startswith("---") and len(parts) == 3 else ("", text)


def _assert_body_mapping(mapping):
    actual = {}
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        pins = PIN.findall(_parts(path)[1])
        if pins:
            actual[path.parent.name] = pins
    assert set(actual) == set(BODY_LEVELS)
    for skill, levels in BODY_LEVELS.items():
        assert actual[skill] == [mapping.model(level) for level in levels], skill


def test_live_skill_body_launch_pins_match_semantic_mapping():
    _assert_body_mapping(policy.ClaudeMapping())


def test_live_skill_frontmatter_models_and_efforts():
    mapping = policy.ClaudeMapping()
    models, efforts = {}, {}
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        frontmatter, _ = _parts(path)
        model = re.search(r"^model:\s*(\S+)\s*$", frontmatter, re.M)
        effort = re.search(r"^effort:\s*(\S+)\s*$", frontmatter, re.M)
        if model:
            models[path.parent.name] = model.group(1)
        if effort:
            efforts[path.parent.name] = effort.group(1)
    assert models == FRONTMATTER_MODELS
    assert set(efforts) == set(FRONTMATTER_EFFORTS)
    for skill, (level, concrete) in FRONTMATTER_EFFORTS.items():
        assert mapping.effort(level) == efforts[skill] == concrete
    assert models["raid"] == f"claude-{mapping.model('standard')}-5"


def test_team_lead_currently_inherits_both_controls():
    frontmatter, _ = _parts(ROOT / "agents/team-lead.md")
    assert not re.search(r"^(model|effort):", frontmatter, re.M)


def test_documented_session_effort_at_unpinned_launches():
    mapping = policy.ClaudeMapping()
    raid = (ROOT / "skills/raid/SKILL.md").read_text(encoding="utf-8")
    hunt = (ROOT / "skills/hunt/SKILL.md").read_text(encoding="utf-8")
    assert "session effort (run the raid at `high`" in raid
    assert "session effort, run at `high`" in hunt
    assert mapping.effort("intensive") == "high"


def test_auto_is_a_configured_tier_not_session_inheritance():
    mapping = policy.ClaudeMapping(auto_tier="haiku")
    assert mapping.model("auto") == "haiku"
    assert mapping.model("auto") != "opus"  # caller may be Opus
    with pytest.raises(ValueError):
        policy.ClaudeMapping(auto_tier="inherit").model("auto")


def test_mapping_change_makes_baseline_red():
    changed = policy.ClaudeMapping(tiers={**policy.ClaudeMapping().tiers, "strong": "sonnet"})
    with pytest.raises(AssertionError, match="hunt|gaze|raid"):
        _assert_body_mapping(changed)
