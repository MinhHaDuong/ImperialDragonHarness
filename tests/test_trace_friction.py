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


# --- ticket 1217: follies, rung table, barrier denials, Pi reader -----------
# Specimens: conception/2026-10-26-self-matching-process-patterns-evidence.md.

SPEC_A = "until ! pgrep -u $USER -f 'padme-llm.py manifest' >/dev/null; do sleep 5; done; python3 x.py"
SPEC_B = "for p in $(pgrep -u $USER -f 'until ! pgrep -u'); do kill $p; done"
SPEC_C = "pkill -f 'bin/make|gmake|cicc|nvcc'"
SPEC_BRACKET = "until ! pgrep -f '[p]adme-llm.py manifest' >/dev/null; do sleep 5; done"
SPEC_ECHO = "echo 'pgrep -f x'"


def test_wait_regex_ignores_quoted_and_heredoc():
    assert not tf.is_wait_command("echo 'sleep 5 and until x'")
    assert not tf.is_wait_command("cat <<EOF\nsleep 5\nuntil true\nEOF")
    assert tf.is_wait_command("x=$(sleep 5; echo hi)")  # command substitution stays
    assert tf.is_wait_command("echo 'a'; sleep 5")


def test_pgrep_self_match_specimens():
    assert tf.folly_pgrep_self(SPEC_A)
    assert tf.folly_pgrep_self(SPEC_B)
    assert not tf.folly_pgrep_self(SPEC_C)  # wide, but does not match itself
    assert not tf.folly_pgrep_self(SPEC_BRACKET)
    assert not tf.folly_pgrep_self(SPEC_ECHO)
    # a quoted pattern holding shell operators is still read whole
    assert tf.folly_pgrep_self("until ! pgrep -f 'a|b' ; do sleep 5; done  # a|b")
    assert not tf.folly_pgrep_self("pgrep -f '[a]x|[b]y' >/dev/null")


def test_sleep_to_cap_full_cap_versus_early_exit():
    full = "for i in $(seq 1 30); do sleep 10; done"
    assert tf.folly_sleep_to_cap(full, 300.0)  # waited the whole cap, 300 s
    assert not tf.folly_sleep_to_cap(full, 40.0)  # condition met early
    assert not tf.folly_sleep_to_cap("sleep 10", 10.0)  # no loop, no cap
    assert tf.folly_sleep_to_cap("while true; do sleep 5; done", 300.0, timeout_s=300)
    assert tf.folly_sleep_to_cap("for i in $(seq 1 3); do sleep 1m; done", 180.0)  # units
    assert tf.folly_sleep_to_cap("for i in $(seq 1 2); do sleep 1m30s; done", 180.0)


def _call(tid, ts, cmd, err=False, secs=1):
    return {
        "id": tid, "start": ts, "end": ts + tf.timedelta(seconds=secs),
        "tool": "Bash", "cmd": cmd, "is_error": err, "text": "Exit code 1" if err else "",
    }  # fmt: skip


def _nrep(calls):
    return len(tf.repeat_failing_calls(calls))


def test_repeat_failing_only_in_a_row_without_edit_between():
    t0 = tf.datetime(2026, 10, 14, 10, tzinfo=tf.timezone.utc)
    mk = lambda i, c, e=True, tool="Bash": {**_call(f"c{i}", t0 + tf.timedelta(minutes=i), c, e), "tool": tool}  # noqa: E731
    same = [mk(0, "make test"), mk(1, "make test")]
    assert _nrep(same) == 1
    assert _nrep([mk(0, "make test"), mk(1, "ls", False), mk(2, "make test")]) == 0
    edited = [mk(0, "make test"), mk(1, "x", False, "Edit"), mk(2, "make test")]
    assert _nrep(edited) == 0
    assert _nrep([mk(0, "make test", False), mk(1, "make test", False)]) == 0


def _cc_rows():
    t = f"{DAY1}T10:00:"
    return [
        _use("a1", "Bash", t + "00Z", command=SPEC_A),
        _res("a1", f"{DAY1}T10:05:00Z", "ok", error=False),
        _use("b1", "Bash", t + "10Z", command=SPEC_BRACKET),
        _res("b1", t + "20Z", "ok", error=False),
    ]


