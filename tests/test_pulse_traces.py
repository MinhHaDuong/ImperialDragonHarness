"""pulse_traces reads how long agents wait on test and gate commands.

The survey feeds a suggestion at lair, so its two failure modes both matter: a
silent miss hides a real speed bump, and a false alarm teaches the author to
ignore the line. These tests pin a positive control (a slow, repeated gate must
fire), the silence of a clean trace, the distinction between "clean" and "could
not look", and the command classifier that decides what counts as a gate.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "pulse_traces.py"
sys.path.insert(0, str(REPO / "scripts"))

import pulse_traces as pt  # noqa: E402

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _trace(path: Path, calls: list[dict]) -> None:
    """One session file: each call becomes a tool_use line then a tool_result line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for index, call in enumerate(calls):
        use_id = f"toolu_{path.stem}_{index}"
        start = call["start"]
        lines.append({
            "type": "assistant", "timestamp": _stamp(start),
            "message": {"content": [{
                "type": "tool_use", "id": use_id, "name": "Bash",
                "input": {"command": call["command"],
                          "run_in_background": call.get("background", False)},
            }]},
        })
        if call.get("unpaired"):
            continue
        lines.append({
            "type": "user",
            "timestamp": _stamp(start + timedelta(seconds=call["seconds"])),
            "message": {"content": [{"type": "tool_result", "tool_use_id": use_id}]},
        })
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")


def _project_dir(root: Path, project: Path) -> Path:
    return root / pt.encode_project(project)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    path = tmp_path / "work" / "my-project"
    path.mkdir(parents=True)
    return path


def _call(command: str, seconds: float, days_ago: float = 0.1, **extra) -> dict:
    return {"command": command, "seconds": seconds,
            "start": NOW - timedelta(days=days_ago), **extra}


# --- the classifier --------------------------------------------------------

@pytest.mark.parametrize("command, expected", [
    ("make check-fast", ["make check-fast"]),
    ("cd /x && time timeout 590 make check-fast 2>&1 | tail -3", ["make check-fast"]),
    ("PYTHONPATH=a:b uv run pytest -q -m 'not slow'", ["pytest"]),
    ("python3 -m pytest tests/ -n 4", ["pytest"]),
    ("rtk proxy python3 -m pytest tests/", ["pytest"]),
    ("python3 scripts/raid-gate.py -- make check", ["make check"]),
    ("python3 scripts/scoped-check.py --dry-run", ["scoped-check"]),
    ("make jetp-ledger-check", ["make jetp-ledger-check"]),
    ("make lint && make check-fast", ["make lint", "make check-fast"]),
    ("(make check-observatory)", ["make check-observatory"]),
    ("make -j 4 -C sub check", ["make check"]),
])
def test_real_gate_commands_are_recognised(command, expected):
    assert pt.gate_classes(command) == expected


@pytest.mark.parametrize("command", [
    'git commit -qam "run make check-fast before pytest"',
    "grep -rn 'make check' skills/ | head",
    "cat >> ticket.erg <<'EOF'\nmake check-fast must pass\npytest -q\nEOF",
    "echo make check",
    "sed -i 's/pytest/pytest -q/' Makefile",
    "until [ -n \"$(tail -c 300 out.log)\" ]; do sleep 5; done",
    "git worktree remove /tmp/wt-for-pytest-run",
])
def test_mentions_are_not_gate_commands(command):
    assert pt.gate_classes(command) == []


def test_project_vocabulary_extends_the_classifier():
    assert pt.gate_classes("make site-audit") == []
    assert pt.gate_classes("make site-audit", extra=[r"make site-audit"]) == ["make site-audit"]


# --- pairing and durations --------------------------------------------------

def test_foreground_duration_is_the_gap_between_call_and_result(tmp_path, project):
    root = tmp_path / "traces"
    _trace(_project_dir(root, project) / "s1.jsonl",
           [_call("make check-fast", 90), _call("make check-fast", 30)])
    rows = pt.collect(root, project, days=7, now=NOW)
    assert sorted(row.seconds for row in rows.foreground) == [30, 90]
    assert rows.unpaired == 0


def test_background_and_unpaired_calls_do_not_count_as_waiting(tmp_path, project):
    root = tmp_path / "traces"
    _trace(_project_dir(root, project) / "s1.jsonl", [
        _call("make check-fast", 1, background=True),
        _call("make check-fast", 0, unpaired=True),
        _call("make check-fast", 60),
    ])
    rows = pt.collect(root, project, days=7, now=NOW)
    assert [row.seconds for row in rows.foreground] == [60]
    assert rows.background == 1
    assert rows.unpaired == 1


def test_chained_gates_are_one_wait_named_for_what_they_chain(tmp_path, project):
    root = tmp_path / "traces"
    _trace(_project_dir(root, project) / "s1.jsonl",
           [_call("make lint && make check-fast", 100)])
    (row,) = pt.collect(root, project, days=7, now=NOW).foreground
    assert row.gate == "make lint + make check-fast"


def test_a_file_that_vanishes_is_counted_not_fatal(tmp_path, project):
    root = tmp_path / "traces"
    directory = _project_dir(root, project)
    _trace(directory / "s1.jsonl", [_call("make check-fast", 40)])
    (directory / "gone.jsonl").symlink_to(directory / "does-not-exist.jsonl")
    collected = pt.collect(root, project, days=7, now=NOW)
    assert collected.unreadable == 1 and len(collected.foreground) == 1


