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
    lines = rs.format_status(2, 1, ["abc123 commit one"])
    joined = "\n".join(lines)
    assert lines[0] == rs.STATUS_HEADING
    assert "2 ready · 1 blocked" in joined
    assert "**Recent commits:**" in joined
    assert "abc123 commit one" in joined


def test_format_status_omits_commits_when_none():
    lines = rs.format_status(1, 0, [])
    assert "**Recent commits:**" not in "\n".join(lines)


# The erg JSON schema is the contract that previously bit us: `erg ready` /
# `erg list` items carry NO `ready` flag, so get_tickets must derive the split
# from list-vs-ready counts. These fixtures mirror the real schema exactly
# (keys: id, title, file, closed, refs, tags, blocked_by).


def _erg_item(tid: str) -> dict:
    return {"id": tid, "title": f"t{tid}", "file": f"{tid}.erg",
            "closed": False, "refs": [], "tags": [], "blocked_by": []}


def test_get_tickets_derives_blocked_from_open_minus_ready(monkeypatch):
    import json as _json

    ready = [_erg_item("0001"), _erg_item("0002"), _erg_item("0003")]
    open_all = [_erg_item(f"00{i:02d}") for i in range(1, 9)]  # 8 open

    def fake_run(cmd):
        # cmd is the list passed to subprocess; pick which query by subcommand
        return _json.dumps(ready if "ready" in cmd else open_all)

    monkeypatch.setattr(rs, "run", fake_run)
    ready_count, blocked_count = rs.get_tickets()
    assert (ready_count, blocked_count) == (3, 5)


def test_get_tickets_never_returns_negative_blocked(monkeypatch):
    import json as _json

    # Defensive: if ready somehow exceeds open, blocked floors at 0, not negative.
    def fake_run(cmd):
        return _json.dumps([_erg_item("0001"), _erg_item("0002")]) if "ready" in cmd \
            else _json.dumps([_erg_item("0001")])

    monkeypatch.setattr(rs, "run", fake_run)
    assert rs.get_tickets() == (2, 0)
