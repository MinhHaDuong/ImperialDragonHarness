"""Budgets for every resident channel, not just ``rules/``.

``test_rules_resident_budget.py`` capped the auto-loaded rule bodies. Measured
against ``/context`` on 2026-09-10, that was 54% of what a session actually
carried: ``AGENTS.md`` and its ``@`` imports, the project memory index, and
the resident frontmatter of every skill and subagent were all outside it. A ratchet on the watched half is an
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

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO / "scripts"))

import resident_census as rc  # noqa: E402
from child_env import child_env  # noqa: E402
from tracked_tree import tracked_checkout  # noqa: E402

# Measured 2026-09-10 (chars, the exact unit — the token column of the census
# is derived). Headroom is a sentence, not a section.
BUDGETS = {
    "rules": 36000,  # owned by test_rules_resident_budget.py, mirrored here
    # Lowered 2026-09-16 (ticket 0906): tickets/AGENTS.md was a local fork of
    # the erg-shipped asset, 8005 chars where the asset is 2356. Restored
    # byte-for-byte, the chain is 4041. At 10500 this gate could no longer
    # fail on anything the chain could plausibly do.
    # Raised 2026-10-02 (ticket 0920): the v8 pilot merges the 0911 reading
    # section into AGENTS.md, as the adopted convention requires. The section
    # was trimmed against this gate; the abridgement is stated in
    # conception/memory-v8/pilot.md, with the template as the reference, so the
    # budget moves to the measured value plus thin headroom instead.
    "import": 4500,  # canonical harness instructions and supporting references
    # Lowered 2026-09-10 by the title-only index pass: the index line is a
    # title and a link, the trailing hook having been a third copy of a sentence
    # the body already carries as `name:` and `description:`. 47 indexes went
    # 198 636 -> 111 021 chars; the largest 26 531 -> 14 061, and the harness
    # index 950 -> 367. Lowering these is the deliverable of that pass.
    # Raised 2026-10-02 (ticket 0920): the v8 pilot index links the real
    # topic, journal and reference surface, so it can no longer fit the
    # legacy 500-char stub.
    "memory": 14500,  # the largest per-project index; only one is resident
    # Lowered 2026-10-20 (ticket 1140): coaching became a script and three
    # step-only skills (typography-finish, bib-merge, related-work-note-validate)
    # became runbooks; with the lifecycle trim of 1132, 6993 -> 6120 chars
    # measured. The budget is that plus thin headroom.
    "skills": 6300,  # tracked cards; local cards are supplemental (1091); +100 for routing hints kept out of the catalog (2026-10-28)
    "agents": 800,  # name + description of every agents/*.md
}

# A floor per channel: enough to fail loudly when a glob silently stops
# matching, low enough never to fire on honest trimming.
FLOORS = {
    "rules": 10000,
    "import": 500,
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


@pytest.fixture
def indexed_tree(tmp_path):
    """The tracked-tree helper omits .git; index this contained copy explicitly."""
    root = tmp_path / "harness"
    shutil.copytree(tracked_checkout(), root, symlinks=True)
    for args in (("init", "-q"), ("add", ".")):
        subprocess.run(["git", "-C", str(root), *args], check=True,
                       capture_output=True, env=child_env())
    return root


def plant_skill(root, name, chars, *, linked):
    target = root.parent / name if linked else root / "skills" / name
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {'x' * (chars - len(name))}\n---\n",
        encoding="utf-8",
    )
    if linked:
        (root / "skills" / name).symlink_to(target, target_is_directory=True)


def test_local_overlay_cost_is_visible_without_breaking_tracked_budget(indexed_tree):
    clean = rc.census(indexed_tree)
    clean_total = rc.channel_chars(clean)["skills"]
    assert clean_total <= BUDGETS["skills"]
    # Costs measured from the three live cards at the ticket's wave base.
    for name, chars in (("email", 275), ("infrastructure", 275), ("directory", 282)):
        plant_skill(indexed_tree, name, chars, linked=True)
    observed = rc.census(indexed_tree)
    totals = rc.channel_chars(observed)
    assert totals["skills"] == clean_total
    assert "Local skill links: absent" in rc._render(clean, False)
    assert totals["skills-local"] == 832
    # Positive control: the old combined-budget interpretation still overflows.
    assert totals["skills"] + totals["skills-local"] > BUDGETS["skills"]
    assert rc.session_chars(observed) == rc.session_chars(clean) + 832
    assert rc.session_chars(observed) == sum(totals.values())
    for detail in (False, True):
        report = rc._render(observed, detail)
        assert "Local skill links: present" in report
        assert "832" in report
        for name in ("email", "infrastructure", "directory"):
            assert f"skills/{name}/SKILL.md" in report
        assert "tracked" in report


@pytest.mark.integration
def test_git_index_handles_tracked_directory_links_and_untracked_directories(indexed_tree):
    plant_skill(indexed_tree, "tracked-link", 71, linked=True)
    subprocess.run(["git", "-C", str(indexed_tree), "add", "skills/tracked-link"],
                   check=True, capture_output=True, env=child_env())
    plant_skill(indexed_tree, "local-directory", 53, linked=False)
    rows = {e.path: e for e in rc.skill_entries(indexed_tree)}
    assert rows["skills/tracked-link/SKILL.md"].channel == "skills"
    assert rows["skills/tracked-link/SKILL.md"].tracking == "tracked"
    assert rows["skills/local-directory/SKILL.md"].channel == "skills-local"
    assert rows["skills/local-directory/SKILL.md"].tracking == "untracked"


def test_missing_git_metadata_keeps_full_observed_cost_and_reports_unknown(tmp_path):
    # No .git: never infer "untracked" from a failed Git inspection.
    plant_skill(tmp_path, "unknown", 97, linked=False)
    rows = rc.skill_entries(tmp_path)
    assert rc.channel_chars(rows)["skills"] == 97
    assert rows[0].tracking == "unknown"
    assert rc.session_chars(rows) == 97
    report = rc._render(rows, False)
    assert "unknown" in report
    assert "Local skill links: unknown" in report
    assert "skills/unknown/SKILL.md" in report
