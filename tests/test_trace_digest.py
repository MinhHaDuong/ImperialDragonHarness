"""Tests for scripts/trace-digest.py — per-trace digest for LLM open-coding (ticket 0240)."""

import importlib.util
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location("trace_digest", SCRIPTS / "trace-digest.py")
td = importlib.util.module_from_spec(spec)
spec.loader.exec_module(td)


def _assistant_row(
    msg_id,
    cache_read=100_000,
    output=200,
    model="claude-opus-4-8",
    tool_uses=None,
    ts_str="2026-06-09T10:00:00.000Z",
):
    content = [{"type": "text", "text": "secret assistant text"}]
    for i, (name, tool_input) in enumerate(tool_uses or []):
        content.append(
            {"type": "tool_use", "id": f"{msg_id}_tu{i}", "name": name, "input": tool_input}
        )
    return {
        "type": "assistant",
        "timestamp": ts_str,
        "message": {
            "id": msg_id,
            "model": model,
            "role": "assistant",
            "usage": {
                "input_tokens": 50,
                "output_tokens": output,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": 1_000,
            },
            "content": content,
        },
    }


def _compact_row():
    return {
        "type": "system",
        "subtype": "compact_boundary",
        "timestamp": "2026-06-09T10:30:00.000Z",
        "compactMetadata": {"trigger": "auto", "preTokens": 170_000, "postTokens": 12_000},
    }


def _write(tmp_path, rows, name="session.jsonl"):
    f = tmp_path / name
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return f


def test_digest_contains_turn_count_and_totals(tmp_path):
    rows = [
        _assistant_row("m1", cache_read=100_000),
        _assistant_row("m2", cache_read=200_000),
    ]
    text = td.digest_trace(_write(tmp_path, rows))
    assert "turns: 2" in text
    assert "cache_read: 300,000" in text
    assert "output: 400" in text


def test_tokens_deduped_by_message_id(tmp_path):
    """The mandatory 0236 fixture: one message over 3 JSONL rows counts once."""
    rows = [_assistant_row("dup", cache_read=100_000)] * 3 + [
        _assistant_row("other", cache_read=100_000)
    ]
    text = td.digest_trace(_write(tmp_path, rows))
    assert "turns: 2" in text
    assert "cache_read: 200,000" in text


def test_tool_calls_named_but_args_stripped(tmp_path):
    rows = [
        _assistant_row(
            "m1",
            tool_uses=[
                ("Bash", {"command": "git push --force-with-lease origin main"}),
                ("Read", {"file_path": "/home/u/project/notes.md"}),
            ],
        )
    ]
    text = td.digest_trace(_write(tmp_path, rows))
    assert "Bash(git)" in text
    assert "--force-with-lease" not in text
    assert "Read" in text and "notes.md" in text


def test_no_message_text_in_digest(tmp_path):
    """Privacy invariant: assistant/user text never reaches the digest."""
    rows = [_assistant_row("m1")]
    rows.append(
        {
            "type": "user",
            "timestamp": "2026-06-09T10:01:00.000Z",
            "message": {"role": "user", "content": "private user prompt"},
        }
    )
    text = td.digest_trace(_write(tmp_path, rows))
    assert "secret assistant text" not in text
    assert "private user prompt" not in text


def test_compact_boundary_marked(tmp_path):
    rows = [_assistant_row("a"), _compact_row(), _assistant_row("b")]
    text = td.digest_trace(_write(tmp_path, rows))
    assert "COMPACT" in text


def test_subagent_spawn_marked(tmp_path):
    rows = [
        _assistant_row(
            "m1", tool_uses=[("Task", {"subagent_type": "Explore", "prompt": "hidden prompt"})]
        )
    ]
    text = td.digest_trace(_write(tmp_path, rows))
    assert "SPAWN" in text and "Explore" in text
    assert "hidden prompt" not in text


def test_long_trace_coalesced_under_budget(tmp_path):
    rows = [_assistant_row(f"m{i}", cache_read=400_000) for i in range(500)]
    text = td.digest_trace(_write(tmp_path, rows), max_tokens=2000)
    assert td.estimate_tokens(text) <= 2000
    assert "turns: 500" in text  # totals survive coalescing


def test_estimate_tokens():
    assert td.estimate_tokens("a" * 400) == 100


def test_cli_flags_present():
    src = (SCRIPTS / "trace-digest.py").read_text()
    for flag in ("--trace", "--output-dir", "--max-tokens"):
        assert flag in src, f"missing CLI flag {flag}"
    assert "ArgumentParser" in src
