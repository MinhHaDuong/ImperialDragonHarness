"""Budgets for every resident channel, not just ``rules/``.

``test_rules_resident_budget.py`` capped the auto-loaded rule bodies. Measured
against ``/context`` on 2026-09-10, that was 54% of what a session actually
carried: ``CLAUDE.md`` and its ``@`` imports, the file the SessionStart hook
prints, the project memory index, and the resident frontmatter of every skill
and subagent were all outside it. A ratchet on the watched half is an
invitation for the growth to happen in the other half.

Each budget is set at the measured value plus thin headroom, deliberately:
repair sequences before a stricter rule, so this lands green and every later
character is an argued one. Lowering a budget is the deliverable of a trimming
pass; raising one is a decision to pay it in every session, in every project,
forever — argue it in a ticket.

The positive control matters more than the budgets. Every count here comes
from a glob, and a glob that stops matching reports zero, which passes every
budget. ``test_every_channel_is_populated`` is what tells a real all-clear
from a census that could not look.
"""

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO / "scripts"))

import resident_census as rc  # noqa: E402

# Measured 2026-09-10 (chars, the exact unit — the token column of the census
# is derived). Headroom is a sentence, not a section.
BUDGETS = {
    "rules": 36000,  # owned by test_rules_resident_budget.py, mirrored here
    "import": 10500,  # CLAUDE.md + tickets/AGENTS.md + RTK.md
    # Both lowered 2026-09-10 by the title-only index pass: the index line is a
    # title and a link, the trailing hook having been a third copy of a sentence
    # the body already carries as `name:` and `description:`. 47 indexes went
    # 198 636 -> 111 021 chars; the largest 26 531 -> 14 061, and the harness
    # index 950 -> 367. Lowering these is the deliverable of that pass.
    "hook": 500,  # memory/MEMORY.md, printed by scripts/on-start.sh
    "memory": 14500,  # the largest per-project index; only one is resident
    "skills": 7000,  # name + description of every SKILL.md
    "agents": 800,  # name + description of every agents/*.md
}

# A floor per channel: enough to fail loudly when a glob silently stops
# matching, low enough never to fire on honest trimming.
FLOORS = {
    "rules": 10000,
    "import": 500,
    "hook": 100,
    "memory": 1000,
    "skills": 1000,
    "agents": 100,
}


@pytest.fixture(scope="module")
def entries() -> list[rc.Entry]:
    return rc.census(REPO)


def test_every_channel_is_populated(entries):
    """The positive control: a zero here means the census went blind.

    Every other assertion in this file is a ceiling, and a ceiling is passed
    by an empty result. Without this, deleting the ``skills/`` glob would read
    as a 6000-character saving.
    """
    totals = rc.channel_chars(entries)
    for channel, floor in FLOORS.items():
        assert totals[channel] >= floor, (
            f"channel '{channel}' measured {totals[channel]} chars, under the "
            f"{floor} floor — either it was trimmed far beyond anything this "
            "repo has done, or its glob in scripts/resident_census.py stopped "
            "matching and every budget below is passing on an empty count"
        )


def test_channel_budgets(entries):
    totals = rc.channel_chars(entries)
    over = {c: totals[c] for c in BUDGETS if totals[c] > BUDGETS[c]}
    detail = "; ".join(
        f"{c} is {totals[c]} chars (> {BUDGETS[c]}), "
        f"~{round(totals[c] / rc.CHARS_PER_TOKEN)} tokens in every session"
        for c in over
    )
    assert not over, (
        f"{detail} — trim a body, scope a rule with `paths:` frontmatter, or "
        "move a procedure to the skill that runs it; raising a budget is a "
        "ticket, not an edit"
    )


def test_no_project_memory_index_exceeds_the_budget(entries):
    """Each index is resident in its own project's sessions, so cap each one."""
    budget = BUDGETS["memory"]
    over = [e for e in entries if e.channel == "memory" and e.chars > budget]
    detail = "; ".join(f"{e.path} is {e.chars} chars (> {budget})" for e in over)
    assert not over, (
        f"{detail} — /dream promotes into these indexes and nothing prunes "
        "them; distil entries into rules, or delete them"
    )


def test_session_total_is_the_sum_of_the_channels(entries):
    """One session pays every channel once, with a single memory index.

    Guards the modelling, not the size: summing all 40-odd project indexes
    would describe a session nobody runs, and quietly inflate every report
    built on this module.
    """
    totals = rc.channel_chars(entries)
    assert rc.session_chars(entries) == sum(totals.values()), (
        "session_chars and channel_chars disagree — one of them stopped "
        "covering a channel the other still counts"
    )
    memory = [e.chars for e in entries if e.channel == "memory"]
    assert totals["memory"] == max(memory), (
        f"the memory channel reports {totals['memory']} chars where the "
        f"largest index is {max(memory)}: a session is resident in exactly "
        "one project's index, so anything else inflates every report"
    )
    assert totals["memory"] < sum(memory), (
        "the memory channel is reporting a sum across all projects, not the "
        "largest index — that describes a session nobody runs"
    )


def test_every_channel_has_a_budget_and_a_floor():
    """A channel added to the census without a budget is an unwatched channel."""
    assert set(rc.CHANNELS) == set(BUDGETS) == set(FLOORS)
