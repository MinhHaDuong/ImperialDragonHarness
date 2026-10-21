"""Daily audit of main: does each commit that entered it carry a gate receipt?

Ticket 1179 (after 1157, tracker 1045). The receipt is the merge gate's note
in refs/notes/gate on the deterministic candidate commit (scripts/merge-gate.py).
The forge's merge commit is a different object, so the audit rebuilds the
candidate from the merge's two parents and reads the note there. Every case
runs the script on a scratch repository whose receipts are written by the
real merge gate; no forge is involved.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "main_sweep.py"
GATE = ROOT / "scripts" / "merge-gate.py"
GATE_JSON = '{"gate": "on", "scope": "s", "checks": [{"name": "t", "argv": ["true"]}]}\n'


def _env(**extra):
    env = {k: v for k, v in child_env().items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="F", GIT_AUTHOR_EMAIL="f@example.invalid",
        GIT_COMMITTER_NAME="F", GIT_COMMITTER_EMAIL="f@example.invalid",
    )
    env.update(extra)
    return env


def git(cwd, *args, **extra):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True,
        env=_env(**extra), check=True,
    ).stdout.strip()


def audit(repo, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--ref", "main", *args],
        capture_output=True, text=True, env=_env(), cwd=repo,
    )


@pytest.fixture
def repo(tmp_path):
    """A gated repository (.merge-gate.json on main) with a bare origin for receipts."""
    r = tmp_path / "r"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    (r / ".merge-gate.json").write_text(GATE_JSON)
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "gate on")
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(r, "remote", "add", "origin", str(origin))
    git(r, "push", "-q", "origin", "main")
    return r


def branch(r, name):
    git(r, "switch", "-q", "-c", name, "main")
    (r / name).write_text(name + "\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", name)
    git(r, "switch", "-q", "main")


def receipt(r, name):
    """The real merge gate writes a passing receipt on the candidate (main + name)."""
    proc = subprocess.run(
        [sys.executable, str(GATE), "run", "--base", "main", "--head", name],
        capture_output=True, text=True, env=_env(), cwd=r,
    )
    assert proc.returncode == 0, proc.stderr


def forge_merge(r, name, **extra):
    """A --no-ff merge with the forge's metadata, not the candidate's."""
    env = dict(GIT_AUTHOR_NAME="Forge", GIT_COMMITTER_NAME="Forge", **extra)
    git(r, "merge", "-q", "--no-ff", name, "-m", f"Merge pull request from {name}", **env)
    return git(r, "rev-parse", "HEAD")


def line_of(proc, sha):
    [line] = [x for x in proc.stdout.splitlines() if sha[:12] in x]
    return line


def test_a_forge_merge_with_a_receipt_on_its_candidate_reads_as_ok(repo):
    branch(repo, "a")
    receipt(repo, "a")
    merge = forge_merge(repo, "a")
    proc = audit(repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert line_of(proc, merge).startswith("ok")


def test_a_receipt_made_on_another_base_is_a_finding(repo):
    branch(repo, "a")
    receipt(repo, "a")
    branch(repo, "b")
    forge_merge(repo, "b")  # main moved after a's receipt was written
    merge = forge_merge(repo, "a")
    proc = audit(repo)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert line_of(proc, merge).startswith("finding")


def test_a_merge_without_a_receipt_is_a_finding(repo):
    branch(repo, "a")
    merge = forge_merge(repo, "a")
    proc = audit(repo)
    assert proc.returncode == 1
    assert line_of(proc, merge).startswith("finding")


def test_a_single_parent_commit_reads_its_own_note(repo):
    (repo / "direct").write_text("direct\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "direct push")
    direct = git(repo, "rev-parse", "HEAD")
    assert line_of(audit(repo), direct).startswith("finding")
    git(repo, "notes", "--ref=refs/notes/gate", "add", "-m", "record", direct)
    assert line_of(audit(repo), direct).startswith("ok")


def test_the_summary_is_one_line_naming_the_first_finding(repo):
    branch(repo, "a")
    receipt(repo, "a")
    forge_merge(repo, "a")
    branch(repo, "b")
    merge = forge_merge(repo, "b")
    proc = audit(repo, "--summary")
    assert proc.returncode == 1
    assert proc.stdout.splitlines() == [
        f"main audit: 3 merges in the last 24 h, 1 without a gate receipt: {merge[:12]}"
    ]


def test_commits_older_than_24_hours_are_outside_the_window(repo):
    old = "@%d +0000" % (int(git(repo, "log", "-1", "--format=%ct")) - 3 * 86400)
    branch(repo, "a")
    forge_merge(repo, "a", GIT_COMMITTER_DATE=old, GIT_AUTHOR_DATE=old)
    branch(repo, "b")
    receipt(repo, "b")
    forge_merge(repo, "b")
    proc = audit(repo, "--summary")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 merges in the last 24 h, 0 without" in proc.stdout


@pytest.mark.parametrize("cap", [["--max-count", "1"], ["--time-limit", "0"]])
def test_a_range_cut_by_a_cap_says_so_and_exits_2(repo, cap):
    branch(repo, "a")
    receipt(repo, "a")
    forge_merge(repo, "a")
    proc = audit(repo, "--summary", *cap)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "range cut" in proc.stdout


def test_a_repository_without_a_gate_prints_nothing(tmp_path):
    r = tmp_path / "plain"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    git(r, "commit", "-q", "--allow-empty", "-m", "no gate")
    for args in ([], ["--summary"]):
        proc = audit(r, *args)
        assert (proc.returncode, proc.stdout) == (0, ""), proc.stderr
