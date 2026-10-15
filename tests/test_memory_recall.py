"""Tests for scripts/census/memory-recall.py — the maintenance-arm classifier.

The script had no test file when the memory skill was renamed
`memory` -> `memory-sweep` on 2026-09-16. That is why the rename sweep, which
keyed on the path `skills/memory` and the command `/memory`, walked past the
two regexes below: there the skill appears as a bare alternative inside a
pattern, matching neither search key. `make check` stayed green while the
classifier silently stopped recognising the renamed skill.

The arm it classifies is the script's own positive control — its docstring
calls it load-bearing, on the reasoning that a probe blind there cannot be
trusted anywhere. A control that silently stops firing is the failure this
file exists to prevent.
"""

import importlib.util
from pathlib import Path

CENSUS = Path(__file__).resolve().parent.parent / "scripts" / "census"

spec = importlib.util.spec_from_file_location("memory_recall", CENSUS / "memory-recall.py")
mr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mr)


def test_skill_pattern_matches_both_sides_of_the_memory_rename():
    """Traces predate and postdate the rename, so both spellings must match."""
    assert mr.SKILL.search(b'"skill": "memory-sweep"')
    assert mr.SKILL.search(b'"skill": "memory"')


def test_command_pattern_matches_both_sides_of_the_memory_rename():
    assert mr.CMD.search(b"<command-name>/memory-sweep</command-name>")
    assert mr.CMD.search(b"<command-name>/memory</command-name>")


def test_patterns_still_match_the_untouched_maintenance_skills():
    for name in (b"dream", b"roar", b"lair"):
        assert mr.SKILL.search(b'"skill": "' + name + b'"')
        assert mr.CMD.search(b"<command-name>/" + name + b"</command-name>")


def test_patterns_do_not_match_an_unrelated_skill():
    """Without this, a pattern loosened into matching everything would read as
    a pass — the all-clear has to be distinguishable from 'I could not look'."""
    assert not mr.SKILL.search(b'"skill": "hunt"')
    assert not mr.CMD.search(b"<command-name>/hunt</command-name>")


def test_trace_fixture_classifies_current_hoard_and_historical_dream(tmp_path):
    """Current hoard and historical dream sessions both stay maintenance."""
    hoard = tmp_path / "hoard.jsonl"
    hoard.write_text(
        '{"type":"assistant","message":{"content":[{"type":"tool_use",'
        '"name":"Skill","input":{"skill":"hoard"}}]}}\n'
    )
    hoard_command = tmp_path / "hoard-command.jsonl"
    hoard_command.write_text(
        '{"type":"user","message":{"content":"<command-name>/hoard</command-name>"}}\n'
    )
    dream = tmp_path / "dream.jsonl"
    dream.write_text(
        '{"type":"user","message":{"content":"<command-name>/dream</command-name>"}}\n'
    )
    hunt = tmp_path / "hunt.jsonl"
    hunt.write_text(
        '{"type":"assistant","message":{"content":[{"type":"tool_use",'
        '"name":"Skill","input":{"skill":"hunt"}}]}}\n'
    )

    assert mr.scan_file(str(hoard))["maintenance"] is True
    assert mr.scan_file(str(hoard_command))["maintenance"] is True
    assert mr.scan_file(str(dream))["maintenance"] is True
    assert mr.scan_file(str(hunt))["maintenance"] is False
