"""verify-gate's check plan: reuse prior results, scope checks to the diff (ticket 1220).

`merge-gate.py plan` prints, before anything runs, one line per declared check
(`run`, `reuse` or `skip`, with the reason) and one for the adherence result.
A prior result is a gate record entry for the `--since` head; it is reused
only when what changed between its candidate and the current one is
bookkeeping (rules/git.md § Gating tiers). Every fixture is a local
repository with a bare origin: no forge, no network.
"""

import json
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "merge-gate.py"

CONFIG = {
    "gate": "on",
    "scope": "plan-set",
    "checks": [
        {"name": "ticket-check", "argv": ["true"]},
        {"name": "suite", "argv": ["sh", "-c", "! test -e FAIL_MARKER"]},
        {"name": "integ", "argv": ["true"], "integration": True, "covers": ["it/"]},
    ],
    "tiers": {"bookkeeping": ["ticket-check", "suite"]},
    "rerun": {"bookkeeping": ["ticket-check"]},
}


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        env=child_env(),
    ).stdout.strip()


def gate(cwd, *args):
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=child_env(),
    )


def commit(repo, *paths, message="change"):
    for path in paths:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(f"{path} {message}\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    subprocess.run(
        ["git", "init", "-q", "--bare", str(origin)], check=True, env=child_env()
    )
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(work)], check=True, env=child_env()
    )
    for key, value in (
        ("user.email", "t@example.com"),
        ("user.name", "Fixture"),
        ("commit.gpgsign", "false"),
    ):
        git(work, "config", key, value)
    (work / ".merge-gate.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    commit(work, "a.txt", message="base")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    git(work, "switch", "-q", "-c", "feature")
    commit(work, "src/code.py", message="feature")
    return work


def record(repo):
    """Run and publish the gate record on the current feature head; return that head."""
    run = gate(repo, "run", "--base", "main", "--head", "feature")
    assert run.returncode in (0, 1), run.stderr
    return git(repo, "rev-parse", "feature")


def plan(repo, *extra):
    result = gate(repo, "plan", "--base", "main", "--head", "feature", *extra)
    assert result.returncode == 0, result.stdout + result.stderr
    actions = {}
    for line in result.stdout.splitlines():
        action, _, rest = line.partition(" ")
        if action in ("run", "reuse", "skip"):
            name, _, reason = rest.partition(": ")
            actions[name] = (action, reason)
    return actions, result.stdout


def names(actions, kind):
    """Declared checks planned as `kind`; the adherence line is asserted on its own."""
    return {
        name
        for name, (action, _) in actions.items()
        if action == kind and name != "adherence"
    }


def test_ticket_only_delta_reuses_the_prior_green_result_and_runs_only_the_ticket_check(
    repo,
):
    prior = record(repo)
    commit(repo, "tickets/0001-x.erg", message="ticket log")
    actions, out = plan(repo, "--since", prior)
    assert names(actions, "run") == {"ticket-check"}, out
    assert names(actions, "reuse") == {"suite", "integ"}, out
    for name in ("suite", "integ"):
        assert prior in actions[name][1], out  # the reuse names its source head
    assert "bookkeeping" in actions["suite"][1], out


def test_code_delta_invalidates_the_reuse(repo):
    prior = record(repo)
    commit(repo, "src/more.py", message="code")
    actions, out = plan(repo, "--since", prior)
    assert names(actions, "reuse") == set(), out
    assert names(actions, "run") == {"ticket-check", "suite"}, out
    assert names(actions, "skip") == {"integ"}, out
    assert "src/more.py" in actions["suite"][1], out


def test_unchanged_head_reuses_every_passed_check(repo):
    prior = record(repo)
    actions, out = plan(repo, "--since", prior)
    assert names(actions, "reuse") == {"ticket-check", "suite", "integ"}, out
    assert names(actions, "run") == set(), out


def test_a_failed_prior_check_is_never_reused(repo):
    commit(repo, "FAIL_MARKER", message="break")
    prior = record(repo)
    commit(repo, "tickets/0001-x.erg", message="ticket log")
    actions, out = plan(repo, "--since", prior)
    assert actions["suite"][0] == "run", out
    assert actions["integ"][0] == "reuse", out


def test_a_code_change_on_the_base_invalidates_the_reuse(repo):
    prior = record(repo)
    git(repo, "switch", "-q", "main")
    commit(repo, "src/base.py", message="base moved")
    git(repo, "switch", "-q", "feature")
    actions, out = plan(repo, "--since", prior)
    assert names(actions, "reuse") == set(), out


def test_a_bookkeeping_change_on_the_base_keeps_the_reuse(repo):
    prior = record(repo)
    git(repo, "switch", "-q", "main")
    commit(repo, "STATE.md", message="state")
    git(repo, "switch", "-q", "feature")
    actions, out = plan(repo, "--since", prior)
    assert names(actions, "run") == {"ticket-check"}, out
    assert names(actions, "reuse") == {"suite", "integ"}, out


def test_without_a_prior_record_every_check_runs(repo):
    actions, out = plan(repo, "--since", git(repo, "rev-parse", "feature"))
    assert names(actions, "run") == {"ticket-check", "suite"}, out
    assert "no record" in actions["suite"][1], out
    actions, out = plan(repo)
    assert names(actions, "run") == {"ticket-check", "suite"}, out


def test_integration_check_runs_when_the_diff_touches_what_it_covers(repo):
    commit(repo, "it/harness.py", message="integ code")
    actions, out = plan(repo)
    assert actions["integ"][0] == "run", out
    assert "it/harness.py" in actions["integ"][1], out


def test_integration_check_runs_when_the_caller_asks(repo):
    actions, out = plan(repo, "--integration")
    assert actions["integ"][0] == "run", out
    assert "--integration" in actions["integ"][1], out


def test_the_plan_names_no_separate_adherence_result(repo):
    """Ticket 1225: adherence is a check of the gate record, not a gaze result to reuse."""
    actions, out = plan(repo)
    assert "adherence" not in actions, out


def test_the_plan_is_printed_before_any_check_runs(repo):
    commit(repo, "FAIL_MARKER", message="would fail if run")
    result = gate(repo, "plan", "--base", "main", "--head", "feature")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("plan: ")


@pytest.mark.parametrize(
    "patch",
    [
        {"rerun": {"bookkeeping": ["no-such-check"]}},
        {"rerun": {"full": ["suite"]}},
        {"rerun": ["ticket-check"]},
        {"checks": [{"name": "x", "argv": ["true"], "integration": "yes"}]},
        {"checks": [{"name": "x", "argv": ["true"], "covers": "it/"}]},
    ],
)
def test_bad_plan_declarations_fail_closed(repo, patch):
    config = {**CONFIG, **patch}
    if "checks" in patch:
        config.pop("tiers")
        config.pop("rerun")
    git(repo, "switch", "-q", "main")
    (repo / ".merge-gate.json").write_text(json.dumps(config), encoding="utf-8")
    git(repo, "commit", "-q", "-am", "config")
    git(repo, "switch", "-q", "feature")
    assert gate(repo, "plan", "--base", "main", "--head", "feature").returncode == 3
