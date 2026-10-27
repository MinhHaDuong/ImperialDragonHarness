"""The testing expert is a consultation the author calls: pin that, and its integration.

The author's rule: agents are never told unconditionally to use a testing
shortcut, and the testing expert is never started automatically. These tests
hold both ends of that: the instruction is gone from the places that carried
it, the skill cannot be invoked by a model, and the wrap-up only suggests it.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import skill_frontmatter as sf  # noqa: E402

SKILL = REPO / "skills" / "test-doctor" / "SKILL.md"


def test_the_expert_cannot_be_invoked_by_a_model():
    meta = sf.load(SKILL)
    assert meta["disable-model-invocation"] is True
    assert meta["user-invocable"] is True
    assert meta["name"] == "test-doctor"


def test_the_hoard_step_does_not_end_the_wrap_up_before_the_testing_step():
    lair = (REPO / "skills" / "lair" / "SKILL.md").read_text()
    hoard = lair.split("**Suggest a hoard", 1)[1].split("**Suggest a testing", 1)[0]
    assert "Then\n    finish" not in hoard and "Then finish" not in hoard


def test_only_hunt_and_the_suggesters_mention_the_expert():
    """Nothing else may grow a path to the expert: only hunt, the wrap-up and
    the trace survey may name it.

    Whether they name it is their wording, not pinned here.
    """
    mentioning = {
        path.parent.name
        for path in (REPO / "skills").glob("*/SKILL.md")
        if "`/test-doctor`" in path.read_text()
    }
    assert mentioning <= {"hunt", "lair", "trace-doctor"}


def test_the_visit_covers_history_evidence_diagnosis_remedy_and_verification():
    body = SKILL.read_text()
    for needed in ("Complaint", "Chart", "Examination", "Differential", "Confirm",
                   "Intervene", "Verify", "revisit"):
        assert needed in body, f"the visit lost its {needed!r} step"
    for evidence_tool in ("gate_traces.py", "gate_profile.py"):
        assert evidence_tool in body
        assert (REPO / "scripts" / evidence_tool).is_file()


def test_the_skill_keeps_project_names_out_of_the_harness():
    text = "\n".join(p.read_text() for p in (SKILL.parent).rglob("*.md"))
    assert not re.search(r"climate|jetp|zotero", text, re.I)
