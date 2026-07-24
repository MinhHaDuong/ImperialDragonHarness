"""The "cut before condense" technique is encoded in the prose layer (ticket 0357).

Word-budget cut plans drafted by agents default to condensation — every
passage shortened in place, none questioned. The technique: run a
whole-removal pass first, then condense the remainder. Three ratchets pin it
into the shared rules layer so a cut plan applies remove-whole-first by
default:

1. The full one-screen procedure lives in rules/prose/cutting.md.
2. rules/prose/_all.md (injected on every prose edit) carries a one-line
   pointer, so any agent mid-cut sees the technique without being told.
3. rules/README.md indexes the scoped file.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CUTTING = REPO / "rules" / "prose" / "cutting.md"
PROSE_ALL = REPO / "rules" / "prose" / "_all.md"
README = REPO / "rules" / "README.md"

pytestmark = pytest.mark.adherence


def test_cutting_rule_exists_with_the_technique():
    assert CUTTING.exists(), "rules/prose/cutting.md must encode the technique"
    body = CUTTING.read_text(encoding="utf-8").lower()
    # The load-bearing sequence: remove whole passages before condensing.
    assert "remove whole" in body, "cutting.md must state the remove-whole-first step"
    assert "condense" in body, "cutting.md must state the condense-the-remainder step"


def test_prose_all_points_to_cutting():
    body = PROSE_ALL.read_text(encoding="utf-8")
    assert "cutting.md" in body, (
        "rules/prose/_all.md must carry a one-line pointer to cutting.md so the "
        "technique injects on every prose edit"
    )


def test_readme_indexes_cutting():
    assert "prose/cutting.md" in README.read_text(encoding="utf-8"), (
        "rules/README.md must index prose/cutting.md — the index is the single "
        "source of truth on when each rule file applies"
    )