def _pi_rows():
    """The same two calls in Pi's session shape, plus unknown line types."""
    def call(tid, ts, cmd):
        blk = {"type": "toolCall", "id": tid, "name": "bash", "arguments": {"command": cmd}}
        return {"type": "message", "timestamp": ts, "message": {"role": "assistant", "content": [blk]}}

    def result(tid, ts, ms):
        return {"type": "message", "timestamp": ts, "message": {
            "role": "toolResult", "toolCallId": tid, "isError": False, "durationMs": ms,
            "content": [{"type": "text", "text": "ok"}]}}

    return [
        {"type": "custom_message", "timestamp": f"{DAY1}T09:59:00Z"},
        {"type": "mystery"},
        call("a1", f"{DAY1}T10:00:00Z", SPEC_A),
        result("a1", f"{DAY1}T10:05:00Z", 300000),
        call("b1", f"{DAY1}T10:00:10Z", SPEC_BRACKET),
        result("b1", f"{DAY1}T10:00:20Z", 10000),
    ]


def test_pi_reader_matches_cc_counts_and_survives_unknown_lines(tmp_path):
    cc = _scan(tmp_path / "cc", _cc_rows())
    runs = tmp_path / "runs-x" / "leg" / "attempts" / "1" / "sessions"
    _write(runs / "s.jsonl", _pi_rows())
    pi = tf.run_pi_scan(tmp_path / "runs-x", now=tf.datetime(2026, 10, 21, tzinfo=tf.timezone.utc))
    assert pi["follies"]["pgrep_self_match"]["count"] == cc["follies"]["pgrep_self_match"]["count"] == 1
    assert pi["totals"]["calls"] == cc["totals"]["calls"] == 2
    assert pi["totals"]["wait_commands"] == cc["totals"]["wait_commands"]
    assert pi["skipped_lines"] >= 3  # two unknown types and the trailing junk line
    assert "SPEC" not in json.dumps(pi) and "padme" not in json.dumps(pi)  # no command text


def test_follies_in_summary_are_bounds_with_rung(tmp_path):
    s = _scan(tmp_path, _cc_rows())
    f = s["follies"]["pgrep_self_match"]
    assert f["count"] == 1 and f["sessions"] == 1
    assert f["seconds_upper_bound"] >= f["seconds_lower_bound"] > 0
    assert f["rung"] == "fix_primitive" and f["runtime"] == {"claude-code": 1}
    assert "hours" not in s["follies_note"].split("not")[0]
    assert set(s["follies"]) <= set(s["folly_barrier"])
    assert s["totals"]["calls"] == 2 and "daily" in s  # existing keys unchanged


def test_barrier_denials_counted_without_verdict(tmp_path):
    rows = _fixture_rows()
    s = _scan(tmp_path, rows)
    d = s["barrier_denials"]
    assert d["worktree_guard"] == 1 and d["write_outside_worktree"] == 1
    assert "unattributed" in d
    blob = json.dumps(d).lower()
    assert "delete" not in blob and "verdict" not in blob and "keep" not in blob


def test_sleep_and_repeat_follies_reach_the_summary_end_to_end(tmp_path):
    t = f"{DAY1}T11:"
    rows = [
        # a condition loop, no explicit timeout: Claude Code's default cap applies
        _use("p1", "Bash", t + "00:00Z", command="until test -f /x/done; do sleep 5; done"),
        _res("p1", t + "02:00Z", "ok", error=False),
        _use("r1", "Bash", t + "05:00Z", command="make test"),
        _res("r1", t + "05:10Z", "Exit code 2"),
        _use("r2", "Bash", t + "06:00Z", command="make  test"),
        _res("r2", t + "06:10Z", "Exit code 2"),
    ]
    s = _scan(tmp_path, rows)
    assert s["follies"]["sleep_poll_to_cap"]["count"] == 1
    assert s["follies"]["repeat_failing"]["count"] == 1
    assert s["follies"]["repeat_failing"]["rung"] == "hook"
