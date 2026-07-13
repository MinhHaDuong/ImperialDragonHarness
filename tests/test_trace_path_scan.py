"""Tests for scripts/trace-path-scan.py — path-access allow/forbid scan (ticket 0289).

Child of tracker 0266 (pillage manifest, technique 1). The scan inspects the
agent tool-call trace for Read/Edit/Write/NotebookEdit/Bash calls that touch a
forbidden path — credential files or another session's worktree — the
scope-violation class a diff-only adherence check structurally misses
(arXiv:2604.21965 App. B.3). Pure-Python, zero LLM tokens → fast tier, no marker.
"""

import importlib.util
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location("trace_path_scan", SCRIPTS / "trace-path-scan.py")
tps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tps)


def _tool_row(msg_id, name, tool_input, ts_str="2026-07-12T10:00:00.000Z"):
    """One assistant row carrying a single tool_use block."""
    block = {"type": "tool_use", "id": f"{msg_id}_tu", "name": name, "input": tool_input}
    return {
        "type": "assistant",
        "timestamp": ts_str,
        "message": {
            "id": msg_id,
            "model": "claude-opus-4-8",
            "role": "assistant",
            "content": [block],
        },
    }


def _write_trace(tmp_path, rows):
    trace = tmp_path / "trace.jsonl"
    trace.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return trace


def test_forbidden_credential_path_detected(tmp_path):
    trace = _write_trace(tmp_path, [
        _tool_row("m1", "Read", {"file_path": "/home/u/.ssh/id_rsa"}),
    ])
    hits = tps.scan_trace_for_forbidden_paths(trace)
    assert len(hits) == 1
    assert hits[0]["tool"] == "Read"
    assert hits[0]["path"] == "/home/u/.ssh/id_rsa"
    assert "ssh" in hits[0]["reason"].lower()
    assert hits[0]["line"] == 1


def test_bash_command_touching_forbidden_path_detected(tmp_path):
    trace = _write_trace(tmp_path, [
        _tool_row("m1", "Bash", {"command": "cat ~/.aws/credentials"}),
    ])
    hits = tps.scan_trace_for_forbidden_paths(trace)
    assert len(hits) == 1
    assert hits[0]["tool"] == "Bash"
    assert ".aws/credentials" in hits[0]["path"]


def test_other_session_worktree_path_detected(tmp_path):
    trace = _write_trace(tmp_path, [
        _tool_row("m1", "Read", {"file_path": "/home/u/.claude/worktrees/other-session/file.py"}),
    ])
    hits = tps.scan_trace_for_forbidden_paths(
        trace, worktree_root="/home/u/.claude/worktrees/mine"
    )
    assert len(hits) == 1
    assert "worktree" in hits[0]["reason"].lower()


def test_own_worktree_path_allowed(tmp_path):
    trace = _write_trace(tmp_path, [
        _tool_row("m1", "Read", {"file_path": "/home/u/.claude/worktrees/mine/file.py"}),
    ])
    hits = tps.scan_trace_for_forbidden_paths(
        trace, worktree_root="/home/u/.claude/worktrees/mine"
    )
    assert hits == []


def test_clean_trace_no_violations(tmp_path):
    trace = _write_trace(tmp_path, [
        _tool_row("m1", "Read", {"file_path": "/home/u/proj/scripts/foo.py"}),
        _tool_row("m2", "Edit", {"file_path": "/home/u/proj/rules/bar.md"}),
        _tool_row("m3", "Bash", {"command": "uv run pytest -q"}),
    ])
    assert tps.scan_trace_for_forbidden_paths(trace) == []


def test_line_numbers_reported(tmp_path):
    trace = _write_trace(tmp_path, [
        _tool_row("m1", "Read", {"file_path": "/home/u/proj/scripts/foo.py"}),
        _tool_row("m2", "Read", {"file_path": "/home/u/.ssh/known_hosts"}),
    ])
    hits = tps.scan_trace_for_forbidden_paths(trace)
    assert len(hits) == 1
    assert hits[0]["line"] == 2
