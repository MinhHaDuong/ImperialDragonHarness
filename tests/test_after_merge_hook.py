"""The reference-transaction hook starts the after-merge runner (ticket 1265, tracker 1226).

On a committed move of `refs/heads/main` to a tip that declares the merge gate,
`hooks/reference-transaction` starts `merge-gate.py run-after --open-ticket
--ref main` detached, from the shared git directory, and never delays or fails
the ref update. Here the runner is a stub that records its start and sleeps:
real git, a scratch clone with `core.hooksPath=hooks`, HOME a temp directory.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "reference-transaction"
STUB_SLEEP = 8  # seconds the stub runner lives: an update waiting on it would show

STUB = """\
import json, os, sys, time
if sys.argv[1:2] != ["run-after"]:
    raise SystemExit(1)  # the guard's own `candidate` call at `prepared`: no receipt
with open({record!r}, "a") as fh:
    fh.write(json.dumps({{"argv": sys.argv[1:], "cwd": os.getcwd(),
                         "leader": os.getsid(0) == os.getpid(),
                         "git_dir": os.environ.get("GIT_DIR")}}) + "\\n")
time.sleep({sleep})
"""


def _env(home):
    env = {k: v for k, v in child_env().items() if not k.startswith("GIT_") and k != "IDH_ROOT"}
    env.update(
        HOME=str(home),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_NAME="Fixture",
        GIT_COMMITTER_EMAIL="fixture@example.invalid",
        LC_ALL="C",
    )
    return env


@pytest.fixture
def repo(tmp_path):
    """origin (bare); work: a clone with the hook, a stub runner and a gated tree; side: a commit to move main to."""
    home = tmp_path / "home"
    home.mkdir()
    env = _env(home)
    record = tmp_path / "started.jsonl"

    def git(cwd, *args, check=True):
        proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env)
        if check and proc.returncode != 0:
            raise AssertionError(f"git {args} failed: {proc.stderr}")
        return proc

    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    work = tmp_path / "work"
    git(tmp_path, "init", "-q", "-b", "main", str(work))
    (work / "hooks").mkdir()
    shutil.copy2(HOOK, work / "hooks" / "reference-transaction")
    (work / "scripts").mkdir()
    (work / "scripts" / "merge-gate.py").write_text(STUB.format(record=str(record), sleep=STUB_SLEEP))
    (work / ".merge-gate.json").write_text('{"gate": "on", "scope": "s", "checks": []}\n')
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "seed")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    git(work, "config", "core.hooksPath", "hooks")
    git(work, "switch", "-q", "-c", "side")
    (work / "side.txt").write_text("side\n")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "side")
    git(work, "switch", "-q", "main")
    common = Path(git(work, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    return {"git": git, "work": work, "record": record, "common": common, "env": env,
            "side": git(work, "rev-parse", "side").stdout.strip(), "tmp": tmp_path}


def starts(r, settle=1.5, expect=0):
    """The stub's start records, waiting up to 10 s for `expect` of them, then `settle` s for any extra."""
    end = time.monotonic() + 10
    while expect and time.monotonic() < end:
        if r["record"].exists() and len(r["record"].read_text().splitlines()) >= expect:
            break
        time.sleep(0.05)
    time.sleep(settle)
    if not r["record"].exists():
        return []
    return [json.loads(line) for line in r["record"].read_text().splitlines()]


def one_start(r):
    found = starts(r, expect=1)
    assert len(found) == 1, f"expected the runner started once, got {len(found)} start(s)"
    return found[0]


def timed(r, *args, cwd=None):
    began = time.monotonic()
    proc = r["git"](cwd or r["work"], *args, check=False)
    return proc, time.monotonic() - began


def test_a_committed_move_of_main_starts_the_runner_once_detached(repo):
    proc, took = timed(repo, "update-ref", "refs/heads/main", repo["side"])
    assert proc.returncode == 0, proc.stderr
    assert took < STUB_SLEEP / 2, f"the update waited {took:.1f} s on the runner"
    start = one_start(repo)
    assert start["argv"] == ["run-after", "--open-ticket", "--ref", "main"]
    assert Path(start["cwd"]).resolve() == repo["common"].resolve()
    assert start["git_dir"] is None  # the runner finds the repository from the shared git dir alone
    if shutil.which("setsid"):
        assert start["leader"], "runner not in a session of its own"
    assert (repo["common"] / "idh" / "after-merge.log").exists()


def test_a_move_from_a_linked_worktree_runs_from_the_shared_git_dir(repo):
    linked = repo["tmp"] / "linked"
    repo["git"](repo["work"], "worktree", "add", "-q", "--detach", str(linked), "side")
    proc, _ = timed(repo, "update-ref", "refs/heads/main", repo["side"], cwd=linked)
    assert proc.returncode == 0, proc.stderr
    start = one_start(repo)
    assert Path(start["cwd"]).resolve() == repo["common"].resolve()


def test_a_commit_on_main_starts_the_runner(repo):
    (repo["work"] / "local.txt").write_text("local\n")
    repo["git"](repo["work"], "add", "-A")
    proc, took = timed(repo, "commit", "-q", "-m", "local on main")
    assert proc.returncode == 0, proc.stderr
    assert took < STUB_SLEEP / 2
    one_start(repo)


@pytest.mark.parametrize("case", ["other-ref", "deletion", "ungated-tip", "disabled"])
def test_no_start_without_a_committed_move_of_main_to_a_gated_tip(repo, case):
    git, work = repo["git"], repo["work"]
    if case == "other-ref":
        proc = git(work, "update-ref", "refs/heads/other", repo["side"], check=False)
    elif case == "deletion":
        git(work, "switch", "-q", "side")
        proc = git(work, "update-ref", "-d", "refs/heads/main", check=False)
    elif case == "ungated-tip":
        git(work, "switch", "-q", "side")
        git(work, "rm", "-q", ".merge-gate.json")
        git(work, "commit", "-q", "-m", "no gate")
        proc = git(work, "update-ref", "refs/heads/main", "side", check=False)
    else:
        git(work, "config", "idh.afterMerge", "off")
        proc = git(work, "update-ref", "refs/heads/main", repo["side"], check=False)
    assert proc.returncode == 0, proc.stderr
    assert starts(repo) == []


@pytest.mark.parametrize("failure", ["runner-missing", "runner-crashes", "log-unwritable"])
def test_the_update_succeeds_when_the_runner_fails_to_start(repo, failure):
    runner = repo["work"] / "scripts" / "merge-gate.py"
    if failure == "runner-missing":
        runner.unlink()
    elif failure == "runner-crashes":
        runner.write_text("raise SystemExit(3)\n")
    else:
        (repo["common"] / "idh").mkdir(exist_ok=True)
        (repo["common"] / "idh" / "after-merge.log").mkdir()  # a directory: the redirect fails
    proc, took = timed(repo, "update-ref", "refs/heads/main", repo["side"])
    assert proc.returncode == 0, proc.stderr
    assert took < STUB_SLEEP / 2
    assert repo["git"](repo["work"], "rev-parse", "main").stdout.strip() == repo["side"]
    assert "Traceback" not in proc.stderr


def test_git_pack_refs_starts_no_runner(repo):
    # pack-refs writes main into packed-refs as a transaction `0 -> value`: a
    # no-op create, not a move (ticket 1268).
    proc, _ = timed(repo, "pack-refs", "--all", "--prune")
    assert proc.returncode == 0, proc.stderr
    assert starts(repo) == []
