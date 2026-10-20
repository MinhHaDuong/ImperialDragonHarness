"""Pin yawn's closing /molt suggestion: present on the fix-now/open-ticket
path, absent on the all-ok path, outside the parsed contract headings."""

from pathlib import Path

YAWN = Path(__file__).resolve().parent.parent / "skills/yawn/SKILL.md"
SUGGESTION = (
    "Next move: `/molt` effects the fix-now entries and files tickets "
    "for the open-ticket entries."
)


def body():
    return YAWN.read_text()


def test_suggestion_line_pinned_once():
    assert body().count(SUGGESTION) == 1


def test_suggestion_follows_action_plan_and_contract_note():
    text = body()
    assert text.index("> **Contract**") < text.index(SUGGESTION)
    assert text.index("**skip**\n- {finding}") < text.index(SUGGESTION)


def test_suggestion_is_conditional_on_fix_now_or_open_ticket():
    text = body()
    rule = text[text.index(SUGGESTION) - 600 : text.index(SUGGESTION) + 600]
    assert "fix-now" in rule and "open-ticket" in rule


def test_all_ok_path_emits_no_plan_and_no_suggestion():
    text = body()
    assert "If all checks are `ok`, omit the Action plan entirely" in text
    assert "no suggestion" in text


def test_contract_headings_untouched():
    text = body()
    for heading in ("**fix-now**", "**open-ticket**", "**skip**"):
        assert text.count(f"\n{heading}\n") == 1
    assert SUGGESTION not in text.split("## Action plan")[1].split("```")[1]
