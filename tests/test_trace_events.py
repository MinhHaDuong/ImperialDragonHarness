"""Tests for scripts/trace_events.py: one event model over Claude Code, Codex and Pi transcripts (ticket 1385).

Fixtures are hand-written rows, not excerpts of real transcripts.
"""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


te = _load("trace_events_under_test", "trace_events.py")


def lines(*rows):
    return [json.dumps(r) for r in rows]


def by_kind(events, kind):
    return [e for e in events if e.kind == kind]


# ---- Codex -----------------------------------------------------------------------------------------

def _codex_rows(model="gpt-6-luna"):
    def count(ts, inp, cached, out):
        total = {"input_tokens": inp, "cached_input_tokens": cached, "cache_write_input_tokens": 0,
                 "output_tokens": out}
        return {"timestamp": ts, "type": "event_msg", "payload": {"type": "token_count",
                "info": {"total_token_usage": total, "last_token_usage": total}}}

    return [
        {"timestamp": "2026-01-01T00:00:00Z", "type": "session_meta", "payload": {"id": "cx-1"}},
        {"timestamp": "2026-01-01T00:00:01Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "t1"}},
        {"timestamp": "2026-01-01T00:00:01Z", "type": "turn_context", "payload": {"model": model, "turn_id": "t1"}},
        {"timestamp": "2026-01-01T00:00:02Z", "type": "response_item", "payload": {
            "type": "custom_tool_call", "call_id": "call_a", "name": "exec", "input": "ls"}},
        {"timestamp": "2026-01-01T00:00:04Z", "type": "response_item", "payload": {
            "type": "custom_tool_call_output", "call_id": "call_a",
            "output": [{"type": "input_text", "text": "Process exited with code 3"}]}},
        count("2026-01-01T00:00:05Z", 100, 40, 10),
        {"timestamp": "2026-01-01T00:00:06Z", "type": "event_msg", "payload": {"type": "token_count", "info": None}},
        count("2026-01-01T00:00:08Z", 250, 100, 30),
        count("2026-01-01T00:00:10Z", 400, 190, 60),
    ]


def test_codex_token_deltas_and_pointer():
    events = te.read_codex(lines(*_codex_rows()), "2026/01/01/rollout-x-cx-1.jsonl")
    turns = by_kind(events, "turn")
    assert [t.tokens["input"] + t.tokens["cache_read"] for t in turns] == [100, 150, 150]
    assert [t.tokens["output"] for t in turns] == [10, 20, 30]
    assert [t.tokens["cache_read"] for t in turns] == [40, 60, 90]
    assert turns[1].start == turns[0].end  # a turn begins where the previous one ended
    tool = by_kind(events, "tool")[0]
    assert (tool.name, tool.exit) == ("exec", 3)
    assert tool.pointer == ("2026/01/01/rollout-x-cx-1.jsonl", "call_a")
    assert tool.end - tool.start == 2.0
    assert events[0].kind == "agent" and events[0].agent == "cx-1"


def test_codex_counter_reset_takes_the_new_total():
    rows = _codex_rows()
    rows.append({"timestamp": "2026-01-01T00:00:12Z", "type": "event_msg", "payload": {
        "type": "token_count", "info": {"total_token_usage": {"input_tokens": 50, "output_tokens": 5}}}})
    last = by_kind(te.read_codex(lines(*rows), "f"), "turn")[-1]
    assert (last.tokens["input"], last.tokens["output"]) == (50, 5)


def test_codex_priced_model_carries_shadow_usd():
    turns = by_kind(te.read_codex(lines(*_codex_rows("gpt-6-luna")), "f"), "turn")
    first = turns[0]  # 60 uncached in, 40 cached, 10 out at 0.1 / 0.01 / 0.5 per MTok
    assert first.cost_source == "price-table"
    assert abs(first.shadow_usd - (60 * 0.1 + 40 * 0.01 + 10 * 0.5) / 1e6) < 1e-12
    assert te.read_codex(lines(*_codex_rows("openai/gpt-6-luna")), "f")[1].shadow_usd == first.shadow_usd


def test_codex_unpriced_model_is_none_never_zero():
    events = te.read_codex(lines(*_codex_rows("codex-auto-review")), "f")
    for event in by_kind(events, "turn") + [events[0]]:
        assert event.shadow_usd is None and event.cost_source == "unpriced"
    assert te.openai_cost("gpt-nope-9", {"input": 5}) is None


# ---- Claude Code -----------------------------------------------------------------------------------

def _claude_rows():
    usage = {"input_tokens": 10, "output_tokens": 20, "cache_read_input_tokens": 100,
             "cache_creation_input_tokens": 1000, "cache_creation": {"ephemeral_1h_input_tokens": 0}}

    def assistant(ts, mid, blocks):
        return {"type": "assistant", "timestamp": ts, "sessionId": "s1", "message": {
            "id": mid, "model": "claude-sonnet-5-5", "usage": usage, "content": blocks}}

    return [
        {"type": "user", "timestamp": "2026-01-01T00:00:00.000Z", "sessionId": "s1", "message": {"content": "hi"}},
        assistant("2026-01-01T00:00:02.000Z", "m1", [{"type": "text", "text": "x"}]),
        assistant("2026-01-01T00:00:02.100Z", "m1", [{"type": "tool_use", "id": "tu1", "name": "Bash", "input": {}}]),
        assistant("2026-01-01T00:00:02.200Z", "m1", [{"type": "tool_use", "id": "tu2", "name": "Agent", "input": {}}]),
        {"type": "user", "timestamp": "2026-01-01T00:00:05.000Z", "sessionId": "s1", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "tu1", "content": "ok"},
            {"type": "tool_result", "tool_use_id": "tu2", "content": "launched in the background"}]}},
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-01-01T00:01:00.000Z",
         "content": "<task-notification><task-id>a9</task-id><tool-use-id>tu2</tool-use-id></task-notification>"},
        {"type": "user", "timestamp": "2026-01-01T00:01:01.000Z", "sessionId": "s1", "message": {"content": "next"}},
    ]


