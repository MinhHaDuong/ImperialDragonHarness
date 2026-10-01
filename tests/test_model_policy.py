"""Runtime mappings resolve portable intentions independently of skill text."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("model_policy", ROOT / "scripts/model_policy.py")
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)

def test_auto_is_a_configured_tier_not_session_inheritance():
    mapping = policy.ClaudeMapping(auto_tier="haiku")
    assert mapping.model("auto") == "haiku"
    assert mapping.model("auto") != "opus"  # caller may be Opus
    with pytest.raises(ValueError):
        policy.ClaudeMapping(auto_tier="inherit").model("auto")


@pytest.mark.parametrize("level", policy.MODEL_LEVELS)
def test_runtime_resolves_every_capability_class(level):
    assert policy.ClaudeMapping().model(level) in {"haiku", "sonnet", "opus", "fable"}


@pytest.mark.parametrize("effort", policy.EFFORTS)
def test_runtime_resolves_every_effort_level(effort):
    assert policy.ClaudeMapping().effort(effort) in {"low", "medium", "high"}


def test_runtime_mapping_can_change_without_editing_skills():
    paths = sorted((ROOT / "skills").rglob("*.md"))
    before = [path.read_bytes() for path in paths]
    original = policy.ClaudeMapping()
    changed = policy.ClaudeMapping(tiers={**original.tiers, "strong": "sonnet"})
    assert original.model("strong") == "opus"
    assert changed.model("strong") == "sonnet"
    assert before == [path.read_bytes() for path in paths]


def test_invalid_intentions_fail_explicitly():
    with pytest.raises(ValueError, match="unsupported model level"):
        policy.ClaudeMapping().model("invented")
    with pytest.raises(ValueError, match="unsupported effort"):
        policy.ClaudeMapping().effort("invented")
