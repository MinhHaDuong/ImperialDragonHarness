"""Ticket 1490: a gate round that stalls records no verdict and leaves its
`gate-<pr>-<session>-r<round>` tree behind; the relaunch under the same session
recomputes the same path and `git worktree add` failed, so the gate escalated.
`gate_tree.py add` replaces such a stale tree through the removal preflight,
and still refuses a tree holding residue, a locked one, or a round whose
verdict is already recorded."""

import json
import subprocess
from pathlib import Path

import pytest
from run_checked import run_checked

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "gate_tree.py"
SESSION = "11111111-2222-3333-4444-555555555555"


def git(repo, *args):
    return run_checked(["git", "-C", str(repo), *args]).stdout.strip()


def repo(tmp_path):
    """A primary repo ignoring `*.stamp`, with two commits."""
    primary = tmp_path / "primary"
    primary.mkdir()
    git(primary, "init", "-b", "main")
    git(primary, "config", "user.email", "t@example.com")
    git(primary, "config", "user.name", "T")
    (primary / ".gitignore").write_text("*.stamp\n")
    git(primary, "add", ".gitignore")
    git(primary, "commit", "-m", "base")
    (primary / "a.txt").write_text("a\n")
    git(primary, "add", "a.txt")
    git(primary, "commit", "-m", "head")
    return primary


def gate_path(primary, rnd=1):
    return primary / ".claude" / "worktrees" / f"gate-7-{SESSION}-r{rnd}"


def add(primary, tree, ref="HEAD", rnd=1, state=None, tmp_path=None):
    cmd = ["python3", str(HELPER), "add", "--repo", str(primary), "--tree", str(tree),
           "--ref", ref, "--session", SESSION, "--round", str(rnd)]
    if state is not None:
        f = tmp_path / "state.json"
        f.write_text(json.dumps(state))
        cmd += ["--gate-state", str(f)]
    return subprocess.run(cmd, capture_output=True, text=True)


def stale(primary, ref="HEAD~1"):
    """A round-1 tree left behind by a stalled run, on an older head."""
    tree = gate_path(primary)
    r = add(primary, tree, ref)
    assert r.returncode == 0, r.stderr
    return tree


def test_fresh_tree_is_created_detached_at_the_ref(tmp_path):
    primary = repo(tmp_path)
    tree = gate_path(primary)
    r = add(primary, tree)
    assert r.returncode == 0, r.stderr
    assert git(tree, "rev-parse", "HEAD") == git(primary, "rev-parse", "HEAD")
    assert subprocess.run(["git", "-C", str(tree), "symbolic-ref", "-q", "HEAD"]).returncode != 0


def test_stale_tree_without_verdict_is_replaced(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    (tree / "out.stamp").write_text("built\n")  # ignored build output of the stalled run
    r = add(primary, tree)
    assert r.returncode == 0, r.stderr
    assert git(tree, "rev-parse", "HEAD") == git(primary, "rev-parse", "HEAD")
    assert not (tree / "out.stamp").exists()


def test_stale_tree_with_a_verdict_of_another_session_or_round_is_replaced(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    state = {"verdicts": [{"round": 1, "session": "99999999-2222-3333-4444-555555555555"},
                          {"round": 2, "session": SESSION}]}
    r = add(primary, tree, state=state, tmp_path=tmp_path)
    assert r.returncode == 0, r.stderr
    assert git(tree, "rev-parse", "HEAD") == git(primary, "rev-parse", "HEAD")


def test_recorded_verdict_for_the_session_and_round_refuses(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    state = {"verdicts": [{"round": 1, "session": SESSION, "verdict": "APPROVED"}]}
    r = add(primary, tree, state=state, tmp_path=tmp_path)
    assert r.returncode == 1
    assert "verdict" in r.stderr
    assert git(tree, "rev-parse", "HEAD") == git(primary, "rev-parse", "HEAD~1")


def test_unignored_residue_refuses_and_keeps_the_tree(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    (tree / "draft.txt").write_text("wip\n")
    r = add(primary, tree)
    assert r.returncode == 1
    assert "draft.txt" in r.stderr
    assert (tree / "draft.txt").read_text() == "wip\n"


def test_modified_tracked_file_refuses(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    (tree / ".gitignore").write_text("changed\n")
    r = add(primary, tree)
    assert r.returncode == 1
    assert (tree / ".gitignore").read_text() == "changed\n"


def test_locked_tree_refuses(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    git(primary, "worktree", "lock", "--reason", "live", str(tree))
    r = add(primary, tree)
    assert r.returncode == 1
    assert "locked" in r.stderr
    assert tree.is_dir()


def test_registered_but_missing_tree_is_recreated(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    run_checked(["rm", "-rf", str(tree)])
    r = add(primary, tree)
    assert r.returncode == 0, r.stderr
    assert git(tree, "rev-parse", "HEAD") == git(primary, "rev-parse", "HEAD")


def test_directory_that_is_not_a_worktree_of_the_repo_refuses(tmp_path):
    primary = repo(tmp_path)
    tree = gate_path(primary)
    tree.mkdir(parents=True)
    (tree / "keep.txt").write_text("x\n")
    r = add(primary, tree)
    assert r.returncode == 1
    assert (tree / "keep.txt").exists()


def test_a_tree_not_named_gate_is_refused(tmp_path):
    primary = repo(tmp_path)
    r = add(primary, primary / ".claude" / "worktrees" / "t7-x")
    assert r.returncode == 2


def test_unreadable_gate_state_refuses_without_a_traceback(tmp_path):
    primary = repo(tmp_path)
    tree = stale(primary)
    f = tmp_path / "state.json"
    f.write_text("not json")
    r = subprocess.run(["python3", str(HELPER), "add", "--repo", str(primary), "--tree", str(tree),
                        "--ref", "HEAD", "--session", SESSION, "--round", "1",
                        "--gate-state", str(f)], capture_output=True, text=True)
    assert r.returncode == 1
    assert "Traceback" not in r.stderr and "unreadable gate state" in r.stderr
    assert git(tree, "rev-parse", "HEAD") == git(primary, "rev-parse", "HEAD~1")


def test_a_commit_only_the_stale_tree_reaches_refuses(tmp_path):
    """Gaze finding: the preflight sees uncommitted files, never commits; a
    local commit on the detached tree would vanish with it."""
    primary = repo(tmp_path)
    tree = stale(primary)
    git(tree, "commit", "--allow-empty", "-m", "local only")
    local = git(tree, "rev-parse", "HEAD")
    r = add(primary, tree)
    assert r.returncode == 1
    assert "not reachable" in r.stderr
    assert git(tree, "rev-parse", "HEAD") == local


def test_a_missing_tree_whose_head_only_it_reaches_refuses(tmp_path):
    """Gaze round 2: with the directory gone, git's registration still holds
    the only reference to a local commit; removing it would drop that commit."""
    primary = repo(tmp_path)
    tree = stale(primary)
    git(tree, "commit", "--allow-empty", "-m", "local only")
    local = git(tree, "rev-parse", "HEAD")
    run_checked(["rm", "-rf", str(tree)])
    r = add(primary, tree)
    assert r.returncode == 1
    assert "not reachable" in r.stderr
    assert local in git(primary, "rev-list", "--all")