def test_claude_events_tokens_once_per_message_and_background_end():
    events = te.read_claude(lines(*_claude_rows()), "proj/s1.jsonl")
    turns = by_kind(events, "turn")
    assert len(turns) == 1  # three rows repeat one message.id
    assert turns[0].tokens == {"input": 10, "output": 20, "cache_read": 100, "cache_write": 1000}
    assert turns[0].pointer == ("proj/s1.jsonl", "m1")
    assert abs(turns[0].shadow_usd - (10 * 3 + 20 * 15 + 100 * 0.3 + 1000 * 3.75) / 1e6) < 1e-12
    tools = {t.pointer[1]: t for t in by_kind(events, "tool")}
    assert tools["tu1"].end - tools["tu1"].start == pytest.approx(2.9)
    assert tools["tu2"].end - tools["tu2"].start == pytest.approx(57.8)  # ends at the completion notification
    assert tools["tu1"].exit == 0
    assert events[0].agent == "s1" and events[0].tokens["output"] == 20


def test_claude_synthetic_message_is_not_a_turn():
    rows = _claude_rows()
    rows[1]["message"]["model"] = "<synthetic>"
    rows[1]["message"]["id"] = "syn"
    assert [t.pointer[1] for t in by_kind(te.read_claude(lines(*rows), "f"), "turn")] == ["m1"]


def test_claude_malformed_line_is_skipped():
    assert te.read_claude(["not json", *lines(*_claude_rows())], "f")[0].kind == "agent"


# ---- Pi, aider -------------------------------------------------------------------------------------

