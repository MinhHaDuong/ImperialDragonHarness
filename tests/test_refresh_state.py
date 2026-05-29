"""Tests for scripts/refresh-STATE.py — section splitting and formatting.

Covers the pure text-surgery helpers that decide how the ## Status block is
replaced while everything before/after it is preserved. The git/erg-touching
functions are left to integration; these pin the parsing that governs whether
hand-edited sections survive a refresh.
"""

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("refresh_state", SCRIPTS / "refresh-STATE.py")
rs = importlib.util.module_from_spec(spec)
sys.modules["refresh_state"] = rs
spec.loader.exec_module(rs)


def test_split_at_status_separates_preamble_and_tail():
    text = "# Title\n\nLast updated: x\n\n## Status\nold status\n\n## Blockers\nb"
    preamble, tail = rs.split_at_status(text)
    assert "# Title" in preamble
    assert "## Status" not in preamble
    assert tail.startswith("## Status")
    assert "## Blockers" in tail


def test_split_at_status_no_status_heading():
    text = "# Title\n\njust preamble"
    preamble, tail = rs.split_at_status(text)
    assert preamble == text.rstrip()
    assert tail == ""


def test_next_section_idx_finds_following_heading():
    tail = "## Status\nbody line\n## Blockers\nx"
    idx = rs._next_section_idx(tail, len(rs.STATUS_HEADING) + 1)
    assert tail[idx:].startswith("## Blockers")


def test_next_section_idx_returns_len_when_no_more_headings():
    tail = "## Status\nbody only, no further heading"
    assert rs._next_section_idx(tail, len(rs.STATUS_HEADING) + 1) == len(tail)


def test_refresh_last_updated_replaces_line():
    preamble = "# T\n\nLast updated: 2020-01-01T00:00Z\n\nintro"
    out = rs.refresh_last_updated(preamble, "2026-05-29T10:00Z")
    assert "Last updated: 2026-05-29T10:00Z" in out
    assert "2020-01-01" not in out


def test_refresh_last_updated_warns_when_absent(capsys):
    preamble = "# T\n\nno timestamp line"
    out = rs.refresh_last_updated(preamble, "2026-05-29T10:00Z")
    assert out == preamble  # unchanged
    assert "Last updated" in capsys.readouterr().err


def test_format_status_summarizes_ready_and_blocked():
    tickets = [
        {"id": "0001", "ready": True},
        {"id": "0002", "ready": True},
        {"id": "0003", "ready": False},
    ]
    lines = rs.format_status(tickets, ["abc123 commit one"])
    joined = "\n".join(lines)
    assert lines[0] == rs.STATUS_HEADING
    assert "2 ready · 1 blocked" in joined
    assert "**Recent commits:**" in joined
    assert "abc123 commit one" in joined


def test_format_status_omits_commits_when_none():
    lines = rs.format_status([{"id": "0001", "ready": True}], [])
    assert "**Recent commits:**" not in "\n".join(lines)
