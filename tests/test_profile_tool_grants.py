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

# Tool-use forms only: "Write(", "Write tool", "use/call/run the Write".
_USE = r"\b{0}\(|\b{0} tool\b|\b(?:use|call|run|invoke)\s+(?:the\s+)?{0}\b"

# tool -> pattern that means "this text tells the reader to call it".
INSTRUCTS = {
    "Skill": re.compile(
        r"\bSkill\(|\binvoke\b"
        r"|\b(?:load|run|use|call|follow)\b[^.\n]*?(?<![/\w])skill\b(?!\.md|s)",
        re.I,
    ),
    "Grep": re.compile(_USE.format("Grep")),
    "Glob": re.compile(_USE.format("Glob")),
    "Edit": re.compile(_USE.format("Edit")),
    "Write": re.compile(_USE.format("Write")),
    "Agent": re.compile(r"\bAgent\(|\bAgent tool\b"),
}


def granted(shell_text: str):
    """Set of granted tools, or None when the shell grants all."""
    parts = shell_text.split("---", 2)
    assert len(parts) == 3, "agent shell has no frontmatter block"
    block = parts[1]
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
        and any(
            pat.search(line) and f"no {tool} tool" not in line
            for line in profile_text.splitlines()
        )
    ]


def test_lint_fires_on_known_bad_fixture():
    """Positive control: the lint must fire on a text it should reject."""
    shell = "---\nname: x\ntools: Read, Bash\n---\n"
    # Control updated for ticket 1167: bare "Grep the tree" no longer matches;
    # Grep must appear in a tool-use form ("use the Grep tool").
    bad = "Your FIRST action is to invoke the skill; then use the Grep tool."
    assert missing_tools(shell, bad) == ["Skill", "Grep"]
    # Per line: the substitute must sit on the instructing line itself.
    assert missing_tools(shell, bad + "\nThere is no Skill tool, no Grep tool.") == [
        "Skill",
        "Grep",
    ]
    same = "Invoke the skill (no Skill tool: read it) and use the Grep tool (no Grep tool: use grep)."
    assert missing_tools(shell, same) == []
    assert missing_tools("---\nname: x\n---\n", bad) == []
    assert missing_tools(shell, "Your first action is Skill(hunt).") == ["Skill"]


def test_substitute_line_alone_clears_its_tool():
    shell = "---\nname: x\ntools: Read, Bash\n---\n"
    assert missing_tools(shell, "You have no Skill tool: read it with Read.") == []


def test_substitute_mention_does_not_clear_other_lines():  # row (a)
    shell = "---\nname: x\ntools: Read, Bash\n---\n"
    text = "You have no Skill tool: read it with Read.\n...\nLater: call Skill(hunt) first."
    assert missing_tools(shell, text) == ["Skill"]


def test_skill_wordings_load_run_follow():  # row (b)
    shell = "---\nname: x\ntools: Read, Bash\n---\n"
    assert missing_tools(shell, "Load the hunt skill first and follow it.") == ["Skill"]
    for ok in (
        "Read skills/hunt/SKILL.md for the steps.",
        "Skills:",
        "See skills/hunt/SKILL.md and use it as a guide.",
    ):
        assert missing_tools(shell, ok) == [], ok


def test_bare_english_word_is_not_a_tool_call():  # row (c)
    shell = "---\nname: x\ntools: Read, Bash\n---\n"
    assert missing_tools(shell, "Write the report in French.") == []
    assert missing_tools(shell, "Use the Write tool for the report.") == ["Write"]
    assert missing_tools(shell, "Call Edit(file) now.") == ["Edit"]


def test_granted_fails_clearly_without_frontmatter():  # row (d)
    with pytest.raises(AssertionError, match="frontmatter"):
        granted("no frontmatter here")


def test_every_profile_calls_only_tools_its_shell_grants():
    shells = sorted((REPO / "agents").glob("*.md"))
    assert shells
    checked = 0
    for shell in shells:
        profile = REPO / "profiles" / shell.stem / "PROFILE.md"
        if not profile.exists():
            continue
        checked += 1
        lacking = missing_tools(
            shell.read_text(encoding="utf-8"), profile.read_text(encoding="utf-8")
        )
        assert not lacking, (
            f"{profile.relative_to(REPO)} instructs {lacking} but "
            f"agents/{shell.name} does not grant them: grant the tool or "
            f"write 'no <Tool> tool' with the substitute"
        )
    assert checked, "no agent shell/profile pair was checked"
