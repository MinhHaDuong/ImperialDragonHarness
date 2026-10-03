"""Agent profile subsystem pins (ticket 0938, wave 1).

The design (docs/2026-10-03-agent-profile-subsystem-design.md) replaces
inline fork roles with thin runtime shells whose body is a pointer to a
harness-side contract at ``profiles/<name>/PROFILE.md``. No machinery
validates the pointer; these doc-pin tests are the enforcement surface the
design names: every roster shell exists with the census-checked card, points
at its contract, declares a model from the short enum, and every contract
exists and lists its baseline rules. They fail while the roster is absent —
the wave 1 red step.

The roster and its census arithmetic come from
docs/2026-10-03-agent-role-inventory.md ("Proposed shell roster"): 323 new
characters, agents channel 438 -> 761 of 800, no budget raise.
"""

import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO / "scripts"))

import resident_census as rc  # noqa: E402
from model_policy import MODEL_LEVELS  # noqa: E402

# name -> (description, model) exactly as the inventory roster registers them.
# The census arithmetic (323 chars, 761/800) depends on these strings.
ROSTER = {
    "coder": (
        "Executes a ticket contract in a worktree; branch, PR, evidence.",
        "strong",
    ),
    "code-reviewer": (
        "Code-review seat; perspective arrives in the prompt.",
        "standard",
    ),
    "prose-reviewer": (
        "Prose-panel seat; role and rulebook arrive in the prompt.",
        "standard",
    ),
    "gate-seat": (
        "Read-only verify-gate seat; verdict only.",
        "standard",
    ),
    "adherence-seat": (
        "Read-only verify-adherence seat; verdict artifact only.",
        "standard",
    ),
}

AGENTS_CHANNEL_BUDGET = 800  # tests/test_resident_census.py owns the budget


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{path}: missing frontmatter"
    block = text.split("---", 2)[1]
    fields = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def test_every_roster_shell_exists_with_the_census_card():
    for name, (description, _model) in ROSTER.items():
        path = REPO / "agents" / f"{name}.md"
        assert path.is_file(), f"agents/{name}.md is absent — roster not landed"
        fm = _frontmatter(path)
        assert fm.get("name") == name, f"{path}: frontmatter name"
        assert fm.get("description") == description, (
            f"{path}: description must match the inventory roster verbatim "
            "(the census arithmetic depends on it)"
        )


def test_every_roster_shell_declares_a_model_from_the_short_enum():
    for name, (_description, model) in ROSTER.items():
        path = REPO / "agents" / f"{name}.md"
        fm = _frontmatter(path)
        declared = fm.get("model")
        assert declared in MODEL_LEVELS, (
            f"{path}: model '{declared}' outside the short enum {MODEL_LEVELS}"
        )
        assert declared == model, (
            f"{path}: model is '{declared}', roster pins '{model}'"
        )


def test_every_roster_shell_body_points_at_its_contract():
    for name in ROSTER:
        body = (REPO / "agents" / f"{name}.md").read_text(encoding="utf-8")
        body = " ".join(body.split())
        assert "Step 0" in body, f"agents/{name}.md: no step-0 pointer"
        assert f"profiles/{name}/PROFILE.md" in body, (
            f"agents/{name}.md: pointer must name profiles/{name}/PROFILE.md"
        )
        assert "say so in your first output line" in body, (
            f"agents/{name}.md: pointer must report resolution failure, "
            "not proceed ungrounded"
        )
        assert "Never guess a different root" in body, (
            f"agents/{name}.md: pointer must ban fallback root search "
            "(a stale sibling install is never silently picked up)"
        )


def test_every_contract_exists_and_lists_its_baseline_rules():
    """guards.md is the wave-0 baseline every bare-context role must load."""
    for name in ROSTER:
        path = REPO / "profiles" / name / "PROFILE.md"
        assert path.is_file(), f"profiles/{name}/PROFILE.md is absent"
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "Rules:" in text, f"{path}: no Rules section"
        assert "rules/guards.md" in text, (
            f"{path}: Rules must list the baseline rules/guards.md"
        )


def test_seat_contracts_pin_reviewer_discipline():
    """Seats that judge work load the git discipline and the
    delegation/decorrelation sections — the bare-context trap the design
    names (reviewers without git discipline or MOE posture)."""
    seats = {
        "code-reviewer": ("rules/workflow.md", "rules/git.md"),
        "prose-reviewer": ("rules/workflow.md", "rules/git.md"),
        "gate-seat": ("rules/workflow.md", "rules/git.md"),
        "adherence-seat": ("rules/workflow.md", "rules/git.md"),
    }
    for name, rules in seats.items():
        text = " ".join(
            (REPO / "profiles" / name / "PROFILE.md").read_text(encoding="utf-8").split()
        )
        for rule in rules:
            assert rule in text, f"profiles/{name}/PROFILE.md: must list {rule}"


def test_coder_contract_pins_git_discipline_and_hunt_reference():
    text = " ".join(
        (REPO / "profiles" / "coder" / "PROFILE.md").read_text(encoding="utf-8").split()
    )
    assert "rules/git.md" in text
    assert "skills/hunt/SKILL.md" in text


