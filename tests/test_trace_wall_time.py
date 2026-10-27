"""Tests for scripts/trace-wall-time.py: raid/hunt/gaze wall-time decomposition."""

import importlib.util
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("trace_wall_time", SCRIPTS / "trace-wall-time.py")
tw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tw)

T0 = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
WT = "/repo/.claude/worktrees/t1-1"


def _t(sec):
    return (T0 + timedelta(seconds=sec)).isoformat().replace("+00:00", "Z")


def _use(tid, name, sec, **inp):
    block = {"type": "tool_use", "id": tid, "name": name, "input": inp}
    return {"type": "assistant", "timestamp": _t(sec), "cwd": WT, "message": {"content": [block]}}


def _res(tid, sec, error=False):
    block = {"type": "tool_result", "tool_use_id": tid, "content": "", "is_error": error}
    return {"type": "user", "timestamp": _t(sec), "cwd": WT, "message": {"content": [block]}}


def _say(sec, text, role="user", **extra):
    return {"type": role, "timestamp": _t(sec), "cwd": WT,
            "message": {"content": [{"type": "text", "text": text}]}, **extra}


def _attach(sec):
    return {"type": "attachment", "timestamp": _t(sec), "attachment": {"type": "hook_success"}}


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    os.utime(path, (time.time(), time.time()))


def _fixture(root):
    sess = root / "proj" / "s1"
    _write(root / "proj" / "s1.jsonl", [
        _say(0, "<command-name>/raid</command-name>"),
        _say(10, "planning", role="assistant"),                       # generation 10
        _use("spawn", "Agent", 12, run_in_background=True),            # generation 2
        _res("spawn", 13),                                             # agent-foreground 1
        _say(14, "waiting", role="assistant"),                         # generation 1
        _attach(100),                                                  # passive: goes to the next record
        _say(114, "<task-notification>done</task-notification>"),      # background-wait 86 + 14
        _say(4114, "back from lunch"),                                 # human-away 4000
    ])
    _write(sess / "subagents" / "agent-a1.jsonl", [
        _say(20, "Role: coder"),
        _use("h", "Skill", 21, skill="hunt"),
        _res("h", 22),
        _use("t1", "Bash", 23, command=f"cd {WT} && uv run pytest tests/ -q > /tmp/x.log"),
        _res("t1", 53),                                                # test/gate 30
        _use("mb", "Bash", 53, command="git merge-base --is-ancestor main HEAD"),
        _res("mb", 54),                                                # read-only git
        _use("t2", "Bash", 54, command="uv run pytest tests/ -q"),
        _res("t2", 84),                                                # rerun, no change
        _use("e", "Edit", 85, file_path=f"{WT}/x.py"),
        _res("e", 86),
        _use("t3", "Bash", 87, command="uv run pytest tests/ -q"),
        _res("t3", 117),                                               # after an edit: not a rerun
        _use("p", "Bash", 118, command="timeout 60 bash -c 'until test -s f; do sleep 5; done'"),
        _res("p", 178),                                                # poll/wait 60
    ])
    (sess / "subagents" / "agent-a1.meta.json").write_text(json.dumps({"toolUseId": "spawn"}))


def _report(tmp_path):
    _fixture(tmp_path)
    since = datetime.now(timezone.utc) - timedelta(days=1)
    return tw.survey(tw.load_traces(tmp_path, since), since - timedelta(days=30))


def test_orchestrator_gaps_go_to_the_record_that_ends_them(tmp_path):
    raid = _report(tmp_path)["raid"]
    o = raid["orchestrator_s"]
    assert raid["runs"] == 1 and raid["agents"] == 1
    assert o["generation"] == 13
    assert o["background-wait"] == 100  # the attachment's 86 s is not "harness"
    assert o["human-away"] == 4000
    assert "harness" not in o and "idle-tail" not in o


def test_hunt_inside_raid_is_counted_in_both_views(tmp_path):
    r = _report(tmp_path)
    assert r["hunt"]["runs"] == 1 and r["hunt"]["nested_in_raid"] == 1
    assert r["raid"]["tree_s"]["test/gate"] == 90
    assert r["raid"]["tree_s"]["poll/wait"] == 60  # quoted loop still a poll


def test_rerun_without_change_is_flagged_and_edit_resets(tmp_path):
    n = _report(tmp_path)["raid"]["test_runs"]
    assert n["runs"] == 3
    assert n["rerun_after_pass"] == 1
    assert "rerun_after_fail" not in n


def test_command_dir_follows_cd_and_dash_c():
    assert tw.command_dir(f"cd {WT}/sub && make check", "/elsewhere") == WT
    assert tw.command_dir(f"git -C {WT} status", "/elsewhere") == WT
    assert tw.command_dir("make check", f"{WT}/a") == WT


def test_command_key_never_prints_arguments():
    assert tw.command_key("TOKEN=s3cret curl -H 'auth: x' https://h") == "curl"
    assert tw.command_key("timeout 590 bash -c 'until grep -q X f; do sleep 5; done'") == "timeout bash"
    assert tw.command_key("echo ghp_SeCrEt") == "echo"
    assert tw.command_key("printf sk-ant-SeCrEt") == "printf"
    assert tw.command_key("curl https://h/SeCrEt") == "curl"
    assert tw.command_key("ssh myhost") == "ssh"
    assert tw.command_key("export KEY=v && curl x") == "curl"
    assert tw.command_key("uv run pytest -q") == "uv run"
    assert tw.command_key("/x/scratchpad/idle.sh 9") == "idle.sh"


def test_p90_is_nearest_rank_and_out_of_window_runs_drop(tmp_path):
    _fixture(tmp_path)
    traces = tw.load_traces(tmp_path, datetime.now(timezone.utc) - timedelta(days=1))
    assert tw.survey(traces, T0 + timedelta(seconds=1))["raid"]["runs"] == 0


def test_mutating_git_chained_before_a_test_resets_the_ledger():
    ev = tw.test_events([tw.Trace(Path("x"), [
        _use("a", "Bash", 0, command="uv run pytest -q"), _res("a", 10),
        _use("b", "Bash", 11, command="git pull && uv run pytest -q"), _res("b", 20),
    ])], None)
    assert tw.redundancy(ev)[0].get("rerun_after_pass", 0) == 0


def test_agent_spawned_before_the_run_is_not_the_runs(tmp_path):
    _fixture(tmp_path)
    sub = tmp_path / "proj" / "s1" / "subagents"
    _write(sub / "agent-early.jsonl", [
        _say(-50, "early"), _use("eh", "Skill", -45, skill="hunt"), _res("eh", -44),
    ])
    (sub / "agent-early.meta.json").write_text(json.dumps({"toolUseId": "spawn"}))
    since = datetime.now(timezone.utc) - timedelta(days=1)
    r = tw.survey(tw.load_traces(tmp_path, since), since - timedelta(days=30))
    assert r["raid"]["agents"] == 1
    assert r["hunt"]["runs"] == 2 and r["hunt"]["nested_in_raid"] == 1  # the early hunt is not nested