def test_first_run_of_a_session_is_told_apart_from_later_runs(tmp_path, project):
    root = tmp_path / "traces"
    for name, first in (("s1", 250), ("s2", 240)):
        _trace(_project_dir(root, project) / f"{name}.jsonl", [
            _call("make lint", first, days_ago=0.4),
            _call("make lint", 5, days_ago=0.3),
            _call("make lint", 6, days_ago=0.2),
        ])
    stats = pt.summarise(pt.collect(root, project, days=7, now=NOW).foreground)["make lint"]
    assert stats["first_of_session_median_s"] == 245 and stats["later_median_s"] == 6


def test_the_window_and_the_project_bound_what_is_read(tmp_path, project):
    root = tmp_path / "traces"
    other = tmp_path / "work" / "other-project"
    other.mkdir()
    _trace(_project_dir(root, project) / "s1.jsonl",
           [_call("make check-fast", 50, days_ago=0.2), _call("make check-fast", 50, days_ago=30)])
    _trace(_project_dir(root, other) / "s2.jsonl", [_call("make check-fast", 999)])
    rows = pt.collect(root, project, days=7, now=NOW)
    assert [row.seconds for row in rows.foreground] == [50]


def test_a_worktree_of_the_project_belongs_to_the_project(tmp_path, project):
    root = tmp_path / "traces"
    worktree = project / ".claude" / "worktrees" / "t1-abc"
    worktree.mkdir(parents=True)
    _trace(_project_dir(root, worktree) / "s1.jsonl", [_call("make check-fast", 77)])
    assert [row.seconds for row in pt.collect(root, project, days=7, now=NOW).foreground] == [77]


# --- the survey -------------------------------------------------------------

def _slow_repeated(root: Path, project: Path) -> None:
    _trace(_project_dir(root, project) / "s1.jsonl",
           [_call("make check-fast", 230, days_ago=0.1 * (i + 1)) for i in range(4)])


def test_positive_control_a_slow_repeated_gate_fires(tmp_path, project):
    root = tmp_path / "traces"
    _slow_repeated(root, project)
    lines = pt.survey(root, project, days=7, now=NOW)
    assert len(lines) == 1
    assert "make check-fast" in lines[0] and "4" in lines[0] and "/pulse" in lines[0]


def test_a_clean_trace_is_silent(tmp_path, project):
    root = tmp_path / "traces"
    _trace(_project_dir(root, project) / "s1.jsonl",
           [_call("make check-fast", 8, days_ago=0.1 * (i + 1)) for i in range(10)])
    assert pt.survey(root, project, days=7, now=NOW) == []


def test_many_quick_runs_are_use_not_a_speed_bump(tmp_path, project):
    root = tmp_path / "traces"
    _trace(_project_dir(root, project) / "s1.jsonl",
           [_call("python3 -m pytest tests/test_x.py", 8, days_ago=0.001 * (i + 1)) for i in range(200)])
    assert pt.survey(root, project, days=7, now=NOW) == []


def test_few_runs_do_not_fire_however_slow(tmp_path, project):
    root = tmp_path / "traces"
    _trace(_project_dir(root, project) / "s1.jsonl", [_call("make check", 900)])
    assert pt.survey(root, project, days=7, now=NOW) == []


def test_not_being_able_to_look_is_said_not_silent(tmp_path, project):
    (line,) = pt.survey(tmp_path / "no-such-root", project, days=7, now=NOW)
    assert line.startswith("pulse: not checked")
    root = tmp_path / "traces"
    root.mkdir()
    (line,) = pt.survey(root, project, days=7, now=NOW)
    assert line.startswith("pulse: not checked")


def test_activity_without_a_recognised_gate_says_so_instead_of_staying_silent(tmp_path, project):
    root = tmp_path / "traces"
    _trace(_project_dir(root, project) / "s1.jsonl", [_call("ls -la", 1), _call("make site-audit", 300)])
    (line,) = pt.survey(root, project, days=7, now=NOW)
    assert "recognised no test or gate command" in line and "--pattern" in line
    (flag,) = pt.survey(root, project, days=7, now=NOW, extra=[r"make site-audit"], min_runs=1)
    assert "make site-audit" in flag


def test_the_survey_names_at_most_three_gates(tmp_path, project):
    root = tmp_path / "traces"
    calls = []
    for name in ("check-fast", "lint", "check", "check-domain"):
        calls += [_call(f"make {name}", 400, days_ago=0.1 * (i + 1)) for i in range(4)]
    _trace(_project_dir(root, project) / "s1.jsonl", calls)
    lines = pt.survey(root, project, days=7, now=NOW)
    assert len(lines) == 4 and "1 more" in lines[-1]


# --- the command line -------------------------------------------------------

def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          env=child_env())


@pytest.mark.integration
def test_cli_survey_and_collect_json(tmp_path, project):
    root = tmp_path / "traces"
    start = datetime.now(timezone.utc)
    _trace(_project_dir(root, project) / "s1.jsonl", [
        {"command": "make check-fast", "seconds": 240,
         "start": start - timedelta(hours=i + 1)} for i in range(4)
    ])
    survey = _run("survey", "--project", str(project), "--traces", str(root))
    assert survey.returncode == 0 and "make check-fast" in survey.stdout
    collect = _run("collect", "--project", str(project), "--traces", str(root), "--json")
    data = json.loads(collect.stdout)
    assert data["gates"]["make check-fast"]["runs"] == 4
    missing = _run("survey", "--project", str(project), "--traces", str(tmp_path / "none"))
    assert missing.returncode == 0 and missing.stdout.startswith("pulse: not checked")