def test_contract_skills_sections_name_the_invokable_contracts():
    skills_of = {
        "coder": "skills/hunt/SKILL.md",
        "code-reviewer": "skills/review-pr/SKILL.md",
        "prose-reviewer": "skills/review-pr-prose/SKILL.md",
        "gate-seat": "skills/verify-gate/SKILL.md",
        "adherence-seat": "skills/verify-adherence/SKILL.md",
    }
    for name, skill_path in skills_of.items():
        text = " ".join(
            (REPO / "profiles" / name / "PROFILE.md").read_text(encoding="utf-8").split()
        )
        assert "Skills:" in text, f"profiles/{name}/PROFILE.md: no Skills section"
        assert skill_path in text, (
            f"profiles/{name}/PROFILE.md: Skills must name {skill_path}"
        )


def test_agents_channel_stays_within_budget():
    """The roster must land at the projected 761/800 — the census arithmetic
    is pre-checked in the inventory; a recount that differs means the
    descriptions drifted from the roster."""
    entries = rc.agent_entries(REPO)
    total = sum(e.chars for e in entries)
    assert total <= AGENTS_CHANNEL_BUDGET, (
        f"agents channel is {total} chars (> {AGENTS_CHANNEL_BUDGET}) — trim a "
        "description or argue a budget raise in a ticket, never by edit"
    )
    for name, (description, _model) in ROSTER.items():
        entry = next(
            (e for e in entries if e.path == f"agents/{name}.md"), None
        )
        assert entry is not None, (
            f"agents/{name}.md is not counted by the census — missing, or "
            "not where agent_entries globs"
        )
        assert entry.chars == len(name) + len(description), (
            f"agents/{name}.md census card is {entry.chars} chars but the "
            f"roster declares {len(name) + len(description)} — the shell's "
            "name or description drifted from the roster"
        )


def test_no_contract_declares_a_model_section():
    """Design v2: frontmatter is authoritative for launch parameters; a
    Model: section in a contract would be a second truth (ticket 0938)."""
    for name in ROSTER:
        text = (REPO / "profiles" / name / "PROFILE.md").read_text()
        assert not re.search(r"^Model:", text, re.MULTILINE), (
            f"profiles/{name}/PROFILE.md declares a Model: section — "
            "frontmatter is authoritative; remove the section"
        )


def test_no_two_agent_shells_share_a_description():
    descriptions = {}
    for path in sorted((REPO / "agents").glob("*.md")):
        fm = _frontmatter(path)
        description = fm.get("description", "")
        assert description, f"{path}: empty description"
        assert description not in descriptions, (
            f"{path}: description duplicates {descriptions[description]} — "
            "a runtime cannot route two shells with the same card"
        )
        descriptions[description] = path


# Wave 2 pilot (ticket 0938 Actions step 4): the review-pr five-perspective
# launch section names the code-reviewer profile instead of restating the
# seat rails per launch. The detached-seat substitution section keeps its
# inline embedding by design (inventory) and stays outside these pins.
REVIEW_PR = REPO / "skills" / "review-pr" / "SKILL.md"


def test_review_pr_launch_names_the_code_reviewer_profile():
    """The parallel-spawn block launches the named profile whose contract
    carries the seat rails; perspective and materials ride in the prompt."""
    review = REVIEW_PR.read_text(encoding="utf-8")
    launch = " ".join(
        review.split("Spin multiple agents", 1)[1]
        .split("### Detached-seat substitution", 1)[0]
        .split()
    )
    assert "the code-reviewer profile" in launch, (
        "the review-pr launch block must name the code-reviewer profile it "
        "launches (agents/code-reviewer.md)"
    )
    assert "agents/code-reviewer.md" in launch
    assert "profiles/code-reviewer/PROFILE.md" in launch, (
        "the launch block must point at the contract that owns the seat rails"
    )
    assert "perspective" in launch and "anchor" in launch, (
        "perspective and anchor materials stay in the launch prompt"
    )


def test_review_pr_no_longer_restates_the_seat_rails():
    """The seat rails are the contract's, not the skill body's. The pinned
    phrases are the removed 'Each agent runs' restatement and the launch
    sentence's discipline re-embedding (whitespace-normalized: both span
    line breaks in the removed text)."""
    flat = " ".join(REVIEW_PR.read_text(encoding="utf-8").split())
    assert "Evaluate from its assigned perspective" not in flat
    assert "Decide a verdict: **approve**, **comment**, or **request-changes**" not in flat
    assert "the `.part`-then-rename discipline" not in flat


def test_code_reviewer_contract_carries_the_report_format():
    """The rails removed from the skill body must live in the contract:
    confidence per finding, the verdict enum, and the verifiable/consider/
    nofollow minor-finding tags with verifiable's evidence requirement."""
    text = " ".join(
        (REPO / "profiles" / "code-reviewer" / "PROFILE.md")
        .read_text(encoding="utf-8")
        .split()
    )
    assert "confidence" in text.lower()
    for verdict in ("approve", "comment", "request-changes"):
        assert verdict in text, f"contract verdict enum missing {verdict}"
    for tag in ("verifiable:", "consider:", "nofollow:"):
        assert tag in text, f"contract minor-finding tag {tag} missing"
    assert "failing assertion" in text or "test_id" in text, (
        "verifiable: must require attached evidence (test_id, command "
        "output, or commit SHA:file:line)"
    )
