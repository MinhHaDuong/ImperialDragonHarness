"""Tests for scripts/trace-stats.py — session-trace census (ticket 0237)."""

import importlib.util
import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location("trace_stats", SCRIPTS / "trace-stats.py")
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)


def _assistant_row(msg_id, model, usage, block, ts_str="2026-06-09T10:00:00.000Z"):
    return {
        "type": "assistant",
        "timestamp": ts_str,
        "message": {
            "id": msg_id,
            "model": model,
            "role": "assistant",
            "usage": usage,
            "content": [block],
        },
    }


USAGE = {
    "input_tokens": 100,
    "output_tokens": 50,
    "cache_read_input_tokens": 1000,
    "cache_creation_input_tokens": 200,
}


def _fixture_lines():
    """Hand-written records covering the mandatory ticket 0237 cases."""
    bash_block = {
        "type": "tool_use",
        "id": "toolu_1",
        "name": "Bash",
        "input": {"command": "git status"},
    }
    bash_block2 = dict(bash_block, id="toolu_2")
    text_block = {"type": "text", "text": "hello"}
    rows = [
        # One assistant message whose usage is REPEATED across 3 rows,
        # same message.id — must be counted ONCE (the 2.7x bug).
        _assistant_row("msg_A", "claude-opus-4-8", USAGE, text_block),
        _assistant_row("msg_A", "claude-opus-4-8", USAGE, bash_block),
        _assistant_row("msg_A", "claude-opus-4-8", USAGE, bash_block2),
        # A <synthetic> record: excluded from $, counted in synthetic_messages.
        _assistant_row(
            "msg_synth",
            "<synthetic>",
            USAGE,
            {"type": "text", "text": "synthetic"},
            ts_str="2026-06-09T10:01:00.000Z",
        ),
    ]
    lines = [json.dumps(r) for r in rows]
    lines.append("{this is not json")  # one malformed line
    return lines


def _write_fixture(tmp_path):
    f = tmp_path / "session.jsonl"
    f.write_text("\n".join(_fixture_lines()) + "\n")
    return f


def test_usage_deduped_by_message_id(tmp_path):
    stats = ts.parse_trace_file(_write_fixture(tmp_path))
    # 3 rows share msg_A: counted once, synthetic excluded.
    assert stats["input_tokens"] == 100
    assert stats["output_tokens"] == 50
    assert stats["cache_read_input_tokens"] == 1000
    assert stats["cache_creation_input_tokens"] == 200
    assert stats["turns"] == 1  # one unique non-synthetic message id


def test_synthetic_excluded_from_cost_but_counted(tmp_path):
    stats = ts.parse_trace_file(_write_fixture(tmp_path))
    assert stats["synthetic_messages"] == 1
    # Cost equals the single Opus message priced once.
    p = ts.PRICING["opus"]
    expected = (
        100 * p["input"]
        + 50 * p["output"]
        + 1000 * p["cache_read"]
        + 200 * p["cache_write_5m"]
    ) / 1_000_000
    assert abs(stats["cost_usd"] - expected) < 1e-12


def test_repeated_bash_command_detected(tmp_path):
    stats = ts.parse_trace_file(_write_fixture(tmp_path))
    assert stats["max_bash_repeat"] == 2
    assert stats["tool_counts"]["Bash"] == 2


def test_malformed_line_counted_not_fatal(tmp_path):
    stats = ts.parse_trace_file(_write_fixture(tmp_path))
    assert stats["skipped_lines"] == 1


def test_missing_message_or_usage_tolerated(tmp_path):
    f = tmp_path / "odd.jsonl"
    rows = [
        {"type": "user", "timestamp": "2026-06-09T10:00:00.000Z"},
        {"type": "assistant", "timestamp": "2026-06-09T10:00:01.000Z", "message": {}},
        {"type": "file-history-snapshot"},
    ]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    stats = ts.parse_trace_file(f)
    assert stats["skipped_lines"] == 0
    assert stats["turns"] == 0


def test_per_message_pricing_uses_each_models_rate(tmp_path):
    f = tmp_path / "mixed.jsonl"
    rows = [
        _assistant_row("msg_O", "claude-opus-4-8", USAGE, {"type": "text", "text": "a"}),
        _assistant_row("msg_S", "claude-sonnet-4-6", USAGE, {"type": "text", "text": "b"}),
    ]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    stats = ts.parse_trace_file(f)

    def cost(p):
        return (
            100 * p["input"]
            + 50 * p["output"]
            + 1000 * p["cache_read"]
            + 200 * p["cache_write_5m"]
        ) / 1_000_000

    expected = cost(ts.PRICING["opus"]) + cost(ts.PRICING["sonnet"])
    assert abs(stats["cost_usd"] - expected) < 1e-12


