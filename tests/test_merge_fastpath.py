"""Fast path for bookkeeping merges, verified after the fact by a monitor (ticket 1226).

A bookkeeping-tier record on an open fast path runs only the checks the base
declares under "fastpath"; the full check set then runs on the new main tip
(scripts/merge_monitor.py) and writes a verdict note keyed by that tip. The
fast path closes when main is K merges past its last verified-green tip, when
that verdict is older than the bound, or when the last verdict is red; no
verdict is unverified. Every fixture is a local repository with a bare origin.
The forge's merge is played by pushing the deterministic candidate to main:
same parents, same tree.
"""

import fcntl
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "merge-gate.py"
MONITOR = ROOT / "scripts" / "merge_monitor.py"
SWEEP = ROOT / "scripts" / "main_sweep.py"

# The "suite" stands for pytest-guard: it reads the live STATE.md, as the
# harness suite does (test_state_within_cap), so a bookkeeping change can break it.
SUITE = ["sh", "-c", "test $(wc -l < STATE.md) -le 3"]


def config(**fastpath):
    return {
        "gate": "on",
        "scope": "fx",
        "checks": [
            {"name": "tickets", "argv": ["true"]},
            {"name": "suite", "argv": SUITE},
        ],
        "tiers": {"bookkeeping": ["tickets", "suite"]},
        "fastpath": {"checks": ["tickets"], "max_lag": 5, "max_age_minutes": 120, **fastpath},
    }


def git(cwd, *args, env=None):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=env or child_env()
    ).stdout.strip()


def tool(script, cwd, *args, env=None):
    return subprocess.run(
        [sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True, env=env or child_env()
    )


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path, config())


