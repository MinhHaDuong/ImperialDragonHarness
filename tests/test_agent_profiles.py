"""Agent profile subsystem pins (ticket 0938, wave 1).

The design (docs/2026-10-03-agent-profile-subsystem-design.md) replaces
inline fork roles with thin runtime shells whose body is a pointer to a
harness-side contract at ``profiles/<name>/PROFILE.md``. No machinery
validates the pointer; these doc-pin tests are the enforcement surface the
design names: every roster shell exists with the census-checked card, points
at its contract, carries no model token, and every contract
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

# name -> description exactly as the inventory roster registers them.
# The census arithmetic (323 chars, 761/800) depends on these strings.
# No model: a frontmatter token reaches the API unmapped (HTTP 404, ticket
# 1063); the per-launch model is the only lever (rules/claude-code.md).
ROSTER = {
    "coder": "Executes a ticket contract in a worktree; branch, PR, evidence.",
    "code-reviewer": "Code-review seat; perspective arrives in the prompt.",
    "prose-reviewer": "Prose-panel seat; role and rulebook arrive in the prompt.",
    "gate-seat": "Read-only verify-gate seat; verdict only.",
    "adherence-seat": "Read-only verify-adherence seat; verdict artifact only.",
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
    for name, description in ROSTER.items():
        path = REPO / "agents" / f"{name}.md"
        assert path.is_file(), f"agents/{name}.md is absent — roster not landed"
        fm = _frontmatter(path)
        assert fm.get("name") == name, f"{path}: frontmatter name"
        assert fm.get("description") == description, (
            f"{path}: description must match the inventory roster verbatim "
            "(the census arithmetic depends on it)"
        )


def test_no_roster_shell_carries_a_model_token():
    """An unpinned launch sends a frontmatter model token to the API as-is
    (HTTP 404, ticket 1063); the model is chosen per launch, never here."""
    for name in ROSTER:
        path = REPO / "agents" / f"{name}.md"
        assert "model" not in _frontmatter(path), (
            f"{path}: frontmatter must not carry a model token"
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
    for name, description in ROSTER.items():
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
        .split("**Fan-out preflight:**", 1)[0]
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


# Wave 3 (ticket 0938, final exit criterion): a profile ports to Pi by
# frontmatter translation alone — demonstrated once, on the pickup surface
# the inventory verified (~/.pi/agent/agents/*.md, the subagent extension).
# The deployed translation is committed as a reproducible template under
# adapters/pi/agents/ so the demonstration is not a one-machine anecdote.
PI_TEMPLATE = REPO / "adapters" / "pi" / "agents" / "code-reviewer.md"

# The deployed Pi values the wave-3 demonstration recorded (ticket 0938
# log, 2026-10-03): model is the observed padme serving value, tools are
# the existing Pi reviewer.md style. Mutations of any of the three pinned
# frontmatter fields must fail the pins below.
PI_MODEL = "padme/qwen3.8-27b"
PI_TOOLS = "read, grep, find, ls, bash"
PI_PROVENANCE_COMMENT = (
    "<!-- Pi translation of agents/code-reviewer.md; "
    "ticket 0938 portability demonstration. -->"
)


def test_pi_translation_template_exists():
    assert PI_TEMPLATE.is_file(), (
        "adapters/pi/agents/code-reviewer.md is absent — the Pi portability "
        "demonstration (0938 exit criterion 3) has no committed template"
    )


def test_pi_translation_carries_the_contract_pointer():
    """The translation changes frontmatter only; the body stays the
    thin-shell pointer, so the contract at profiles/code-reviewer/PROFILE.md
    is the single truth on both runtimes."""
    body = " ".join(PI_TEMPLATE.read_text(encoding="utf-8").split())
    assert "Step 0" in body, "adapters/pi template: no step-0 pointer"
    assert "profiles/code-reviewer/PROFILE.md" in body, (
        "adapters/pi template: must point at profiles/code-reviewer/PROFILE.md"
    )
    assert "say so in your first output line" in body
    assert "Never guess a different root" in body


def test_pi_translation_frontmatter_matches_the_in_repo_shell():
    """Frontmatter is the whole translation: name and description carried
    verbatim from the in-repo shell, model and tools at the deployed Pi
    values. Each field is pinned against drift — a runtime re-translation
    that renames, rewrites the census card, or re-points the model or tool
    grant must fail here, not in the field."""
    fm = _frontmatter(PI_TEMPLATE)
    shell = _frontmatter(REPO / "agents" / "code-reviewer.md")
    assert fm.get("name") == shell.get("name") == "code-reviewer", (
        "the Pi translation and the in-repo shell must declare the same "
        "frontmatter name — the port is a key translation, not a rename"
    )
    assert fm.get("description") == shell.get("description"), (
        "the Pi template description must equal the in-repo shell "
        "description verbatim — the census-counted routing card travels "
        "unchanged across runtimes"
    )
    assert fm.get("model") == PI_MODEL, (
        f"the Pi template model must stay the deployed value '{PI_MODEL}' "
        "(the wave-3 observed padme serving value)"
    )
    assert fm.get("tools") == PI_TOOLS, (
        f"the Pi template tools must stay the deployed reviewer-style list "
        f"'{PI_TOOLS}' — the shell's tool grant is not widened by the port"
    )


def test_pi_template_body_is_the_shell_pointer_plus_one_provenance_comment():
    """Accurate claim (gaze round-1 correction, PR #1175): frontmatter
    translated; pointer paragraph byte-identical; exactly one provenance
    comment added after the frontmatter (Pi's parseFrontmatter requires
    the file to start with ---). Any other body drift — a reworded pointer,
    a second comment, a Pi-local edit — fails here."""
    shell_body = (
        (REPO / "agents" / "code-reviewer.md")
        .read_text(encoding="utf-8")
        .split("---", 2)[2]
    )
    template_body = PI_TEMPLATE.read_text(encoding="utf-8").split("---", 2)[2]
    assert template_body == "\n\n" + PI_PROVENANCE_COMMENT + shell_body, (
        "the Pi template body must be the in-repo shell's pointer paragraph "
        "byte-identical, preceded by exactly the one provenance comment"
    )


# Wave 3 fix (ticket 0938, gaze reroll round 1, PR #1175): the three
# remaining inventory-justified call sites launch named profiles per the
# wave-2 pattern. Each pin slices to its launch block only — a stray
# profile mention elsewhere in the skill must not satisfy it.
GAZE = REPO / "skills" / "gaze" / "SKILL.md"
PROSE = REPO / "skills" / "review-pr-prose" / "SKILL.md"


def test_gaze_agent_a_launch_names_the_adherence_seat_profile():
    """The phase 2-4 adherence launch (label-skip aside) names the
    adherence-seat profile and its contract; the live Skill(verify-adherence)
    invocation stays in the block — the sub-skill contract is not a role
    rail and is not delegated."""
    gaze = GAZE.read_text(encoding="utf-8")
    launch = " ".join(
        gaze.split("**Agent A — adherence**", 1)[1]
        .split("**Agent B — built-in review**", 1)[0]
        .split()
    )
    assert "the adherence-seat profile" in launch, (
        "the Agent A launch block must name the adherence-seat profile it "
        "launches (agents/adherence-seat.md)"
    )
    assert "agents/adherence-seat.md" in launch
    assert "profiles/adherence-seat/PROFILE.md" in launch, (
        "the Agent A launch block must point at the contract that owns the "
        "seat rails"
    )
    assert 'Skill(skill: "verify-adherence"' in launch, (
        "the live Skill(verify-adherence) invocation contract stays verbatim "
        "in the Agent A launch block"
    )


def test_gaze_gate_launch_names_the_gate_seat_profile():
    """The phase 6 gate launch names the gate-seat profile and its contract;
    the embedded gate procedure below the launch stays in the skill."""
    gaze = GAZE.read_text(encoding="utf-8")
    launch = " ".join(
        gaze.split("### 6. Gate", 1)[1]
        .split("Embedded gate procedure:", 1)[0]
        .split()
    )
    assert "the gate-seat profile" in launch, (
        "the phase 6 gate launch block must name the gate-seat profile it "
        "launches (agents/gate-seat.md)"
    )
    assert "agents/gate-seat.md" in launch
    assert "profiles/gate-seat/PROFILE.md" in launch, (
        "the gate launch block must point at the contract that owns the "
        "containment rails"
    )


def test_prose_panel_launches_name_the_prose_reviewer_profile():
    """The panel recruitment step launches every seat as the
    prose-reviewer profile; the role and rulebook ride in the prompt, the
    editorial-brief auditor stays inline by inventory."""
    prose = PROSE.read_text(encoding="utf-8")
    launch = " ".join(
        prose.split("3. Recruit the panel", 1)[1]
        .split("## The seats are", 1)[0]
        .split()
    )
    assert "the prose-reviewer profile" in launch, (
        "the review-pr-prose launch step must name the prose-reviewer "
        "profile it launches (agents/prose-reviewer.md)"
    )
    assert "agents/prose-reviewer.md" in launch
    assert "profiles/prose-reviewer/PROFILE.md" in launch, (
        "the prose launch step must point at the contract that owns the "
        "seat rails"
    )

def test_coder_profile_conversions():
    """The two inventory coder sites (gaze REROLL fix, raid wave execution)
    launch the named coder profile; task materials ride in the prompt."""
    gaze = (REPO / "skills" / "gaze" / "SKILL.md").read_text(encoding="utf-8")
    reroll = gaze.split("- **REROLL, round 1**", 1)[1].split("- **REROLL, round 2**", 1)[0]
    assert "coder profile" in reroll and "agents/coder.md" in reroll
    assert "profiles/coder/PROFILE.md" in reroll
    raid = (REPO / "skills" / "raid" / "SKILL.md").read_text(encoding="utf-8")
    wave = raid.split("For each wave, launch agents", 1)[1].split(
        "The execute-agent contract", 1
    )[0]
    assert "coder" in wave and "agents/coder.md" in wave
    assert "profiles/coder/PROFILE.md" in wave


def test_hunt_detach_profile_carries_skill_and_agent_tools():
    """The executor hunt step 2b detaches must be able to run the hunt flow.

    Its first action is ``Skill(skill: "hunt", ...)`` and the flow launches
    reviewers and /review-pr seats; a profile without Skill and Agent stops at
    once (ticket 1075, observed on ticket 1046).
    """
    hunt = (REPO / "skills" / "hunt" / "SKILL.md").read_text(encoding="utf-8")
    named = set(re.findall(r"agents/([\w-]+)\.md", hunt))
    assert named, "hunt must name the profile it detaches to"
    for name in named:
        tools = _frontmatter(REPO / "agents" / f"{name}.md").get("tools", "")
        listed = {t.strip() for t in tools.split(",")}
        assert {"Skill", "Agent"} <= listed, (
            f"agents/{name}.md tools {tools!r} must include Skill and Agent"
        )
