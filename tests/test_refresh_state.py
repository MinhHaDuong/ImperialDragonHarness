"""Tests for scripts/refresh-STATE.py — section splitting and formatting.

Covers the pure text-surgery helpers that decide how the ## Status block is
replaced while everything before/after it is preserved. The git/erg-touching
functions are left to integration; these pin the parsing that governs whether
hand-edited sections survive a refresh.
"""

import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "refresh_state", SCRIPTS / "refresh-STATE.py"
)
rs = importlib.util.module_from_spec(spec)
sys.modules["refresh_state"] = rs
spec.loader.exec_module(rs)

NO_TICKETS = {"ready": 0, "blocked": 0, "awaiting": 0, "next": []}


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


# format_status — one orientation question per line (ticket 0304)


def test_format_status_summarizes_ready_and_blocked():
    tickets = {"ready": 2, "blocked": 1, "awaiting": 0, "next": []}
    lines = rs.format_status(tickets, ["abc123 commit one"])
    joined = "\n".join(lines)
    assert lines[0] == rs.STATUS_HEADING
    assert "2 ready · 1 blocked" in joined
    assert "awaiting author" not in joined  # zero awaiting → omitted
    assert "**Recent (first-parent):**" in joined
    assert "abc123 commit one" in joined


def test_format_status_omits_commits_when_none():
    tickets = {"ready": 1, "blocked": 0, "awaiting": 0, "next": []}
    assert "Recent" not in "\n".join(rs.format_status(tickets, []))


def test_format_status_names_awaiting_and_next_picks():
    tickets = {
        "ready": 3,
        "blocked": 1,
        "awaiting": 2,
        "next": [("0268", "guard refresh-STATE"), ("0304", "x" * 60)],
    }
    joined = "\n".join(rs.format_status(tickets, []))
    assert "2 awaiting author" in joined
    assert "next: 0268 guard refresh-STATE · 0304" in joined
    assert "x" * 60 not in joined  # long title truncated
    assert "…" in joined


def test_format_status_anchor_and_in_flight_lines():
    joined = "\n".join(
        rs.format_status(
            NO_TICKETS, [], head_sha="4b3837e", in_flight="2 open PRs", ci="success"
        )
    )
    assert "· as of 4b3837e -->" in joined
    assert "**In flight:** 2 open PRs · CI main: success" in joined


def test_format_status_omits_unknowable_lines():
    # No forge CLI (in_flight=None, ci=None), no anchor: plain block, no stubs.
    joined = "\n".join(rs.format_status(NO_TICKETS, ["abc msg"]))
    assert "In flight" not in joined
    assert "as of" not in joined


# The erg JSON schema is the contract that previously bit us: items carry NO
# `ready` flag (blocked = list minus ready) and label values live under
# `labels`. These fixtures mirror the real schema exactly
# (keys: id, title, file, closed, refs, labels, blocked_by).


def _erg_item(tid: str, labels=()) -> dict:
    return {
        "id": tid,
        "title": f"t{tid}",
        "file": f"{tid}.erg",
        "closed": False,
        "refs": [],
        "labels": list(labels),
        "blocked_by": [],
    }


def test_get_tickets_derives_blocked_awaiting_and_next(tmp_path, monkeypatch):
    (tmp_path / "tickets").mkdir()
    (tmp_path / "tickets" / "erg").touch()

    ready = [_erg_item("0001"), _erg_item("0002"), _erg_item("0003")]
    open_all = [_erg_item(f"00{i:02d}") for i in range(1, 9)]  # 8 open
    open_all[4]["labels"] = ["needs-human"]
    open_all[5]["labels"] = ["needs-human", "deferred"]

    def fake_run(cmd, repo_root):
        return json.dumps(ready if "ready" in cmd else open_all)

    monkeypatch.setattr(rs, "run", fake_run)
    t = rs.get_tickets(tmp_path)
    assert (t["ready"], t["blocked"], t["awaiting"]) == (3, 5, 2)
    assert t["next"] == [("0001", "t0001"), ("0002", "t0002")]