def make_repo(tmp_path, conf):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, env=child_env())
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True, env=child_env())
    for key, value in (("user.email", "t@example.com"), ("user.name", "Fixture"), ("commit.gpgsign", "false")):
        git(work, "config", key, value)
    (work / ".merge-gate.json").write_text(json.dumps(conf), encoding="utf-8")
    (work / "STATE.md").write_text("state\n", encoding="utf-8")
    (work / "tickets").mkdir()
    (work / "tickets" / "0001-a.erg").write_text("one\n", encoding="utf-8")
    (work / "code.txt").write_text("code\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "base")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    return work


def merge(work, path, text, *, env=None, expect=0):
    """Branch from origin/main, change one file, record, and land the candidate as main.

    Returns the record's stdout; the landed tip is origin/main afterwards.
    """
    git(work, "fetch", "-q", "origin")
    git(work, "switch", "-q", "--detach", "origin/main")
    target = work / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", f"change {path}")
    head = git(work, "rev-parse", "HEAD")
    run = tool(GATE, work, "run", "--base", "origin/main", "--head", head, env=env)
    assert run.returncode == expect, run.stdout + run.stderr
    if expect == 0:
        check = tool(GATE, work, "check", "--base", "origin/main", "--head", head)
        assert check.returncode == 0, check.stdout + check.stderr
        cand = tool(GATE, work, "candidate", "--base", "origin/main", "--head", head).stdout.strip()
        git(work, "push", "-q", "origin", f"{cand}:refs/heads/main")
        git(work, "fetch", "-q", "origin")
    return run.stdout


def verify(work, *extra, env=None):
    git(work, "fetch", "-q", "origin")
    return tool(MONITOR, work, "verify", "--tip", "origin/main", *extra, env=env)


def fastpath(work, env=None):
    git(work, "fetch", "-q", "origin")
    return tool(GATE, work, "fastpath", "--base", "origin/main", env=env)


def scope_of(record):
    return next(line for line in record.splitlines() if line.startswith("scope: "))


def verdict_note(work):
    git(work, "fetch", "-q", "origin", "+refs/notes/gate-verdict:refs/notes/gate-verdict")
    return git(work, "notes", "--ref=refs/notes/gate-verdict", "show", "origin/main")


def test_no_verdict_anywhere_keeps_the_fast_path_closed(repo):
    probe = fastpath(repo)
    assert probe.returncode == 1, probe.stdout + probe.stderr
    record = merge(repo, "tickets/0002-b.erg", "two\n")
    assert scope_of(record) == "scope: fx/bookkeeping: tickets suite"


def test_ticket_only_merge_on_an_open_fast_path_runs_no_suite(repo):
    assert verify(repo).returncode == 0
    assert fastpath(repo).returncode == 0
    record = merge(repo, "tickets/0002-b.erg", "two\n")
    assert scope_of(record) == "scope: fx/fastpath: tickets"
    assert not any(line.startswith("check: suite ") for line in record.splitlines())
    assert any(line.startswith("duration: ") for line in record.splitlines())


def test_fast_path_record_is_accepted_by_the_hook_check_and_the_audit_of_main(repo):
    verify(repo)
    merge(repo, "tickets/0002-b.erg", "two\n")
    hook_check = tool(GATE, repo, "check", "--no-fetch", "--base", "origin/main^1", "--head", "origin/main^2")
    assert hook_check.returncode == 0, hook_check.stdout + hook_check.stderr
    audit = tool(SWEEP, repo, "--ref", "origin/main")
    tip = git(repo, "rev-parse", "origin/main")[:12]
    line = next(x for x in audit.stdout.splitlines() if tip in x)
    assert line.startswith("ok"), audit.stdout


def test_state_over_cap_on_the_fast_path_is_caught_by_the_monitor_and_closes_it(repo):
    verify(repo)
    merge(repo, "tickets/0002-b.erg", "two\n")
    merge(repo, "STATE.md", "1\n2\n3\n4\n5\n")
    bad = git(repo, "rev-parse", "origin/main")
    record = merge(repo, "tickets/0003-c.erg", "three\n")
    assert scope_of(record) == "scope: fx/fastpath: tickets"  # nothing has run the suite yet
    result = verify(repo)
    assert result.returncode == 1, result.stdout + result.stderr
    note = verdict_note(repo)
    assert "result: fail" in note
    assert f"culprit: {bad}" in note  # re-run on the merges since green names the STATE.md merge
    assert fastpath(repo).returncode == 1
    record = merge(repo, "tickets/0004-d.erg", "four\n", expect=1)
    assert scope_of(record) == "scope: fx/bookkeeping: tickets suite"


def test_a_green_verdict_reopens_the_fast_path_after_a_red_one(repo):
    verify(repo)
    merge(repo, "STATE.md", "1\n2\n3\n4\n5\n")
    verify(repo)
    assert fastpath(repo).returncode == 1
    merge(repo, "STATE.md", "fixed\n")  # pays the full record, which verifies its own tip
    probe = fastpath(repo)
    assert probe.returncode == 0, probe.stdout


def test_six_merges_with_a_slow_monitor_close_the_fast_path_at_the_sixth(repo):
    verify(repo)
    for n in range(1, 6):
        record = merge(repo, f"tickets/{n:04d}-x.erg", f"{n}\n")
        assert scope_of(record) == "scope: fx/fastpath: tickets", n
    record = merge(repo, "tickets/0006-x.erg", "6\n")
    assert scope_of(record) == "scope: fx/bookkeeping: tickets suite"


def test_a_code_merge_after_a_bad_bookkeeping_merge_fails_its_own_record(repo):
    verify(repo)
    merge(repo, "STATE.md", "1\n2\n3\n4\n5\n")
    record = merge(repo, "code.txt", "new code\n", expect=1)
    assert scope_of(record) == "scope: fx: tickets suite"
    assert "check: suite fail" in record


def test_a_dead_monitor_closes_the_fast_path_once_the_last_verdict_is_too_old(repo):
    verify(repo)
    merge(repo, "tickets/0002-b.erg", "two\n")  # no monitor runs after it
    assert fastpath(repo).returncode == 0
    later = {**child_env(), "MERGE_GATE_NOW": str(int(time.time()) + 3 * 3600)}
    probe = fastpath(repo, env=later)
    assert probe.returncode == 1 and "older than" in probe.stdout, probe.stdout
    record = merge(repo, "tickets/0003-c.erg", "three\n", env=later)
    assert scope_of(record) == "scope: fx/bookkeeping: tickets suite"


def test_monitor_coalesces_one_run_in_flight_and_one_pending_latest_wins(repo):
    verify(repo)  # green base: the merges below take the fast path and leave their tips unverified
    base = git(repo, "rev-parse", "origin/main")
    state = repo / ".git" / "merge-gate-monitor"
    state.mkdir(exist_ok=True)
    tips = []
    with open(state / "lock", "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)  # a run is in flight
        for n in range(3):
            merge(repo, "tickets/0002-b.erg", f"{n}\n")
            tips.append(git(repo, "rev-parse", "origin/main"))
            spawned = tool(MONITOR, repo, "spawn", "--ref", "origin/main")
            assert spawned.returncode == 0, spawned.stderr
        time.sleep(1)  # any worker spawned meanwhile meets the lock and leaves
        assert (state / "pending").read_text().strip() == tips[-1]
    worked = tool(MONITOR, repo, "work")
    assert worked.returncode == 0, worked.stdout + worked.stderr
    git(repo, "fetch", "-q", "origin", "+refs/notes/gate-verdict:refs/notes/gate-verdict")
    noted = git(repo, "notes", "--ref=refs/notes/gate-verdict", "list").split()
    assert sorted(noted[1::2]) == sorted([base, tips[-1]])  # one run for three merges
    assert not (state / "pending").exists()


FLAKY_SUITE = (
    'if [ -e "$0.ran" ]; then exit 0; fi; touch "$0.ran"; '
    'echo "FAILED tests/test_x.py::test_flake - boom"; exit 1'
)


@pytest.mark.parametrize("reproduces", [False, True])
def test_a_red_suite_reruns_only_its_failing_tests_once(tmp_path, reproduces):
    marker = tmp_path / "suite"
    rerun_body = "exit 1" if reproduces else 'echo "$@" > "$0.rerun"; exit 0'
    conf = config(rerun={"suite": ["sh", "-c", rerun_body, str(marker)]})
    conf["checks"][1]["argv"] = ["sh", "-c", FLAKY_SUITE, str(marker)]
    work = make_repo(tmp_path, conf)
    result = verify(work)
    note = verdict_note(work)
    assert "failed-first-run: tests/test_x.py::test_flake" in note
    if reproduces:
        assert result.returncode == 1 and "result: fail" in note
        assert fastpath(work).returncode == 1
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "result: pass" in note
        assert "flaky: 1 tests/test_x.py::test_flake" in note
        assert Path(f"{marker}.rerun").read_text().split() == ["tests/test_x.py::test_flake"]
        assert fastpath(work).returncode == 0


def test_a_suite_that_stopped_early_is_red_even_if_its_listed_failures_pass_alone(tmp_path):
    """Gaze round 11: pytest exits 2 (interrupted) or 3 (internal error) after listing a
    failure; the tests after the stop never ran, so re-running the listed id proves nothing."""
    marker = tmp_path / "suite"
    conf = config(rerun={"suite": ["sh", "-c", 'echo "$@" > "$0.rerun"; exit 0', str(marker)]})
    conf["checks"][1]["argv"] = ["sh", "-c", 'echo "FAILED tests/test_x.py::test_a - boom"; exit 2']
    work = make_repo(tmp_path, conf)
    result = verify(work)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "result: fail" in verdict_note(work)
    assert not Path(f"{marker}.rerun").exists()
    assert fastpath(work).returncode == 1


MAKE_SUITE = (
    'echo "FAILED tests/test_x.py::test_flake - boom"; {extra}'
    'echo "======== 1 failed, 3 passed in 1.00s ========"; exit 1'
)


@pytest.mark.parametrize("extra, recovers", [
    ("", True),  # an ordinary failure behind make (exit 2): the flaky re-run still works
    ('echo "!!!!!!!! Interrupted: 1 error during collection !!!!!!!!"; ', False),
    ('echo "INTERNALERROR> boom"; ', False),
])
def test_the_flaky_rerun_reads_pytest_behind_make(tmp_path, extra, recovers):
    """Gaze round 12: pytest-guard is `make check-tests`, and make exits 2 for any failing
    recipe, so the exit code alone cannot tell an ordinary failure from a stopped run."""
    marker = tmp_path / "suite"
    makefile = tmp_path / "Makefile"
    makefile.write_text("check:\n\t@sh -c '" + MAKE_SUITE.format(extra=extra).replace("'", "'\\''") + "'\n")
    conf = config(rerun={"suite": ["sh", "-c", 'echo "$@" > "$0.rerun"; exit 0', str(marker)]})
    conf["checks"][1]["argv"] = ["make", "-s", "-f", str(makefile), "check"]
    work = make_repo(tmp_path, conf)
    result = verify(work)
    note = verdict_note(work)
    if recovers:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "result: pass" in note and "flaky: 1 tests/test_x.py::test_flake" in note
    else:
        assert result.returncode == 1 and "result: fail" in note
        assert not Path(f"{marker}.rerun").exists()


def test_a_verdict_stamped_in_the_future_keeps_the_fast_path_closed(repo):
    verify(repo)
    earlier = {**child_env(), "MERGE_GATE_NOW": str(int(time.time()) - 3600)}
    probe = fastpath(repo, env=earlier)
    assert probe.returncode == 1 and "future" in probe.stdout, probe.stdout


def test_a_fast_path_record_not_written_on_an_open_path_is_refused(repo):
    verify(repo)
    git(repo, "fetch", "-q", "origin")
    git(repo, "switch", "-q", "--detach", "origin/main")
    (repo / "tickets" / "0002-b.erg").write_text("two\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "ticket")
    head = git(repo, "rev-parse", "HEAD")
    record = tool(GATE, repo, "run", "--base", "origin/main", "--head", head).stdout
    assert scope_of(record) == "scope: fx/fastpath: tickets"
    cand = tool(GATE, repo, "candidate", "--base", "origin/main", "--head", head).stdout.strip()
    forged = "\n".join(
        "fastpath: closed: red verdict" if line.startswith("fastpath: ") else line
        for line in record.splitlines()
        if not line.startswith(("pass:", "duration:"))
    )
    git(repo, "fetch", "-q", "origin", "+refs/notes/gate:refs/notes/gate")
    git(repo, "notes", "--ref=refs/notes/gate", "append", "-m", forged, cand)
    check = tool(GATE, repo, "check", "--no-fetch", "--base", "origin/main", "--head", head)
    assert check.returncode == 1 and "fast path" in check.stdout, check.stdout + check.stderr


def test_a_failing_id_with_a_control_character_still_writes_a_red_verdict(tmp_path):
    conf = config()
    conf["checks"][1]["argv"] = ["sh", "-c", "printf 'FAILED tests/a\\001b - boom\\n'; exit 1"]
    work = make_repo(tmp_path, conf)
    result = verify(work)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "result: fail" in verdict_note(work)


def load_monitor():
    spec = importlib.util.spec_from_file_location("merge_monitor_under_test", MONITOR)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    return monitor


@pytest.mark.parametrize("error", ["Timeout", "GateError", "OSError"])
def test_a_culprit_search_that_fails_keeps_the_red_verdict(repo, monkeypatch, tmp_path, error):
    merge(repo, "STATE.md", "1\n2\n3\n4\n5\n", expect=1)  # the full record is red; land it anyway
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "-q", "origin", f"{head}:refs/heads/main")
    git(repo, "fetch", "-q", "origin")
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        monkeypatch.delenv(key)
    monkeypatch.chdir(repo)
    monitor = load_monitor()

    def late(*_args):
        raise {"Timeout": monitor.Timeout, "GateError": monitor.mg.GateError, "OSError": OSError}[error]("culprit failed")

    monkeypatch.setattr(monitor, "culprit", late)
    assert monitor.verify_tip(head, "origin", tmp_path) == monitor.RED
    note = verdict_note(repo)
    assert "result: fail" in note and "culprit: unknown" in note


def test_a_worker_drains_every_pending_tip_however_many_merges_arrive(tmp_path, monkeypatch):
    monitor = load_monitor()
    seen = []

    def fake_verify(tip, _remote, directory):
        seen.append(tip)
        if len(seen) < 15:  # a spawn lands during every run
            (directory / "pending").write_text(f"tip{len(seen)}\n")
        return monitor.GREEN

    monkeypatch.setattr(monitor, "verify_tip", fake_verify)
    monkeypatch.setattr(monitor.os, "nice", lambda _n: 0)
    (tmp_path / "pending").write_text("tip0\n")
    args = monitor.parser().parse_args(["work", "--state-dir", str(tmp_path)])
    assert monitor.cmd_work(args) == 0
    assert seen == [f"tip{n}" for n in range(15)]
    assert not (tmp_path / "pending").exists()


def test_a_fast_path_record_is_refused_at_merge_once_the_path_has_closed(repo):
    verify(repo)
    git(repo, "switch", "-q", "--detach", "origin/main")
    (repo / "tickets" / "0002-b.erg").write_text("two\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "ticket")
    head = git(repo, "rev-parse", "HEAD")
    record = tool(GATE, repo, "run", "--base", "origin/main", "--head", head).stdout
    assert scope_of(record) == "scope: fx/fastpath: tickets"
    later = {**child_env(), "MERGE_GATE_NOW": str(int(time.time()) + 3 * 3600)}
    at_merge = tool(GATE, repo, "check", "--base", "origin/main", "--head", head, env=later)
    assert at_merge.returncode == 1 and "closed since the record" in at_merge.stdout, at_merge.stdout
    hook = tool(GATE, repo, "check", "--no-fetch", "--base", "origin/main", "--head", head, env=later)
    assert hook.returncode == 0, hook.stdout  # after the fact, the record stated the path open


def test_a_spawn_never_replaces_the_pending_tip_with_an_older_one(repo):
    older = git(repo, "rev-parse", "origin/main")
    merge(repo, "code.txt", "newer\n")
    newer = git(repo, "rev-parse", "origin/main")
    state = repo / ".git" / "merge-gate-monitor"
    state.mkdir(exist_ok=True)
    with open(state / "lock", "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)  # no worker takes the slot meanwhile
        assert tool(MONITOR, repo, "spawn", "--ref", newer).returncode == 0
        assert tool(MONITOR, repo, "spawn", "--ref", older).returncode == 0
        assert (state / "pending").read_text().strip() == newer
    assert not list(state.glob("pending.tmp*")) and not [f for f in state.glob("pending.*") if f.name != "pending.lock"]


def test_a_git_call_past_its_timeout_raises_when_checked_and_answers_124_otherwise(monkeypatch):
    mg = load_monitor().mg

    def hung(*_args, **kwargs):
        raise subprocess.TimeoutExpired("git", kwargs.get("timeout"))

    monkeypatch.setattr(mg.subprocess, "run", hung)
    monkeypatch.setattr(mg, "toplevel", lambda _cwd: str(ROOT))
    with pytest.raises(mg.GateError, match="no answer"):
        mg.git("fetch", "origin")
    assert mg.git("worktree", "prune", check=False).returncode == 124


def test_a_fast_path_declaring_no_checks_is_an_invalid_gate(tmp_path):
    conf = config()
    conf["fastpath"]["checks"] = []
    repo = make_repo(tmp_path, conf)
    git(repo, "switch", "-q", "--detach", "origin/main")
    (repo / "tickets" / "0002-b.erg").write_text("two\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "ticket")
    run = tool(GATE, repo, "run", "--base", "origin/main", "--head", git(repo, "rev-parse", "HEAD"))
    assert run.returncode == 3 and "at least one" in run.stderr, run.stdout + run.stderr


def test_a_hung_notes_read_is_an_error_not_a_missing_note(monkeypatch):
    mg = load_monitor().mg
    monkeypatch.setattr(mg, "toplevel", lambda _cwd: str(ROOT))

    def hung(*_args, **kwargs):
        raise subprocess.TimeoutExpired("git", kwargs.get("timeout"))

    monkeypatch.setattr(mg.subprocess, "run", hung)
    with pytest.raises(mg.GateError, match="no answer"):
        mg.read_note("0" * 40)


@pytest.mark.parametrize("code, raises", [(1, False), (128, True)])
def test_only_exit_1_reads_as_a_missing_note(monkeypatch, code, raises):
    """Gaze round 6: git exits 1 for no note (or no notes ref yet), 128 on a fatal error.

    A fatal read counted as absent would let the fast path skip an unreadable verdict
    and accept an older green one: fail open.
    """
    mg = load_monitor().mg
    monkeypatch.setattr(mg, "toplevel", lambda _cwd: str(ROOT))

    def answer(args, *_a, **_kw):
        return subprocess.CompletedProcess(args, code, stdout="", stderr="fatal: bad object")

    monkeypatch.setattr(mg.subprocess, "run", answer)
    if raises:
        with pytest.raises(mg.GateError, match="exit 128"):
            mg.read_note("0" * 40)
    else:
        assert mg.read_note("0" * 40) == ""


def test_a_verdict_survives_a_concurrent_notes_fetch_between_append_and_push(repo, monkeypatch):
    """Gaze round 8: another session's fetch (+ref:ref) resets the local verdict ref
    after the append. Pushing the ref by name then reports "up to date" and the red
    verdict is lost, leaving the fast path open on the older green one."""
    monkeypatch.chdir(repo)
    mg = load_monitor().mg
    ref = mg.VERDICT_REF
    base = git(repo, "rev-parse", "HEAD")
    mg.append_and_push(base, "green", "origin", ref=ref)
    real_git, clobbered = mg.git, []

    def interleaved(*args, **kwargs):
        result = real_git(*args, **kwargs)
        if args[:1] == ("notes",) and "append" in args and not clobbered:
            clobbered.append(True)
            real_git("fetch", "-q", "origin", f"+{ref}:{ref}")  # the concurrent session
        return result

    monkeypatch.setattr(mg, "git", interleaved)
    mg.append_and_push(base, "red", "origin", ref=ref)
    assert clobbered
    origin = repo.parent / "origin.git"
    shown = subprocess.run(["git", "-C", str(origin), "notes", f"--ref={ref}", "show", base],
                           capture_output=True, text=True, check=True, env=child_env())
    assert "red" in shown.stdout


def test_a_verdict_fetched_after_the_listing_is_not_dropped(repo, monkeypatch):
    """Gaze round 9: the remote listing says no verdict ref yet; before the stale-ref
    drop, another session fetches the first (red) verdict into the local ref. Dropping
    it would leave no verdict, and the fast path would rest on an older green record."""
    monkeypatch.chdir(repo)
    mg = load_monitor().mg
    ref = mg.VERDICT_REF
    base = git(repo, "rev-parse", "HEAD")
    real_git, arrived = mg.git, []

    def interleaved(*args, **kwargs):
        result = real_git(*args, **kwargs)
        if args[:1] == ("ls-remote",) and not arrived:
            arrived.append(True)
            real_git("notes", f"--ref={ref}", "append", "-m", "red", base)  # the other session's fetch
        return result

    monkeypatch.setattr(mg, "git", interleaved)
    assert mg.fetch_notes("origin", ref) is False
    assert arrived
    assert "red" in mg.read_note(base, ref)


def _notes_session(repo, monkeypatch):
    monkeypatch.chdir(repo)
    mg = load_monitor().mg
    return mg, mg.VERDICT_REF, git(repo, "rev-parse", "HEAD")


def test_a_stale_local_verdict_the_remote_lacks_is_dropped(repo, monkeypatch):
    mg, ref, base = _notes_session(repo, monkeypatch)
    mg.git("notes", f"--ref={ref}", "append", "-m", "green, never published", base)
    assert mg.fetch_notes("origin", ref) is False
    assert mg.local_ref(ref) == ""


def test_a_local_verdict_that_moved_after_the_listing_is_kept(repo, monkeypatch):
    mg, ref, base = _notes_session(repo, monkeypatch)
    mg.git("notes", f"--ref={ref}", "append", "-m", "stale", base)
    real_git, moved = mg.git, []

    def interleaved(*args, **kwargs):
        result = real_git(*args, **kwargs)
        if args[:1] == ("ls-remote",) and not moved:
            moved.append(True)
            real_git("notes", f"--ref={ref}", "append", "-m", "red", base)  # a concurrent fetch
        return result

    monkeypatch.setattr(mg, "git", interleaved)
    mg.fetch_notes("origin", ref)
    assert moved and "red" in mg.read_note(base, ref)


@pytest.mark.parametrize("failing", ["update-ref", "rev-parse"])
def test_an_unreadable_or_undroppable_local_ref_fails_closed(repo, monkeypatch, failing):
    """Gaze round 10: a failed read must not pass for an absent ref, and a failed drop of an
    unmoved stale ref must not be swallowed; either way the gate cannot know the verdict."""
    mg, ref, base = _notes_session(repo, monkeypatch)
    mg.git("notes", f"--ref={ref}", "append", "-m", "green, never published", base)
    real_git = mg.git

    def broken(*args, **kwargs):
        if args[:1] == (failing,):
            return subprocess.CompletedProcess(["git", *args], 124, "", "no answer")
        return real_git(*args, **kwargs)

    monkeypatch.setattr(mg, "git", broken)
    with pytest.raises(mg.GateError):
        mg.fetch_notes("origin", ref)
