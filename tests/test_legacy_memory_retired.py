"""Prevent reintroducing executable native/shared-store memory mutation."""
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]


def test_legacy_dream_entrypoints_are_retired():
    for name in ("commit.py", "read-index.py", "provenance.py"):
        assert not (REPO / "skills" / "dream" / name).exists(), name


def test_active_index_excludes_retired_rule_advice():
    index = (REPO / "memory" / "MEMORY.md").read_text()
    assert "feedback_rules_come_from_memory_consolidation.md" not in index
    source = REPO / "memory" / "feedback_rules_come_from_memory_consolidation.md"
    assert "RETIRED LEGACY" in source.read_text()
