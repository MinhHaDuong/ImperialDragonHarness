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
import time
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "main_sweep.py"
GATE = ROOT / "scripts" / "merge-gate.py"
GATE_JSON = '{"gate": "on", "scope": "s", "checks": [{"name": "t", "argv": ["%s"]}]}\n'
DAYS_AGO_3 = "@%d +0000" % (int(time.time()) - 3 * 86400)


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
    """Root commit 3 days old, then the gate turned on today; a bare origin takes receipts."""
    r = tmp_path / "r"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    git(r, "commit", "-q", "--allow-empty", "-m", "init", GIT_COMMITTER_DATE=DAYS_AGO_3)
    gate(r, "true")
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(r, "remote", "add", "origin", str(origin))
    git(r, "push", "-q", "origin", "main")
    return r


def gate(r, check, message="gate on"):
    """Declare the gate on main with one check command (`true` passes, `false` fails)."""
    (r / ".merge-gate.json").write_text(GATE_JSON % check)
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", message)


def commit(r, name, **extra):
    (r / name).write_text(name + "\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", name, **extra)
    return git(r, "rev-parse", "HEAD")


def branch(r, name):
    git(r, "switch", "-q", "-c", name, "main")
    commit(r, name)
    git(r, "switch", "-q", "main")


def receipt(r, name, expect=0):
    """The real merge gate writes a receipt on the candidate (main + name)."""
    proc = subprocess.run(
        [sys.executable, str(GATE), "run", "--base", "main", "--head", name],
        capture_output=True, text=True, env=_env(), cwd=r,
    )
    assert proc.returncode == expect, proc.stderr


def forge_merge(r, *names, **extra):
    """A --no-ff merge with the forge's metadata, not the candidate's."""
    env = dict(GIT_AUTHOR_NAME="Forge", GIT_COMMITTER_NAME="Forge", **extra)
    git(r, "merge", "-q", "--no-ff", *names, "-m", "Merge pull request", **env)
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


def test_a_failing_receipt_is_a_finding(repo):
    gate(repo, "false", "gate with a failing check")
    branch(repo, "a")
    receipt(repo, "a", expect=1)
    merge = forge_merge(repo, "a")
    proc = audit(repo)
    assert proc.returncode == 1
    assert line_of(proc, merge).startswith("finding")


def test_a_merge_whose_tree_differs_from_the_candidate_is_a_finding(repo):
    branch(repo, "a")
    receipt(repo, "a")
    git(repo, "merge", "-q", "--no-ff", "--no-commit", "a")
    (repo / "extra").write_text("not gated\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Merge a, edited")
    merge = git(repo, "rev-parse", "HEAD")
    proc = audit(repo)
    assert proc.returncode == 1
    assert line_of(proc, merge).startswith("finding")


def test_an_octopus_merge_on_a_two_parent_receipt_is_a_finding(repo):
    branch(repo, "a")
    receipt(repo, "a")
    git(repo, "switch", "-q", "-c", "c", "main")
    git(repo, "commit", "-q", "--allow-empty", "-m", "c")  # same tree as the candidate
    git(repo, "switch", "-q", "main")
    merge = forge_merge(repo, "a", "c")
    proc = audit(repo)
    assert proc.returncode == 1
    assert line_of(proc, merge).startswith("finding")


def test_a_single_parent_commit_reads_its_own_note(repo):
    direct = commit(repo, "direct")
    assert line_of(audit(repo), direct).startswith("finding")
    git(repo, "notes", "--ref=refs/notes/gate", "add", "-m", "record", direct)
    assert line_of(audit(repo), direct).startswith("ok")


def test_an_orphan_commit_at_the_tip_is_a_finding(repo):
    git(repo, "switch", "-q", "--orphan", "orphan")
    git(repo, "checkout", "main", "--", ".merge-gate.json")
    git(repo, "commit", "-q", "-m", "orphan")
    orphan = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/heads/main", orphan)
    proc = audit(repo)
    assert proc.returncode == 1
    assert line_of(proc, orphan).startswith("finding")


def test_the_summary_is_one_line_naming_the_first_finding(repo):
    branch(repo, "a")
    receipt(repo, "a")
    forge_merge(repo, "a")
    branch(repo, "b")
    merge = forge_merge(repo, "b")
    proc = audit(repo, "--summary")
    assert proc.returncode == 1
    assert proc.stdout.splitlines() == [
        f"main audit: 3 commits in the last 24 h, 1 without a gate receipt: {merge[:12]}"
    ]


def test_commits_older_than_24_hours_below_the_window_are_left_out(repo):
    init = git(repo, "rev-list", "--max-parents=0", "main")
    proc = audit(repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert init[:12] not in proc.stdout and "gate on" in proc.stdout


def test_an_old_dated_commit_does_not_hide_the_commits_below_it(repo):
    direct = commit(repo, "direct")  # dated now, no receipt
    commit(repo, "backdated", GIT_COMMITTER_DATE=DAYS_AGO_3)
    branch(repo, "a")
    receipt(repo, "a")
    forge_merge(repo, "a")
    proc = audit(repo)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert line_of(proc, direct).startswith("finding")


@pytest.mark.parametrize("cap", [["--max-count", "1"], ["--time-limit", "0"]])
def test_a_range_cut_by_a_cap_says_so_and_exits_2(repo, cap):
    branch(repo, "a")
    receipt(repo, "a")
    forge_merge(repo, "a")
    proc = audit(repo, "--summary", *cap)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "range cut" in proc.stdout


def test_a_failed_fetch_is_could_not_look(repo, tmp_path):
    git(repo, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    assert audit(repo, "--fetch").returncode == 2


def test_an_unreadable_declaration_is_could_not_look(repo):
    (repo / ".merge-gate.json").write_text("{not json")
    git(repo, "commit", "-q", "-am", "broken declaration")
    assert audit(repo).returncode == 2


def test_an_unknown_ref_is_could_not_look(repo):
    assert audit(repo, "--ref", "no-such-branch").returncode == 2


def test_a_cap_below_one_is_refused(repo):
    assert audit(repo, "--max-count", "0").returncode == 2


def test_a_repository_without_a_gate_prints_nothing(tmp_path):
    r = tmp_path / "plain"
    git(tmp_path, "init", "-q", "-b", "main", str(r))
    git(r, "commit", "-q", "--allow-empty", "-m", "no gate")
    for args in ([], ["--summary"], ["--fetch"]):
        proc = audit(r, *args)
        assert (proc.returncode, proc.stdout) == (0, ""), proc.stderr


def test_a_bookkeeping_merge_with_its_tier_receipt_reads_as_ok(repo):
    """Ticket 1221: a tickets/STATE/memory-only merge carries a tier receipt."""
    (repo / ".merge-gate.json").write_text(
        '{"gate": "on", "scope": "s", "checks": [{"name": "t", "argv": ["true"]},'
        ' {"name": "full", "argv": ["false"]}], "tiers": {"bookkeeping": ["t"]}}\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tiers")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "switch", "-q", "-c", "books", "main")
    commit(repo, "STATE.md")
    git(repo, "switch", "-q", "main")
    receipt(repo, "books")
    merge = forge_merge(repo, "books")
    proc = audit(repo)
    assert line_of(proc, merge).startswith("ok"), proc.stdout + proc.stderr
