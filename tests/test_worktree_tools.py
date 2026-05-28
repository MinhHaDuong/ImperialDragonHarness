"""Tests for the worktree tooling scripts (tickets 0168, 0169).

Exercises:
  - scripts/worktree-salvage.sh        — commit + push WIP before removal
  - scripts/guard-worktree-remove-wip.sh — PreToolUse guard blocking removal on WIP
  - scripts/worktree-gc.sh             — GC stale agent-* worktrees
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or shutil.which("jq") is None,
    reason="git and jq required",
)


def run(args, cwd=None, check=True):
    return subprocess.run(
        args, cwd=cwd, check=check, capture_output=True, text=True
    )


def git(repo, *args, check=True):
    return run(["git", "-C", str(repo), *args], check=check)


@pytest.fixture
def origin(tmp_path):
    """A bare remote plus a primary clone with an initial commit on main."""
    remote = tmp_path / "remote.git"
    run(["git", "init", "--bare", "-b", "main", str(remote)])

    primary = tmp_path / "primary"
    run(["git", "init", "-b", "main", str(primary)])
    git(primary, "config", "user.email", "test@example.com")
    git(primary, "config", "user.name", "Test")
    git(primary, "config", "commit.gpgsign", "false")
    (primary / "README").write_text("hi\n")
    git(primary, "add", "-A")
    git(primary, "commit", "-m", "init")
    git(primary, "remote", "add", "origin", str(remote))
    git(primary, "push", "-u", "origin", "main")
    return remote, primary


def make_agent_worktree(primary, name, *, dirty=False, push=True):
    """Create an agent-* worktree on its own branch; optionally push + leave WIP."""
    wt = primary.parent / name
    git(primary, "worktree", "add", "-b", name, str(wt))
    (wt / "work.txt").write_text("first\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-m", "work")
    if push:
        git(wt, "push", "-u", "origin", name)
    if dirty:
        (wt / "work.txt").write_text("uncommitted change\n")
    return wt


def make_branch_gone(remote, primary, name):
    """Delete the branch on the remote and prune so the local branch reads [gone]."""
    git(remote, "update-ref", "-d", f"refs/heads/{name}")
    git(primary, "fetch", "--prune", "origin")


# --------------------------------------------------------------------------- #
# worktree-salvage.sh
# --------------------------------------------------------------------------- #

def test_salvage_commits_and_pushes_wip(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-salv", dirty=True)

    res = run([str(SCRIPTS / "worktree-salvage.sh"), str(wt)])
    assert res.returncode == 0

    head_msg = git(wt, "log", "-1", "--format=%s").stdout.strip()
    assert head_msg == "WIP: salvaged from interrupted raid"
    assert git(wt, "status", "--porcelain").stdout.strip() == ""
    # Pushed: remote tip matches local HEAD.
    local = git(wt, "rev-parse", "HEAD").stdout.strip()
    remote_tip = git(remote, "rev-parse", "refs/heads/agent-salv").stdout.strip()
    assert local == remote_tip


def test_salvage_clean_tree_is_noop(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-clean", dirty=False)
    before = git(wt, "rev-parse", "HEAD").stdout.strip()

    res = run([str(SCRIPTS / "worktree-salvage.sh"), str(wt)])
    assert res.returncode == 0
    assert "nothing to salvage" in res.stdout
    assert git(wt, "rev-parse", "HEAD").stdout.strip() == before


def test_salvage_missing_arg_errors(origin):
    res = run([str(SCRIPTS / "worktree-salvage.sh")], check=False)
    assert res.returncode == 2


# --------------------------------------------------------------------------- #
# guard-worktree-remove-wip.sh
# --------------------------------------------------------------------------- #

def _guard(cmd, cwd=None):
    body = {"tool_name": "Bash", "tool_input": {"command": cmd}}
    if cwd is not None:
        body["cwd"] = str(cwd)
    payload = json.dumps(body)
    return subprocess.run(
        ["bash", str(SCRIPTS / "guard-worktree-remove-wip.sh")],
        input=payload, capture_output=True, text=True,
    )


def test_guard_blocks_remove_with_wip(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-dirty", dirty=True)
    res = _guard(f"git worktree remove --force {wt}")
    assert res.returncode == 2
    assert "uncommitted WIP" in res.stderr


def test_guard_allows_remove_when_clean(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-ok", dirty=False)
    res = _guard(f"git worktree remove {wt}")
    assert res.returncode == 0
    assert res.stderr == ""


def test_guard_ignores_unrelated_command(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-x", dirty=True)
    # Not a worktree-remove command — must not block even with a dirty path.
    res = _guard(f"git worktree list {wt}")
    assert res.returncode == 0


def test_guard_allows_nonexistent_path():
    res = _guard("git worktree remove /no/such/worktree/path")
    assert res.returncode == 0


def test_guard_resolves_relative_path_against_json_cwd(origin):
    """A relative path should resolve against the PreToolUse JSON .cwd, not
    the hook's own cwd. Otherwise dirty removes via relative paths slip past."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-rel", dirty=True)
    # Command uses a relative path; cwd is primary's parent (the tmp dir).
    res = _guard(f"git worktree remove --force {wt.name}", cwd=wt.parent)
    assert res.returncode == 2
    assert "uncommitted WIP" in res.stderr


def test_guard_handles_malformed_json():
    """Bad JSON on stdin should exit cleanly, not abort the script with set -e."""
    res = subprocess.run(
        ["bash", str(SCRIPTS / "guard-worktree-remove-wip.sh")],
        input="not json{", capture_output=True, text=True,
    )
    assert res.returncode == 0
    assert res.stderr == ""


# --------------------------------------------------------------------------- #
# worktree-gc.sh
# --------------------------------------------------------------------------- #

def _gc(primary):
    return run([str(SCRIPTS / "worktree-gc.sh"), str(primary)])


def _worktree_paths(primary):
    out = git(primary, "worktree", "list", "--porcelain").stdout
    return [l[len("worktree "):] for l in out.splitlines() if l.startswith("worktree ")]


def test_gc_removes_gone_clean_agent_worktree(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-gone", dirty=False)
    make_branch_gone(remote, primary, "agent-gone")

    res = _gc(primary)
    assert res.returncode == 0
    assert "removed agent-gone" in res.stdout
    assert str(wt) not in _worktree_paths(primary)


def test_gc_keeps_dirty_worktree(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-wip", dirty=True)
    make_branch_gone(remote, primary, "agent-wip")

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-wip (uncommitted WIP)" in res.stdout
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_live_branch_worktree(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-live", dirty=False)  # branch still on origin

    res = _gc(primary)
    assert res.returncode == 0
    assert str(wt) in _worktree_paths(primary)


def test_gc_ignores_non_agent_worktree(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "feature-x", dirty=False)
    make_branch_gone(remote, primary, "feature-x")

    res = _gc(primary)
    assert res.returncode == 0
    assert str(wt) in _worktree_paths(primary)


def test_gc_silent_when_nothing_to_do(origin):
    _, primary = origin
    res = _gc(primary)
    assert res.returncode == 0
    assert res.stdout.strip() == ""


def test_gc_unlocks_and_removes_locked_gone_worktree(origin):
    """A locked but unlockable agent-* worktree on a gone branch should be
    unlocked and removed — exercises the locked-branch code path."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-locked", dirty=False)
    git(primary, "worktree", "lock", str(wt))
    make_branch_gone(remote, primary, "agent-locked")

    res = _gc(primary)
    assert res.returncode == 0
    assert "removed agent-locked" in res.stdout
    assert str(wt) not in _worktree_paths(primary)
