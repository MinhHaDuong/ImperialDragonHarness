"""Exact tool-grant facts behind ticket 1167.

A 14-day transcript scan found 74 "No such tool available: Skill" failures: a
profile told the delegate to call Skill while its agent definition did not
grant it. The suspected cause was one missing grant plus three profiles that assumed it.
These checks pin those facts without parsing prose; a prose lint was tried and
withdrawn after two independent reviews kept defeating it (see ticket 1167's
log and the structured-declaration follow-up).
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

# Seats whose profile says "You have no Skill tool" must not be granted it.
READ_ONLY_SEATS = ("code-reviewer", "gate-seat", "prose-reviewer")


def granted(agent: str) -> set[str]:
    text = (REPO / "agents" / f"{agent}.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"agents/{agent}.md has no frontmatter block"
    m = re.search(r"^tools:\s*(.+)$", text.split("---", 2)[1], re.M)
    assert m, f"agents/{agent}.md has no tools: line"
    return {t.strip() for t in m.group(1).split(",")}


@pytest.mark.parametrize("seat", READ_ONLY_SEATS)
def test_seat_without_skill_says_so(seat):
    """The profile's substitute sentence and the grant must agree."""
    profile = (REPO / "profiles" / seat / "PROFILE.md").read_text(encoding="utf-8")
    assert "Skill" not in granted(seat)
    assert "You have no Skill tool: read that file with Read." in profile


# --- Declared needs (ticket 1175): one machine-read line, no English parsing.

PROFILES = sorted(
    d.name for d in (REPO / "profiles").iterdir() if (d / "PROFILE.md").is_file()
)
DECL = re.compile(r"^Requires-tools:[ \t]*(.+?)[ \t]*$", re.M)
SKILL_CALL = "Skill("


def declared(text: str, label: str = "profile") -> set[str]:
    """Tools named by the profile's single ``Requires-tools:`` line."""
    found = DECL.findall(text)
    assert len(found) == 1, f"{label}: needs exactly one Requires-tools: line"
    return {t.strip() for t in found[0].split(",") if t.strip()}


def check_pair(profile_text: str, shell_tools: set[str], label: str = "profile"):
    """Return the violations of one profile/shell pair."""
    errors = []
    missing = declared(profile_text, label) - shell_tools
    if missing:
        errors.append(f"{label}: declares ungranted tools {sorted(missing)}")
    if "Skill" not in shell_tools and SKILL_CALL in profile_text:
        errors.append(f"{label}: contains a Skill( call but the shell lacks Skill")
    return errors


def profile_text(name: str) -> str:
    return (REPO / "profiles" / name / "PROFILE.md").read_text(encoding="utf-8")


def test_at_least_one_pair_is_checked():
    assert PROFILES, "no profiles found: the declaration test would pass silently"


@pytest.mark.parametrize("name", PROFILES)
def test_profile_declaration_matches_its_shell(name):
    assert check_pair(profile_text(name), granted(name), name) == []


@pytest.mark.parametrize("name", PROFILES)
def test_every_profile_declares_something(name):
    assert declared(profile_text(name), name)


# Positive controls: mutate a copy of the text, never the real files.


def test_control_ungranted_declaration_fails():
    text = profile_text("gate-seat")
    mutated = text.replace("Requires-tools: ", "Requires-tools: Edit, Skill, ", 1)
    errors = check_pair(mutated, granted("gate-seat"), "gate-seat")
    assert errors and "Edit" in errors[0] and "Skill" in errors[0]


def test_control_tool_removed_from_shell_fails():
    shell = granted("coder") - {"Edit"}
    assert check_pair(profile_text("coder"), shell, "coder")


def test_control_skill_call_without_grant_fails():
    text = profile_text("gate-seat") + "\nCall Skill(skill: \"x\") first.\n"
    errors = check_pair(text, granted("gate-seat"), "gate-seat")
    assert any("Skill( call" in e for e in errors)


def test_control_missing_or_duplicate_declaration_fails():
    text = profile_text("coder")
    with pytest.raises(AssertionError):
        declared(DECL.sub("", text), "coder")
    with pytest.raises(AssertionError):
        declared(text + "\nRequires-tools: Read\n", "coder")