def _pi_rows(cost=0):
    usage = {"input": 5, "output": 2, "cacheRead": 1, "cacheWrite": 0, "cost": {"total": cost}}
    return [
        {"type": "session", "id": "pi-1", "timestamp": "2026-01-01T00:00:00.000Z"},
        {"type": "model_change", "timestamp": "2026-01-01T00:00:00.100Z", "modelId": "local-model"},
        {"type": "message", "id": "e1", "timestamp": "2026-01-01T00:00:03.000Z", "message": {
            "role": "assistant", "model": "local-model", "usage": usage,
            "content": [{"type": "toolCall", "id": "call_p", "name": "read"}]}},
        {"type": "message", "id": "e2", "timestamp": "2026-01-01T00:00:04.000Z", "message": {
            "role": "toolResult", "toolCallId": "call_p", "content": []}},
    ]


def test_pi_tokens_pointer_and_recorded_cost():
    events = te.read_pi(lines(*_pi_rows()), "s/pi.jsonl")
    turn = by_kind(events, "turn")[0]
    assert turn.tokens == {"input": 5, "output": 2, "cache_read": 1, "cache_write": 0}
    assert turn.shadow_usd == 0.0 and turn.cost_source == "pi-recorded"  # recorded 0 stays 0
    tool = by_kind(events, "tool")[0]
    assert tool.pointer == ("s/pi.jsonl", "call_p") and tool.end - tool.start == 1.0
    assert events[0].agent == "pi-1" and events[0].cost_source == "pi-recorded"


def test_pi_without_cost_record_is_unpriced():
    rows = _pi_rows()
    del rows[2]["message"]["usage"]["cost"]
    assert by_kind(te.read_pi(lines(*rows), "f"), "turn")[0].shadow_usd is None


def test_opaque_runtime_is_file_only():
    (event,) = te.read_opaque("aider", "x/chat.md", 10.0, 20.0, "ai-1", "parent", "ai/aider")
    assert event.pointer == ("x/chat.md", None) and event.shadow_usd is None and event.tokens is None


# ---- price table -----------------------------------------------------------------------------------

def test_trace_stats_reexports_the_moved_table():
    spec = importlib.util.spec_from_file_location("trace_stats_for_events", SCRIPTS / "trace-stats.py")
    stats = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stats)
    assert set(stats.PRICING) == {"fable", "opus", "sonnet", "haiku"}
    assert all("cache_write_5m" in row for row in stats.PRICING.values())  # trace-hypotheses reads it
    assert stats.resolve_pricing("claude-opus-5") is stats.PRICING["opus"]
    assert stats.resolve_pricing("gpt-6-luna") is None
    assert stats._message_cost("gpt-6-luna", {"input_tokens": 9}) == 0.0


# ---- tool-call classes (ticket 1393) ---------------------------------------------------------------

@pytest.mark.parametrize("name,command,expected", [
    ("Skill", None, "subagent"), ("Agent", None, "subagent"),
    ("Read", None, "file"), ("Edit", None, "file"), ("Grep", None, "file"), ("apply_patch", None, "file"),
    ("Bash", "pytest tests/test_x.py -q", "tests"),
    ("Bash", "cd /w && uv run pytest -x", "tests"),
    ("Bash", "RUN=1 python3 -m pytest tests", "tests"),
    ("Bash", "rtk proxy python3 -m pytest tests", "tests"),
    ("Bash", "make check-fast", "tests"), ("Bash", "make -j4 lint", "tests"),
    ("Bash", "codex exec --model gpt-6-sol 'review this'", "worker"),
    ("Bash", "claude -p 'say OK' --model haiku", "worker"),
    ("Bash", "python3 scripts/seat_clock.py run -- codex exec x", "worker"),
    ("Bash", "pytest -q && codex exec go", "worker"),  # precedence: worker over tests
    ("Bash", "bash -lc 'make check'", "tests"),
    ("Bash", "git status", "git"), ("Bash", "ls -la", "file"), ("Bash", "", "other"),
    # negatives: a command that only mentions the words is not that class
    ("Bash", "grep -rn pytest tests/", "file"),
    ("Bash", "echo 'run pytest then codex exec'", "other"),
    ("Bash", "git commit -m 'fix pytest flake\n\nmake check passes'", "git"),
    ("Bash", "cat <<'EOF'\npytest\nEOF", "file"),
    ("Bash", "cat notes.md | grep 'make check'", "file"),
    ("WebFetch", None, "other"),
    # prefixes are looked through
    ("Bash", "IDH_ROOT=/x; P=/y; python3 -m pytest -q", "tests"),
    ("Bash", "export IDH_ROOT=/x && cat a.md", "file"),
    ("Bash", "timeout 110 make check-fast > log 2>&1", "tests"),
    ("Bash", "cd /w && git fetch -q && git log --oneline", "git"),
    ("Bash", "env FOO=1 nice -n 5 time grep -n x f", "file"),
    ("Bash", "${ERG:-tickets/erg} log 1393 'note'", "git"),
    ("Bash", "gh pr view 5", "git"), ("Bash", "tickets/erg close 3", "git"),
    ("Bash", "sed -n 1,5p f", "file"), ("Bash", "find . -name '*.py' | wc -l", "file"),
    ("Bash", "git diff | grep pytest", "git"),  # precedence: git over file
    ("Bash", "git status && codex exec go", "worker"),
    ("Bash", "echo done", "other"), ("Bash", "cd /w", "other"), ("Bash", "export A=1", "other"),
    ("Bash", "grep '|' pytest", "file"), ("Bash", "grep 'a;b' pytest", "file"),  # quoted separators
    ("Bash", "# run pytest later\nls", "file"), ("Bash", "# c\npytest -q", "tests"),  # comments
    ("Bash", "make check 2>&1 | tail -3", "tests"), ("Bash", "pytest &> out.log", "tests"),
])
def test_classify_tool(name, command, expected):
    assert te.classify_tool(name, command) == expected


