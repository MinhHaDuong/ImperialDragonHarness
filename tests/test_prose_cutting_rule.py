"""The "cut before condense" technique stays reachable (ticket 0357, 0572).

Word-budget cut plans drafted by agents default to condensation — every passage
shortened in place, none questioned. The technique: run a whole-removal pass
first, then condense the remainder.

The technique lived in ``rules/prose/cutting.md``, resident in every session, until
2026-09-09: its trigger is a task, not a file, so it became the ``/cut-prose``
skill. What stays pinned is structural: the old rule body stays gone, and the
prose rule injected on every prose edit points at a skill that exists, so an agent
mid-cut meets it without being told.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "cut-prose" / "SKILL.md"
PROSE_ALL = REPO / "rules" / "prose" / "_all.md"
OLD_RULE = REPO / "rules" / "prose" / "cutting.md"

pytestmark = pytest.mark.adherence


def test_the_rule_body_did_not_come_back():
    """One home. A resident copy would be paid by every session that never cuts."""
    assert not OLD_RULE.exists(), (
        "rules/prose/cutting.md is back: the technique lives in /cut-prose "
        "(ticket 0572) — a task-triggered body has no place in the resident set"
    )


def test_prose_all_points_to_the_skill():
    assert SKILL.exists(), "the /cut-prose pointer must resolve to skills/cut-prose/SKILL.md"
    body = PROSE_ALL.read_text(encoding="utf-8")
    assert "/cut-prose" in body, (
        "rules/prose/_all.md must carry a one-line pointer to /cut-prose so the "
        "technique reaches any agent editing prose mid-cut"
    )
