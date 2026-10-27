"""Tests for scripts/trace-stopguard.py: bad stops measured from Claude Code traces."""

import importlib.util
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("trace_stopguard", SCRIPTS / "trace-stopguard.py")
sg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sg)

T0 = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)  # a Tuesday, ISO week 43


def _t(sec):
    return (T0 + timedelta(seconds=sec)).isoformat().replace("+00:00", "Z")


def _use(tid, name, sec, **inp):
    block = {"type": "tool_use", "id": tid, "name": name, "input": inp}
    return {"type": "assistant", "timestamp": _t(sec), "message": {"content": [block], "stop_reason": "tool_use"}}


def _res(tid, sec, content="Async agent launched successfully.", error=False):
    block = {"type": "tool_result", "tool_use_id": tid, "content": content, "is_error": error}
    return {"type": "user", "timestamp": _t(sec), "message": {"content": [block]}}


def _human(sec, text="go"):
    return {"type": "user", "timestamp": _t(sec), "origin": {"kind": "human"}, "message": {"content": text}}


def _note(sec, tid):
    text = f"<task-notification>\n<tool-use-id>{tid}</tool-use-id>\n<status>completed</status>\n</task-notification>"
    return {"type": "user", "timestamp": _t(sec), "origin": {"kind": "task-notification"}, "message": {"content": text}}