def test_codex_exec_calls_are_classified_by_their_command():
    def row(ts, payload):
        return {"timestamp": ts, "type": "response_item", "payload": payload}

    def js(cmd):
        return 'text(await tools.exec_command({cmd:%s,"workdir":"/w"}));' % json.dumps(cmd)

    rows = [
        row("2026-01-01T00:00:01.000Z", {"type": "custom_tool_call", "name": "exec", "call_id": "c1", "input": js("pytest -q")}),
        row("2026-01-01T00:00:02.000Z", {"type": "custom_tool_call", "name": "exec", "call_id": "c2", "input": js("rg pytest docs")}),
        row("2026-01-01T00:00:03.000Z", {"type": "function_call", "name": "shell", "call_id": "c3",
                                         "arguments": json.dumps({"command": ["bash", "-lc", "codex exec x"]})}),
        row("2026-01-01T00:00:04.000Z", {"type": "function_call", "name": "spawn_agent", "call_id": "c4", "arguments": "{}"}),
        row("2026-01-01T00:00:05.000Z", {"type": "custom_tool_call", "name": "exec", "call_id": "c5",
                                         "input": "text(await tools.apply_patch(`*** Begin Patch`));"}),
        row("2026-01-01T00:00:07.000Z", {"type": "custom_tool_call", "name": "exec", "call_id": "c7",
                                         "input": 'text(await tools.exec_command({"cmd":"pytest -q","workdir":"/w"}));'}),
        row("2026-01-01T00:00:06.000Z", {"type": "local_shell_call", "call_id": "c6", "action": {"command": ["make", "check"]}}),
    ]
    tools = {t.pointer[1]: t.tool_class for t in by_kind(te.read_codex(lines(*rows), "f"), "tool")}
    assert tools == {"c1": "tests", "c2": "file", "c3": "worker", "c4": "subagent", "c5": "file", "c6": "tests", "c7": "tests"}


def test_claude_tool_class_comes_from_the_command_and_non_tools_have_none():
    rows = _claude_rows()
    rows[2]["message"]["content"][0]["input"] = {"command": "pytest -q", "description": "run tests"}
    events = te.read_claude(lines(*rows), "proj/s1.jsonl")
    tools = {t.pointer[1]: t.tool_class for t in by_kind(events, "tool")}
    assert tools == {"tu1": "tests", "tu2": "subagent"}
    assert events[0].tool_class is None and all(t.tool_class is None for t in by_kind(events, "turn"))
