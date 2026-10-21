"""Tests for scripts/trace-friction.py (ticket 1169): daily friction series."""

import importlib.util
import json
import os
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "trace_friction", SCRIPTS / "trace-friction.py"
)
tf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tf)

DAY1 = "2026-10-14"
DAY2 = "2026-10-15"


def _use(tid, name, ts, **inp):
    block = {"type": "tool_use", "id": tid, "name": name, "input": inp}
    return {"type": "assistant", "timestamp": ts, "message": {"content": [block]}}


def _res(tid, ts, text, error=True):
    block = {
        "type": "tool_result",
        "tool_use_id": tid,
        "content": text,
        "is_error": error,
    }
    return {"type": "user", "timestamp": ts, "message": {"content": [block]}}


def _fixture_rows():
    t = f"{DAY1}T10:00:0"
    return [
        # positive controls, one per error class
        _use("g1", "Bash", t + "0Z", command="git -C /x status"),
        _res("g1", t + "1Z", "This git form is too complex to verify"),
        _use("n1", "Skill", t + "2Z"),
        _res("n1", t + "3Z", "Error: No such tool available: Skill"),
        _use("w1", "Write", t + "4Z", file_path="/home/x/f"),
        _res(
            "w1",
            t + "5Z",
            "<tool_use_error>Edit the worktree copy of this file instead",
        ),
        _use("o1", "Bash", t + "6Z", command="false"),
        _res("o1", t + "7Z", "Exit code 1"),
        # slow successful wait command: 60 s, next day
        _use("s1", "Bash", f"{DAY2}T09:00:00Z", command="sleep 60"),
        _res("s1", f"{DAY2}T09:01:00Z", "ok", error=False),
        # plain fast success
        _use("f1", "Bash", f"{DAY2}T09:02:00Z", command="ls"),
        _res("f1", f"{DAY2}T09:02:01Z", "a", error=False),
    ]


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n")


def _scan(tmp_path, rows):
    _write(tmp_path / "proj" / "sess.jsonl", rows)
    now = tf.datetime(2026, 10, 21, tzinfo=tf.timezone.utc)
    # fixture file mtime is "now"; pin the window to the fixture dates
    os.utime(tmp_path / "proj" / "sess.jsonl", (now.timestamp(), now.timestamp()))
    return tf.run_scan(tmp_path, 28, now=now)


def test_each_error_class_counted(tmp_path):
    s = _scan(tmp_path, _fixture_rows())
    day = next(d for d in s["daily"] if d["date"] == DAY1)
    assert day["errors"] == 4
    assert day["errors_by_cause"] == {
        "worktree_guard": 1,
        "no_such_tool": 1,
        "write_outside_worktree": 1,
        "other": 1,
    }
    assert s["skipped_lines"] == 1


def test_real_write_guard_wordings_classified():
    for text in (
        "PreToolUse:Write hook error: BLOCKED: Worktree path guard: 'x' resolves to the main repo",
        "This background session hasn't isolated its changes yet. Call EnterWorktree first",
    ):
        assert tf.classify_error("Write", text) == "write_outside_worktree"
    assert tf.classify_error("Bash", "BLOCKED: Worktree path guard") == "worktree_guard"
    assert tf.classify_error("Write", "File has not been read yet") == "other"


def test_isolation_hook_wordings_classified():
    wt = "/home/u/.claude/worktrees/t1"
    sess = f"This session is isolated in the worktree {wt} but this command "
    agent = f"This agent is isolated in the worktree {wt} but this command "
    write = f"This session is isolated in the worktree {wt} so its writes are limited to the worktree"
    assert tf.classify_error("Bash", sess + "names git in a form too complex") == (
        "worktree_guard"
    )
    assert tf.classify_error("Bash", agent + "runs sed with a value computed") == (
        "worktree_guard"
    )
    assert tf.classify_error("Write", write) == "write_outside_worktree"
    assert tf.classify_error("Bash", write) == "worktree_guard"


def test_daily_series_shows_class_stopping(tmp_path):
    s = _scan(tmp_path, _fixture_rows())
    day2 = next(d for d in s["daily"] if d["date"] == DAY2)
    assert day2["errors"] == 0
    assert day2["errors_by_cause"]["worktree_guard"] == 0
    assert [d["date"] for d in s["daily"]] == [DAY1, DAY2]


def test_slow_tail_and_wait_counted_as_upper_bound(tmp_path):
    s = _scan(tmp_path, _fixture_rows())
    assert s["totals"]["slow_calls"] == 1
    assert s["slow_by_tool_hours_upper_bound"][0]["tool"] == "Bash"
    assert s["totals"]["wait_commands"] == 1
    assert "upper bound" in s["duration_note"]


def test_wait_regex_positive_and_negative():
    for cmd in (
        "sleep 5",
        "gh run watch 12",
        "gh pr checks 3 --watch",
        "x; until true; do :; done",
        "while ! x; do sleep 5; done",
        "if a; then sleep 2; fi",
        "for i in 1 2; do sleep 3; done",
        "timeout 9 sleep 5",
    ):
        assert tf.is_wait_command(cmd), cmd
    assert not tf.is_wait_command("echo asleep and untilled")


def test_dangling_symlink_tolerated(tmp_path):
    _write(tmp_path / "proj" / "sess.jsonl", _fixture_rows())
    (tmp_path / "proj" / "dead.jsonl").symlink_to(tmp_path / "missing.jsonl")
    sub = tmp_path / "proj" / "sess" / "subagents"
    _write(sub / "agent-1.jsonl", [])
    s = tf.run_scan(tmp_path, 28)
    assert s["files"] == 2


def test_duplicate_tool_use_ids_counted_once(tmp_path):
    rows = _fixture_rows()
    _write(tmp_path / "proj" / "a.jsonl", rows)
    _write(tmp_path / "proj" / "b.jsonl", rows)
    now = tf.datetime(2026, 10, 21, tzinfo=tf.timezone.utc)
    for n in ("a", "b"):
        p = tmp_path / "proj" / f"{n}.jsonl"
        os.utime(p, (now.timestamp(), now.timestamp()))
    s = tf.run_scan(tmp_path, 28, now=now)
    assert s["totals"]["errors"] == 4


def test_naive_timestamp_counted_as_utc(tmp_path):
    rows = [
        _use("x1", "Bash", f"{DAY1}T10:00:00", command="false"),
        _res("x1", f"{DAY1}T10:00:01", "Exit code 1"),
    ]
    s = _scan(tmp_path, rows)
    assert s["totals"]["errors"] == 1