def test_cache_write_split_with_only_1h_key(tmp_path):
    usage = dict(USAGE, cache_creation_input_tokens=300)
    usage["cache_creation"] = {"ephemeral_1h_input_tokens": 200}  # no 5m key
    f = tmp_path / "split.jsonl"
    row = _assistant_row("msg_H", "claude-opus-4-8", usage, {"type": "text", "text": "x"})
    f.write_text(json.dumps(row) + "\n")
    stats = ts.parse_trace_file(f)
    p = ts.PRICING["opus"]
    expected = (
        100 * p["input"]
        + 50 * p["output"]
        + 1000 * p["cache_read"]
        + 100 * p["cache_write_5m"]  # 300 total - 200 in the 1h bucket
        + 200 * p["cache_write_1h"]
    ) / 1_000_000
    assert abs(stats["cost_usd"] - expected) < 1e-12


def test_unknown_model_flagged_not_priced(tmp_path):
    f = tmp_path / "unk.jsonl"
    row = _assistant_row("msg_U", "future-model-9", USAGE, {"type": "text", "text": "x"})
    f.write_text(json.dumps(row) + "\n")
    stats = ts.parse_trace_file(f)
    assert stats["unknown_model_messages"] == 1
    assert stats["cost_usd"] == 0


def test_worktree_suffix_stripped():
    assert (
        ts.strip_worktree("-home-haduong--claude--claude-worktrees-explore-foo")
        == "-home-haduong--claude"
    )
    assert ts.strip_worktree("-home-haduong--claude") == "-home-haduong--claude"


def test_cli_flags_present():
    src = (SCRIPTS / "trace-stats.py").read_text()
    for flag in ("--projects-dir", "--days", "--output", "--json"):
        assert flag in src, f"missing CLI flag {flag}"
    assert "ArgumentParser" in src


# --- ticket 0243 detector columns (H10/H11/H13) ---


def _tool_row(msg_id, name, tool_input, ts_str="2026-06-09T10:00:00.000Z"):
    block = {"type": "tool_use", "id": f"{msg_id}_tu", "name": name, "input": tool_input}
    return _assistant_row(msg_id, "claude-opus-4-8", USAGE, block, ts_str=ts_str)


def _result_row(text):
    return {
        "type": "user",
        "timestamp": "2026-06-09T10:02:00.000Z",
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "x", "content": text}],
        },
    }


def test_nav_and_idle_turns_classified(tmp_path):
    rows = [
        _tool_row("m1", "Bash", {"command": "cd /tmp"}),
        _tool_row("m2", "Bash", {"command": "git status"}),
        _tool_row("m3", "Bash", {"command": "uv run pytest -q"}),
        _assistant_row("m4", "claude-opus-4-8", USAGE, {"type": "text", "text": "thinking"}),
    ]
    f = tmp_path / "nav.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    stats = ts.parse_trace_file(f)
    assert stats["nav_turns"] == 2  # cd + git status
    assert stats["idle_turns"] == 1  # m4 has no tool_use
    assert stats["max_nav_run"] == 2  # m1,m2 consecutive


def test_merge_marker_turn_recorded(tmp_path):
    rows = [
        _tool_row("m1", "Bash", {"command": "gh pr view"}),
        _result_row("Merge queued; lands when required checks pass."),
        _tool_row("m2", "Bash", {"command": "git log"}),
    ]
    f = tmp_path / "merged.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    stats = ts.parse_trace_file(f)
    assert stats["merge_marker_turn"] == 1  # marker arrived after turn 1
    assert stats["turns"] == 2


def test_no_merge_marker_is_none(tmp_path):
    stats = ts.parse_trace_file(_write_fixture(tmp_path))
    assert stats["merge_marker_turn"] is None


def test_verify_gaze_skill_count(tmp_path):
    rows = [
        _tool_row("m1", "Skill", {"skill": "verify"}),
        _tool_row("m2", "Skill", {"skill": "gaze"}),
        _tool_row("m3", "Skill", {"skill": "celebrate"}),
    ]
    f = tmp_path / "vg.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    stats = ts.parse_trace_file(f)
    assert stats["verify_gaze_skills"] == 2


def test_new_csv_columns_declared():
    for col in (
        "nav_turns",
        "idle_turns",
        "max_nav_run",
        "merge_marker_turn",
        "verify_gaze_skills",
    ):
        assert col in ts.CSV_COLUMNS, f"missing CSV column {col}"


# --- ticket 0244 refined probes: disjoint turn buckets + join feedstock ---


def _merge_result_row(pr=370):
    return _result_row(f"PR #{pr}\nMerge queued; lands when required checks pass.")


def _cr_tool_row(msg_id, name, tool_input, cache_read):
    r = _tool_row(msg_id, name, tool_input)
    r["message"]["usage"] = dict(USAGE, cache_read_input_tokens=cache_read)
    return r


