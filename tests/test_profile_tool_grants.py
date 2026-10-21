"""Profile text must not instruct a tool its agent definition lacks (ticket 1167).

A 14-day transcript scan found 74 "No such tool available: Skill" and 15 Grep
failures: a profile told the delegate to call a tool the definition never
granted. The lint reads each agents/<name>.md ``tools:`` list and the matching
profiles/<name>/PROFILE.md text; a text that instructs a tool outside the list
fails, unless it names the substitute with the phrase ``no <Tool> tool``.
Shells without a ``tools:`` line inherit every tool and are skipped.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

# tool -> pattern that means "this text tells the reader to call it".
INSTRUCTS = {
    "Skill": re.compile(r"\bSkill\(|\binvoke\b"),
    "Grep": re.compile(r"\bGrep\b"),
    "Glob": re.compile(r"\bGlob\b"),
    "Edit": re.compile(r"\bEdit\b"),
    "Write": re.compile(r"\bWrite\b"),
    "Agent": re.compile(r"\bAgent\(|\bAgent tool\b"),
}


def granted(shell_text: str):
    """Set of granted tools, or None when the shell grants all."""
    block = shell_text.split("---", 2)[1]
    m = re.search(r"^tools:\s*(.+)$", block, re.M)
    return None if m is None else {t.strip() for t in m.group(1).split(",")}


def missing_tools(shell_text: str, profile_text: str) -> list[str]:
    tools = granted(shell_text)
    if tools is None:
        return []
    return [
        tool
        for tool, pat in INSTRUCTS.items()
        if tool not in tools
        and pat.search(profile_text)
        and f"no {tool} tool" not in profile_text
    ]


def test_lint_fires_on_known_bad_fixture():
    """Positive control: the lint must fire on a text it should reject."""
    shell = "---\nname: x\ntools: Read, Bash\n---\n"
    bad = "Your FIRST action is to invoke the skill; then Grep the tree."
    assert missing_tools(shell, bad) == ["Skill", "Grep"]
    assert missing_tools(shell, bad + " There is no Skill tool, no Grep tool.") == []
    assert missing_tools("---\nname: x\n---\n", bad) == []


def test_every_profile_calls_only_tools_its_shell_grants():
    shells = sorted((REPO / "agents").glob("*.md"))
    assert shells
    for shell in shells:
        profile = REPO / "profiles" / shell.stem / "PROFILE.md"
        if not profile.exists():
            continue
        lacking = missing_tools(
            shell.read_text(encoding="utf-8"), profile.read_text(encoding="utf-8")
        )
        assert not lacking, (
            f"{profile.relative_to(REPO)} instructs {lacking} but "
            f"agents/{shell.name} does not grant them: grant the tool or "
            f"write 'no <Tool> tool' with the substitute"
        )
