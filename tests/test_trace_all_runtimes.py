"""Ticket 1517: trace-stats, trace-friction and trace-wall-time read every runtime's corpus.

Synthetic fixtures only: one Claude Code session, one Codex rollout and one Pi session, each in its
own root; the Pi spool root is absent, so it must come out as `could not look` while the others are
counted under their runtime. A measure a runtime cannot supply must be `not measured`, never 0.
"""

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ts = _load("trace_stats_1517", "trace-stats.py")
tf = _load("trace_friction_1517", "trace-friction.py")
tw = _load("trace_wall_time_1517", "trace-wall-time.py")

NOW = datetime.now(timezone.utc).replace(microsecond=0)
T0 = NOW - timedelta(hours=2)


def _t(sec):
    return (T0 + timedelta(seconds=sec)).isoformat().replace("+00:00", "Z")


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows) + "not json\n")


def _claude_rows():
    usage = {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 1000,
             "cache_creation_input_tokens": 200}
    use = {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "sleep 45"}}
    return [
        {"type": "user", "timestamp": _t(0), "message": {"content": "<command-name>/raid</command-name>"}},
        {"type": "assistant", "timestamp": _t(5),
         "message": {"id": "msg_1", "model": "claude-opus-4-8", "usage": usage, "content": [use]}},
        {"type": "user", "timestamp": _t(50),
         "message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "ok",
                                  "is_error": False}]}},
        {"type": "assistant", "timestamp": _t(60),
         "message": {"id": "msg_2", "model": "claude-opus-4-8", "usage": usage,
                     "content": [{"type": "text", "text": "done"}]}},
    ]


def _codex_call(cid, sec, cmd):
    return {"timestamp": _t(sec), "type": "response_item",
            "payload": {"type": "function_call", "name": "exec_command", "call_id": cid,
                        "arguments": json.dumps({"cmd": cmd})}}


def _codex_out(cid, sec, text):
    return {"timestamp": _t(sec), "type": "response_item",
            "payload": {"type": "function_call_output", "call_id": cid, "output": text}}


def _codex_rows(model="codex-auto-review"):
    return [
        {"timestamp": _t(0), "type": "session_meta", "payload": {"id": "cx-1", "source": "exec", "cwd": "/w"}},
        {"timestamp": _t(0), "type": "turn_context", "payload": {"model": model, "turn_id": "t1"}},
        _codex_call("c1", 1, "sleep 60"),
        _codex_out("c1", 62, "Process exited with code 0"),
        _codex_call("c2", 63, "false"),
        _codex_out("c2", 64, "Process exited with code 1"),
        _codex_call("c2b", 64, "false"),  # the same failing command again: a repeat_failing folly
        _codex_out("c2b", 64, "Process exited with code 1"),
        _codex_call("c3", 65, "ls"),
        _codex_out("c3", 66, "a b"),  # no exit code recorded: outcome unknown
        {"timestamp": _t(67), "type": "response_item",  # the `exec` script tool, its output a block list
         "payload": {"type": "custom_tool_call", "name": "exec", "call_id": "c4",
                     "input": 'await tools.exec_command({cmd: "make check"})'}},
        {"timestamp": _t(68), "type": "response_item",
         "payload": {"type": "custom_tool_call_output", "call_id": "c4",
                     "output": [{"type": "input_text", "text": "Script failed\nWall time 1 s"}]}},
        {"timestamp": _t(70), "type": "event_msg",
         "payload": {"type": "token_count",
                     "info": {"total_token_usage": {"input_tokens": 1000, "cached_input_tokens": 400,
                                                    "output_tokens": 50}}}},
    ]


def _pi_rows():
    usage = {"input": 10, "output": 5, "cacheRead": 0, "cacheWrite": 0, "cost": {"total": 0.002}}
    call = {"type": "toolCall", "id": "p1", "name": "bash", "arguments": {"command": "sleep 40"}}
    return [
        {"type": "session", "id": "pi-1", "timestamp": _t(0), "cwd": "/w"},
        {"type": "message", "id": "m1", "timestamp": _t(1),
         "message": {"role": "assistant", "model": "local-x", "usage": usage, "content": [call]}},
        {"type": "message", "id": "m2", "timestamp": _t(41),
         "message": {"role": "toolResult", "toolCallId": "p1", "isError": False, "durationMs": 40000,
                     "content": [{"type": "text", "text": "ok"}]}},
    ]


def _roots(tmp_path, codex_model="codex-auto-review"):
    claude = tmp_path / "claude" / "projects"
    _write(claude / "-w" / "sess-1.jsonl", _claude_rows())
    codex = tmp_path / "codex"
    _write(codex / "sessions" / "2026" / "11" / "10" / "rollout-x.jsonl", _codex_rows(codex_model))
    pi = tmp_path / "pi" / "sessions"
    _write(pi / "--w--" / "s.jsonl", _pi_rows())
    return {"Claude Code": claude, "Codex": codex, "Pi": pi, "Pi spool": tmp_path / "absent-spool"}


def _by_name(entries):
    return {e["name"]: e for e in entries}


# ---- trace-stats ------------------------------------------------------------------------------


