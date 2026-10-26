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

SKILL = REPO / "skills" / "pulse" / "SKILL.md"


def test_the_expert_cannot_be_invoked_by_a_model():
    meta = sf.load(SKILL)
    assert meta["disable-model-invocation"] is True
    assert meta["user-invocable"] is True
    assert meta["name"] == "pulse"


def test_the_wrap_up_suggests_the_expert_and_never_runs_it():
    lair = (REPO / "skills" / "lair" / "SKILL.md").read_text()
    step = lair.split("13. **Suggest a testing consultation", 1)[1]
    assert "pulse_traces.py" in step and "survey" in step
    assert "never run automatically" in step
    assert "pulse: not checked" in step, "silence must not read as an all-clear"


def test_the_hoard_step_does_not_end_the_wrap_up_before_the_pulse_step():
    lair = (REPO / "skills" / "lair" / "SKILL.md").read_text()
    hoard = lair.split("12. **Suggest a hoard", 1)[1].split("13. **Suggest a testing", 1)[0]
    assert "Then\n    finish" not in hoard and "Then finish" not in hoard


def test_only_hunt_and_the_wrap_up_mention_the_expert():
    """Nothing else may grow a path to the expert: only hunt and the wrap-up may name it.

    Whether hunt names it is hunt's wording, not pinned here; the wrap-up must.
    """
    mentioning = {
        path.parent.name
        for path in (REPO / "skills").glob("*/SKILL.md")
        if "`/pulse`" in path.read_text()
    }
    assert "lair" in mentioning and mentioning <= {"hunt", "lair"}


def test_the_visit_covers_history_evidence_diagnosis_remedy_and_verification():
    body = SKILL.read_text()
    for needed in ("Complaint", "Chart", "Examination", "Differential", "Confirm",
                   "Intervene", "Verify", "revisit"):
        assert needed in body, f"the visit lost its {needed!r} step"
    for evidence_tool in ("pulse_traces.py", "pulse_profile.py"):
        assert evidence_tool in body
        assert (REPO / "scripts" / evidence_tool).is_file()


def test_the_skill_keeps_project_names_out_of_the_harness():
    text = "\n".join(p.read_text() for p in (SKILL.parent).rglob("*.md"))
    assert not re.search(r"climate|jetp|zotero", text, re.I)
