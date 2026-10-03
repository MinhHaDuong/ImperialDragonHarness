"""Guards rule pins (ticket 0938, wave 0).

Two audience-neutral guards apply to every agent role — the main session and
every spawned profile alike, whatever runtime launched it. They lived inline
in AGENTS.md (## Harness instructions and ## Project memory boundary), which
made them invisible to bare-context profiles that do not inherit harness
text. Wave 0 hoists both into ``rules/guards.md``; later waves list that one
file in each PROFILE.md contract instead of restating the guards per role.

These tests pin the rule file so the hoist cannot drift back: the
credential-display ban must keep its partial-display clause and its
"here's what I found" carve-out (a summary is still chat text), and the
no-write guard must keep the stop-and-report fallback ban. They fail while
``rules/guards.md`` is absent — the wave 0 red step.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

GUARDS = REPO / "rules" / "guards.md"


def _guards_text() -> str:
    """Whitespace-normalized: the pinned sentences must survive re-wrapping."""
    return " ".join(GUARDS.read_text().split())


def test_guards_rule_exists_and_addresses_every_agent_role():
    text = _guards_text()
    # One sentence at the top states both guards apply to every agent role.
    assert "every agent" in text


def test_guards_rule_bans_credential_display():
    text = _guards_text()
    assert (
        "Never display API keys, tokens, passwords, or any credentials in chat text"
        in text
    )
    assert "not even partially" in text
    assert '"here\'s what I found"' in text


def test_guards_rule_pins_the_no_write_guard():
    text = _guards_text()
    assert "does not authorize writing" in text
    assert "harness, its shared memory, or another project" in text
    assert "Resolve the project repository before writing" in text
    assert "stop and report an unavailable destination" in text
    assert "instead of falling back to the harness or native store" in text
