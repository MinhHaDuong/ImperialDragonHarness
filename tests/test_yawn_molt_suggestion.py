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
    text = " ".join(body().split())
    assert (
        "only when the Action plan holds at least one `fix-now` "
        "or `open-ticket` entry (a `skip`-only plan gets none)"
    ) in text


def test_all_ok_path_emits_no_plan_and_no_suggestion():
    text = body()
    assert "If all checks are `ok`, omit the Action plan entirely" in text
    assert "An all-ok run emits no Action plan and no suggestion." in text


def test_contract_headings_untouched():
    text = body()
    for heading in ("**fix-now**", "**open-ticket**", "**skip**"):
        assert text.count(f"\n{heading}\n") == 1
    # The suggestion sits in its own fence, after the plan format block closes.
    plan = text.index("```\n## Action plan")
    plan_close = text.index("\n```\n", plan + 4) + len("\n```\n")
    pos = text.index(SUGGESTION)
    assert plan_close < pos
    between = text[plan_close:pos]
    assert between.count("```") == 1  # only the suggestion's own opening fence
    assert between.rstrip().endswith("```")