def _end(sec, text):
    return {"type": "assistant", "timestamp": _t(sec),
            "message": {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"}}


def _stop(sec, pending=None):
    rec = {"type": "system", "subtype": "turn_duration", "timestamp": _t(sec)}
    if pending is not None:
        rec["pendingBackgroundAgentCount"] = pending
    return rec


def _turns(*recs):
    return sg.stops(sg.Trace(Path("s.jsonl"), list(recs)))


def test_ask_up_flags_question_without_advisor():
    found = _turns(
        _human(0), _use("a", "Agent", 1, prompt="advise: A or B?"), _res("a", 2), _end(3, "Advisor prefers A.\n\nWhich one?"), _stop(4),
        _human(10), _end(11, "Two options remain.\n\nWhich one?"), _stop(12),
    )
    assert [f["ask_without_ask_up"] for f in found] == [False, True]


def test_worker_spawn_is_not_an_ask_up():
    found = _turns(
        _human(0), _use("w", "Agent", 1, description="Execute ticket 12", prompt="Raid wave 2"), _res("w", 2),
        _end(3, "Coder launched. Which ticket next?"), _stop(4, pending=1),
        _human(10), _use("f", "Agent", 11, description="Pick", model="fable", prompt="A or B"), _res("f", 12),
        _end(13, "Which ticket next?"), _stop(14),
    )
    assert [f["ask_without_ask_up"] for f in found] == [True, False]


def test_question_in_code_fence_and_mid_message_not_flagged():
    found = _turns(
        _human(0), _end(1, "Is it set?\n\nIt is: done."), _stop(2),
        _human(10), _end(11, "Run this:\n```\nread -p 'continue?'\n```"), _stop(12),
        _human(20), _end(21, "Ready to proceed?**"), _stop(22),
    )
    assert [f["ask_without_ask_up"] for f in found] == [False, False, True]


def test_authors_call_question_is_excluded():
    found = _turns(
        _human(0), _end(1, "The branch is ready. Shall I merge and push it?"), _stop(2),
        _human(10), _end(11, "Je dépose les enfants, je pousse et j'ouvre la PR ?"), _stop(12),
    )
    assert [f["ask_without_ask_up"] for f in found] == [False, False]
    assert all(f["authors_call"] for f in found)


def test_wait_flagged_only_without_pending_background_task():
    pending = _turns(
        _human(0), _use("b", "Bash", 1, command="make check", run_in_background=True), _res("b", 2),
        _end(3, "Waiting for the gate to finish."), _stop(4),
    )
    woken = _turns(
        _human(0), _use("b", "Bash", 1, command="make check", run_in_background=True), _res("b", 2),
        _end(3, "Started."), _stop(4),
        _note(50, "b"), _end(51, "Gate passed. Waiting for CI on the PR."), _stop(52),
    )
    assert pending[0]["wait_without_wake"] is False
    assert [f["wait_without_wake"] for f in woken] == [False, True]


def test_wait_uses_runtime_pending_agent_count():
    found = _turns(
        _human(0), _end(1, "The coder is on it; I'll merge when the coder's PR lands."), _stop(2, pending=1),
        _human(10), _end(11, "I'll merge when the coder's PR lands."), _stop(12),
    )
    assert [f["wait_without_wake"] for f in found] == [False, True]


def test_absent_pending_key_falls_back_to_tracked_launches():
    found = _turns(
        _human(0), _use("a", "Agent", 1, description="Review PR 9"), _res("a", 2),
        _end(3, "When the review arrives I'll merge."), _stop(4),
        _note(30, "a"), _end(31, "Merged. I'll merge the next when CI passes."), _stop(32),
        _human(40), _use("w", "Workflow", 41, script="x"), _res("w", 42), _end(43, "I'll report when it completes."), _stop(44),
    )
    assert [f["wait_without_wake"] for f in found] == [False, True, False]


def test_waiting_for_the_author_is_not_a_wait():
    found = _turns(_human(0), _end(1, "Waiting for your go."), _stop(2))
    assert found[0]["wait_without_wake"] is False


def test_turn_ended_by_interrupt_is_not_a_stop():
    found = _turns(
        _human(0), _use("x", "Bash", 1, command="ls"),
        _human(5, "[Request interrupted by user]"), _end(6, "Which one?"), _stop(7),
    )
    assert len(found) == 1 and found[0]["turn"] == 2


def test_weekly_counts_and_g1(tmp_path):
    sess = tmp_path / "proj" / "s1.jsonl"
    rows = [_human(0), _end(1, "Which one?"), _stop(2), _human(10), _end(11, "Done."), _stop(12)]
    sess.parent.mkdir(parents=True)
    sess.write_text("".join(json.dumps(r) + "\n" for r in rows))
    sub = tmp_path / "proj" / "s1" / "subagents" / "agent-a.jsonl"
    sub.parent.mkdir(parents=True)
    sub.write_text("".join(json.dumps(r) + "\n" for r in rows))  # sub-agents are not the author's stops
    for p in (sess, sub):
        os.utime(p, (time.time(), time.time()))
    since = datetime.now(timezone.utc) - timedelta(days=1)
    rep = sg.report(sg.load_traces(tmp_path, since), T0 - timedelta(days=1))
    week = rep["runtimes"]["claude-code"]["weeks"]["2026-W43"]
    assert week == {"stops": 2, "ask_without_ask_up": 1, "wait_without_wake": 0, "bad": 1}
    assert rep["g1"]["threshold_per_week"] == 5 and rep["g1"]["verdict"] == "below"
    assert rep["runtimes"]["codex"] == "unmeasured"


def test_wait_ending_on_a_question_is_an_ask_and_old_paragraphs_are_ignored():
    found = _turns(
        _human(0), _end(1, "Waiting for CI.\n\nCI passed, PR merged.\n\nAll done.\n\nNothing left."), _stop(2),
        _human(10), _end(11, "I'll merge once CI passes. Is the scope right?"), _stop(12),
    )
    assert [f["wait_without_wake"] for f in found] == [False, False]
    assert found[1]["ask_without_ask_up"] is False  # "scope" is the author's call


def test_replayed_stop_in_a_forked_session_counts_once(tmp_path):
    end = _end(1, "Which one?")
    end["message"]["id"] = "msg_1"
    for name in ("s1", "s2"):
        p = tmp_path / "proj" / f"{name}.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r) + "\n" for r in [_human(0, "go " * 200), end, _stop(2)]))
    since = datetime.now(timezone.utc) - timedelta(days=1)
    rep = sg.report(sg.load_traces(tmp_path, since), T0 - timedelta(days=1))
    assert rep["runtimes"]["claude-code"]["weeks"]["2026-W43"]["stops"] == 1


def test_g1_verdict_at_or_above_threshold():
    rows = []
    for i in range(6):
        rows += [_human(10 * i, "go " * 50), _end(10 * i + 1, "Which one?"), _stop(10 * i + 2)]
    tr = sg.Trace(Path("s.jsonl"), rows)
    rep = sg.report([tr], T0 - timedelta(days=1), now=T0 + timedelta(days=6))
    assert rep["g1"]["bad_per_week"] == 6.0 and rep["g1"]["verdict"] == "at_or_above"


def test_foreground_agent_result_clears_it_and_failed_advisor_is_no_ask_up():
    found = _turns(
        _human(0), _use("a", "Agent", 1, description="Review PR 9"), _res("a", 2, content="Review: clean."),
        _end(3, "Review clean. I'll merge once CI passes."), _stop(4),
        _human(10), _use("f", "Agent", 11, model="fable", prompt="A or B"), _res("f", 12, content="boom", error=True),
        _end(13, "Which one?"), _stop(14),
    )
    assert [f["wait_without_wake"] for f in found] == [True, False]
    assert [f["ask_without_ask_up"] for f in found] == [False, True]