def test_stats_counts_each_runtime_and_reports_the_absent_spool(tmp_path):
    rows, meta = ts.run_census(_roots(tmp_path, codex_model="gpt-6-sol"), 28)
    summary = ts.summarize(rows, meta, 28)
    rt = _by_name(summary["runtimes"])
    assert rt["Claude Code"]["status"] == "read" and rt["Claude Code"]["agents"] == 1
    assert rt["Codex"]["status"] == "read"
    assert rt["Codex"]["sessions"] == 1 and rt["Codex"]["turns"] == 1
    assert rt["Codex"]["tokens"] == {"input": 600, "output": 50, "cache_read": 400, "cache_write": 0}
    assert rt["Codex"]["cost_usd"] > 0 and rt["Codex"]["unpriced_turns"] == 0
    assert rt["Pi"]["status"] == "read" and rt["Pi"]["turns"] == 1
    assert rt["Pi"]["cost_usd"] == 0.002 and rt["Pi"]["cost_source"] == "pi-recorded"
    assert rt["Pi spool"]["status"] == "could not look"
    assert summary["runtimes_read"] == ["Claude Code", "Codex", "Pi"]
    assert summary["runtimes_not_read"] == ["Pi spool"]
    # the census CSV and its totals stay Claude Code's: trace-hypotheses reads them
    assert len(rows) == 1 and summary["totals_scope"] == ["Claude Code"]


def test_stats_marks_unpriced_and_claude_only_measures_not_measured(tmp_path):
    rows, meta = ts.run_census(_roots(tmp_path), 28)
    codex = _by_name(meta["runtimes"])["Codex"]
    assert codex["cost_usd"] is None and codex["unpriced_turns"] == 1  # cost unknown, never 0
    assert "synthetic_messages" in codex["not_measured"]
    assert "synthetic_messages" not in (_by_name(meta["runtimes"])["Claude Code"].get("not_measured") or {})


def test_stats_bare_path_reads_claude_code_only(tmp_path):
    roots = _roots(tmp_path)
    rows, meta = ts.run_census(roots["Claude Code"], 28)
    rt = _by_name(meta["runtimes"])
    assert rt["Claude Code"]["status"] == "read" and len(rows) == 1
    assert rt["Codex"]["status"] == "not read"


# ---- trace-friction ---------------------------------------------------------------------------


def test_friction_counts_each_runtime_and_reports_the_absent_spool(tmp_path):
    s = tf.run_scan(_roots(tmp_path), 28, now=NOW)
    rt = _by_name(s["runtimes"])
    assert rt["Claude Code"]["status"] == "read" and rt["Claude Code"]["calls"] == 1
    assert rt["Codex"]["status"] == "read" and rt["Codex"]["calls"] == 5
    assert rt["Pi"]["status"] == "read" and rt["Pi"]["calls"] == 1
    assert rt["Pi spool"]["status"] == "could not look"
    assert s["totals"]["calls"] == 7  # every runtime read is in the series
    assert rt["Codex"]["errors"] == 3 and rt["Codex"]["slow_calls"] == 1
    assert rt["Codex"]["bash_calls"] == 5
    assert rt["Codex"]["wait_commands"] == 1
    assert s["follies"]["repeat_failing"]["runtime"] == {"codex": 1}


def test_friction_codex_call_without_exit_code_is_not_measured_not_a_success(tmp_path):
    s = tf.run_scan(_roots(tmp_path), 28, now=NOW)
    codex = _by_name(s["runtimes"])["Codex"]
    assert codex["calls_outcome_unknown"] == 1
    assert any("outcome" in k for k in codex["not_measured"])
    assert s["totals"]["calls_outcome_unknown"] == 1


def test_friction_codex_exec_script_outcome_is_read_from_its_markers():
    assert tf.codex_outcome("Script failed\nWall time 1 s") is True
    assert tf.codex_outcome("Script completed\nWall time 1 s") is False
    assert tf.codex_outcome('Script completed\n{"exit_code": 2}') is True  # an inner command failed
    assert tf.codex_outcome('Script completed\n{"exit_code": 0}') is False
    assert tf.codex_outcome("Process exited with code 1") is True
    assert tf.codex_outcome("a b") is None
    assert tf.codex_outcome("Process exited with code 0\nsee exit code 2 in the log") is False  # prose, not a record


def test_friction_bare_path_reads_claude_code_only(tmp_path):
    roots = _roots(tmp_path)
    s = tf.run_scan(roots["Claude Code"], 28, now=NOW)
    assert s["totals"]["calls"] == 1
    assert _by_name(s["runtimes"])["Pi"]["status"] == "not read"


# ---- trace-wall-time --------------------------------------------------------------------------


def test_wall_time_reads_each_runtime_and_marks_skill_runs_not_measured(tmp_path):
    since = NOW - timedelta(days=1)
    r = tw.survey_runtimes(_roots(tmp_path), since)
    rt = _by_name(r["runtimes"])
    assert r["raid"]["runs"] == 1  # the Claude Code run is decomposed as before
    assert rt["Claude Code"]["status"] == "read"
    for name in ("Codex", "Pi"):
        assert rt[name]["status"] == "read" and rt[name]["sessions_in_window"] == 1
        assert rt[name]["not_measured"]  # raid, hunt and gaze runs: no record marks them there
    assert rt["Pi spool"]["status"] == "could not look"
    assert r["runtimes_not_read"] == ["Pi spool"]


def test_wall_time_absent_claude_corpus_is_could_not_look(tmp_path):
    roots = _roots(tmp_path)
    roots["Claude Code"] = tmp_path / "nowhere"
    r = tw.survey_runtimes(roots, NOW - timedelta(days=1))
    assert _by_name(r["runtimes"])["Claude Code"]["status"] == "could not look"
    assert r["raid"]["runs"] == 0 and "Codex" in r["runtimes_read"]