def test_get_tickets_never_returns_negative_blocked(tmp_path, monkeypatch):
    (tmp_path / "tickets").mkdir()
    (tmp_path / "tickets" / "erg").touch()

    # Defensive: if ready somehow exceeds open, blocked floors at 0, not negative.
    def fake_run(cmd, repo_root):
        return (
            json.dumps([_erg_item("0001"), _erg_item("0002")])
            if "ready" in cmd
            else json.dumps([_erg_item("0001")])
        )

    monkeypatch.setattr(rs, "run", fake_run)
    t = rs.get_tickets(tmp_path)
    assert (t["ready"], t["blocked"]) == (2, 0)


# main() — end-to-end text surgery with all subprocess surfaces faked


def _repo_with_state(tmp_path, state_text):
    (tmp_path / "STATE.md").write_text(state_text)
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    (tickets / "erg").touch()
    return tmp_path


def _fake_run(cmd, repo_root):
    if "rev-parse" in cmd:
        return "abc1234"
    if "log" in cmd:
        return "abc1234 test commit"
    return "[]"


def _patch_subprocess_surfaces(monkeypatch):
    monkeypatch.setattr(rs, "run", _fake_run)
    monkeypatch.setattr(rs, "_gh_json", lambda args, repo_root: None)


def test_main_uses_path_argument(tmp_path, monkeypatch):
    """main() must use the supplied path argument, not git rev-parse."""
    _repo_with_state(
        tmp_path,
        "# Project\n\nLast updated: 2020-01-01T00:00Z\n\n## Status\nold\n\n## Blockers\nnone\n",
    )

    def checked_run(cmd, repo_root):
        assert repo_root == tmp_path, (
            f"run() called with repo_root={repo_root!r}, expected {tmp_path!r}"
        )
        return _fake_run(cmd, repo_root)

    monkeypatch.setattr(rs, "run", checked_run)
    monkeypatch.setattr(rs, "_gh_json", lambda args, repo_root: None)
    monkeypatch.setattr(sys, "argv", ["refresh-STATE.py", str(tmp_path)])
    rs.main()

    refreshed = (tmp_path / "STATE.md").read_text()
    assert "old" not in refreshed
    assert "Last updated:" in refreshed
    assert "as of abc1234" in refreshed


# Guard (ticket 0268): a customized Status heading marks a hand-maintained
# section — the script must abort without writing rather than clobber it.
# An absent heading is the adoption path: append a generated section.


def test_main_aborts_on_titled_status_heading(tmp_path, monkeypatch, capsys):
    text = (
        "# P\n\nLast updated: 2020-01-01T00:00Z\n\n"
        "## Status: TWO PAPERS SUBMITTED\n### Oeconomia\ncurated detail\n"
    )
    _repo_with_state(tmp_path, text)
    _patch_subprocess_surfaces(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["refresh-STATE.py", str(tmp_path)])
    try:
        rs.main()
        raise AssertionError("expected SystemExit")
    except SystemExit as e:
        assert e.code == 2
    assert (tmp_path / "STATE.md").read_text() == text  # byte-identical
    assert "refusing to overwrite" in capsys.readouterr().err


def test_main_aborts_on_status_snapshot_heading(tmp_path, monkeypatch):
    text = "# P\n\nLast updated: x\n\n## Status snapshot\nhand-written\n"
    _repo_with_state(tmp_path, text)
    _patch_subprocess_surfaces(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["refresh-STATE.py", str(tmp_path)])
    try:
        rs.main()
        raise AssertionError("expected SystemExit")
    except SystemExit as e:
        assert e.code == 2
    assert (tmp_path / "STATE.md").read_text() == text


def test_main_appends_status_when_heading_absent(tmp_path, monkeypatch):
    text = "# P\n\nLast updated: 2020-01-01T00:00Z\n\n## North star\nwhy we exist\n"
    _repo_with_state(tmp_path, text)
    _patch_subprocess_surfaces(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["refresh-STATE.py", str(tmp_path)])
    rs.main()
    out = (tmp_path / "STATE.md").read_text()
    assert "## North star\nwhy we exist" in out  # hand content preserved
    assert "## Status" in out and "abc1234" in out  # generated section appended