def _write_rows(tmp_path, rows, name="t.jsonl"):
    f = tmp_path / name
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return f


def test_last_marker_not_first(tmp_path):
    """Two merge markers: tail counts only turns after the LAST one."""
    rows = [
        _tool_row("m1", "Bash", {"command": "gh pr merge"}),
        _merge_result_row(101),
        _tool_row("m2", "Bash", {"command": "uv run pytest"}),
        _tool_row("m3", "Bash", {"command": "gh pr merge"}),
        _merge_result_row(102),
        _tool_row("m4", "Bash", {"command": "uv run pytest"}),
    ]
    stats = ts.parse_trace_file(_write_rows(tmp_path, rows))
    assert stats["merge_markers"] == 2
    assert stats["merge_marker_turn_last"] == 3
    assert stats["tail_turns"] == 1  # only m4
    assert stats["pr_numbers"] == [101, 102]


def test_bucket_cache_read_disjoint(tmp_path):
    """Each turn's cache_read lands in exactly ONE bucket: tail > vg > micro > core."""
    rows = [
        _cr_tool_row("m1", "Bash", {"command": "cd /tmp"}, 100),  # nav -> micro
        _cr_tool_row("m2", "Bash", {"command": "uv run pytest"}, 200),  # core
        _merge_result_row(),
        _cr_tool_row("m3", "Bash", {"command": "cd /x"}, 400),  # nav but after marker -> tail
        _cr_tool_row("m4", "Bash", {"command": "git log"}, 800),  # after marker -> tail
    ]
    stats = ts.parse_trace_file(_write_rows(tmp_path, rows))
    assert stats["bucket_tail_cr"] == 1200  # m3+m4
    assert stats["bucket_micro_cr"] == 100  # m1 only
    assert stats["bucket_vg_cr"] == 0
    total = stats["bucket_tail_cr"] + stats["bucket_vg_cr"] + stats["bucket_micro_cr"]
    assert total <= stats["cache_read_input_tokens"]


def test_final_idle_turn_excluded_from_micro(tmp_path):
    rows = [
        _tool_row("m1", "Bash", {"command": "uv run pytest"}),
        _assistant_row("m2", "claude-opus-4-8", USAGE, {"type": "text", "text": "answer"}),
    ]
    stats = ts.parse_trace_file(_write_rows(tmp_path, rows))
    assert stats["idle_turns"] == 1  # 0243 screening stat unchanged
    assert stats["bucket_micro_cr"] == 0  # final turn never billed to micro


def test_vg_bucket_after_second_invocation(tmp_path):
    rows = [
        _cr_tool_row("m1", "Skill", {"skill": "verify"}, 100),
        _cr_tool_row("m2", "Skill", {"skill": "gaze"}, 200),  # 2nd: later turns -> vg
        _cr_tool_row("m3", "Skill", {"skill": "celebrate"}, 400),
        _cr_tool_row("m4", "Skill", {"skill": "verify"}, 800),
    ]
    stats = ts.parse_trace_file(_write_rows(tmp_path, rows))
    assert stats["vg_second_turn"] == 2
    assert stats["bucket_vg_cr"] == 1200  # m3+m4


def test_mandated_tail_classification(tmp_path):
    rows = [
        _tool_row("m1", "Bash", {"command": "gh pr merge"}),
        _merge_result_row(),
        _tool_row("m2", "Write", {"file_path": "/home/u/.claude/projects/x/memory/note.md"}),
        _tool_row("m3", "Edit", {"file_path": "/home/u/repo/STATE.md"}),
        _tool_row("m4", "Edit", {"file_path": "/home/u/repo/src/feature.py"}),
    ]
    stats = ts.parse_trace_file(_write_rows(tmp_path, rows))
    assert stats["tail_turns"] == 3
    assert stats["tail_mandated_turns"] == 2  # memory + STATE, not feature.py


def test_first_turn_cache_write_and_excess_reads(tmp_path):
    rows = [
        _tool_row("m1", "Read", {"file_path": "/a.md"}),
        _tool_row("m2", "Read", {"file_path": "/a.md"}),
        _tool_row("m3", "Read", {"file_path": "/b.md"}),
    ]
    stats = ts.parse_trace_file(_write_rows(tmp_path, rows))
    assert stats["first_turn_cache_write"] == USAGE["cache_creation_input_tokens"]
    assert stats["excess_file_reads"] == 1  # /a.md read twice


def test_bucket_csv_columns_declared():
    for col in (
        "merge_markers",
        "merge_marker_turn_last",
        "tail_turns",
        "tail_mandated_turns",
        "bucket_tail_cr",
        "bucket_vg_cr",
        "bucket_micro_cr",
        "vg_second_turn",
        "first_turn_cache_write",
        "excess_file_reads",
        "pr_numbers",
    ):
        assert col in ts.CSV_COLUMNS, f"missing CSV column {col}"
