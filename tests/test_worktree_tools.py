"""Tests for the worktree tooling scripts (tickets 0168, 0169, 0174).

Exercises:
  - scripts/worktree-salvage.sh         — commit + push WIP before removal
  - scripts/guard-worktree-remove-wip.sh — PreToolUse guard blocking removal on WIP
  - scripts/worktree-gc.sh              — GC stale worktrees (any path/name)
                                          on upstream-gone branches; rails:
                                          clean tree, gone branch, not the
                                          invoking worktree. Also report-only
                                          surfaces unregistered "husk" dirs
                                          under .claude/worktrees/ (ticket 0325).
  - scripts/worktree-exit-preflight.sh  — refuse worktree-exit while there are
                                          uncommitted files (incl. untracked).
                                          Closes the ExitWorktree gap that lost
                                          the 0173 draft (ticket 0174).
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


@pytest.mark.integration
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
    return [line[len("worktree "):] for line in out.splitlines() if line.startswith("worktree ")]


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


def test_gc_removes_non_agent_named_worktree_on_gone_branch(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "feature-x", dirty=False)
    make_branch_gone(remote, primary, "feature-x")

    res = _gc(primary)
    assert res.returncode == 0
    assert "removed feature-x" in res.stdout
    assert str(wt) not in _worktree_paths(primary)


def test_gc_silent_when_nothing_to_do(origin):
    _, primary = origin
    res = _gc(primary)
    assert res.returncode == 0
    assert res.stdout.strip() == ""


def _out_of_tree_worktree(remote, primary, tmp_path, *, dirty=False):
    """Register a worktree on branch raid-session-01 at an arbitrary path
    OUTSIDE .claude/worktrees/ (mirrors /tmp/erg-migrate-216/claude-harness),
    committed + pushed. Returns its path."""
    wt = tmp_path / "erg-migrate-test" / "claude-harness"
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(primary, "worktree", "add", "-b", "raid-session-01", str(wt))
    (wt / "work.txt").write_text("first\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-m", "work")
    git(wt, "push", "-u", "origin", "raid-session-01")
    if dirty:
        (wt / "work.txt").write_text("uncommitted change\n")
    return wt


def test_gc_removes_out_of_tree_worktree(origin, tmp_path):
    """The real 0195 bug: a clean, gone-branch worktree at an arbitrary path
    (not named agent-*, not under .claude/worktrees/) must be removed."""
    remote, primary = origin
    wt = _out_of_tree_worktree(remote, primary, tmp_path)
    make_branch_gone(remote, primary, "raid-session-01")

    res = _gc(primary)
    assert res.returncode == 0
    assert "removed claude-harness" in res.stdout
    assert str(wt) not in _worktree_paths(primary)


def test_gc_keeps_dirty_out_of_tree_worktree(origin, tmp_path):
    """The dirty rail must still protect an out-of-tree worktree with WIP."""
    remote, primary = origin
    wt = _out_of_tree_worktree(remote, primary, tmp_path, dirty=True)
    make_branch_gone(remote, primary, "raid-session-01")

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip claude-harness (uncommitted WIP)" in res.stdout
    assert str(wt) in _worktree_paths(primary)


@pytest.mark.integration
def test_gc_reports_unregistered_husk_dir(origin):
    """A husk dir under .claude/worktrees/ that is NOT a registered worktree
    (a deregistered session base cwd, only a scratch .claude/ left behind) must
    be reported — report-only, never removed, since it may be a live session's
    base cwd (ticket 0325)."""
    _, primary = origin
    husk = primary / ".claude" / "worktrees" / "husk-agent-dead"
    (husk / ".claude").mkdir(parents=True)

    res = _gc(primary)
    assert res.returncode == 0
    assert "husk-agent-dead" in res.stdout
    assert "husk" in res.stdout


@pytest.mark.integration
def test_gc_reports_husk_when_run_from_linked_worktree(origin):
    """The husk scan must root on the PRIMARY repo, not on the `repo` arg's own
    toplevel — else running gc from a linked worktree (the harness's normal cwd,
    and how lair invokes it bare) silently skips the scan (ticket 0325)."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-live", dirty=False)  # live linked worktree
    husk = primary / ".claude" / "worktrees" / "husk-agent-dead"
    (husk / ".claude").mkdir(parents=True)

    res = _gc(wt)  # invoked from the linked worktree, not the primary
    assert res.returncode == 0
    assert "husk-agent-dead" in res.stdout
    assert "husk" in res.stdout


@pytest.mark.integration
def test_gc_does_not_report_registered_worktree_under_claude_worktrees(origin):
    """A REGISTERED worktree living directly under .claude/worktrees/ (the real
    harness layout) must NOT be flagged as a husk — it is in the registered set,
    so the set-difference excludes it (ticket 0325)."""
    _, primary = origin
    wtdir = primary / ".claude" / "worktrees"
    wtdir.mkdir(parents=True)
    wt = wtdir / "agent-live"
    git(primary, "worktree", "add", "-b", "agent-live", str(wt))
    git(wt, "push", "-u", "origin", "agent-live")  # live branch, not gone → kept

    res = _gc(primary)
    assert res.returncode == 0
    assert "husk" not in res.stdout
    assert str(wt) in _worktree_paths(primary)


@pytest.mark.integration
def test_gc_does_not_report_container_of_nested_registered_worktree(origin):
    """A registered worktree at .claude/worktrees/g/leaf (multi-segment names are
    allowed by EnterWorktree's schema) must NOT make the container dir `g` be
    reported as a husk: `g` is at find's -maxdepth 1 but merely CONTAINS a
    registered worktree. An exact-path set-difference misses that, false-flagging
    a live worktree's container (ticket 0325, verify round 1 finding 1)."""
    _, primary = origin
    wtdir = primary / ".claude" / "worktrees"
    leaf = wtdir / "g" / "leaf"
    leaf.parent.mkdir(parents=True)
    git(primary, "worktree", "add", "-b", "g-leaf", str(leaf))
    git(leaf, "push", "-u", "origin", "g-leaf")  # live branch, not gone → kept

    res = _gc(primary)
    assert res.returncode == 0
    assert "husk" not in res.stdout
    assert str(leaf) in _worktree_paths(primary)


@pytest.mark.integration
def test_gc_husk_name_with_newline_cannot_forge_line(origin):
    """A husk dirname with an embedded newline must not forge an extra output
    line: raw interpolation of $(basename) / $dir would split the message and let
    the name inject a standalone line. Every non-empty stdout line must stay
    prefixed by the tool banner (ticket 0325, verify round 1 finding 2)."""
    _, primary = origin
    husk = primary / ".claude" / "worktrees" / "evil\nFAKE injected line"
    (husk / ".claude").mkdir(parents=True)

    res = _gc(primary)
    assert res.returncode == 0
    for line in res.stdout.splitlines():
        if line.strip():
            assert line.startswith("worktree-gc:"), f"forged line: {line!r}"


@pytest.mark.integration
def test_gc_warns_when_worktrees_dir_unreadable(origin):
    """When .claude/worktrees/ is unreadable, `find` inside the process
    substitution fails invisibly to set -e and the scan silently reports zero
    husks. The scan must fail open WITH a visible stderr signal (ticket 0325,
    verify round 1 finding 4)."""
    import os

    if os.geteuid() == 0:
        pytest.skip("permission gate is a no-op for root")
    _, primary = origin
    wtdir = primary / ".claude" / "worktrees"
    (wtdir / "husk-x" / ".claude").mkdir(parents=True)
    os.chmod(wtdir, 0o000)
    try:
        res = _gc(primary)
    finally:
        os.chmod(wtdir, 0o755)
    assert res.returncode == 0
    assert "unreadable" in res.stderr.lower()


# --------------------------------------------------------------------------- #
# worktree-exit-preflight.sh — ticket 0174
# --------------------------------------------------------------------------- #
#
# The PreToolUse Bash(git worktree remove*) matcher does not fire on the
# ExitWorktree harness tool, so a /roar sweep that Write's a ticket draft
# and then calls ExitWorktree silently drops the draft. The preflight script
# is the skill-level gate that closes that window: invoked by the roar
# and lair skills before they call ExitWorktree, it refuses when the
# worktree has any uncommitted state (tracked or untracked).

def _preflight(path):
    return subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh"), str(path)],
        capture_output=True, text=True,
    )


def test_preflight_blocks_on_untracked_ticket_draft(origin):
    """The exact failure mode that lost the 0173 draft: a /roar sweep
    Write's a new ticket file (untracked, never `git add`'d) and step 9 then
    calls ExitWorktree. The preflight must refuse before ExitWorktree runs."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-sweep", dirty=False)
    (wt / "tickets").mkdir()
    (wt / "tickets" / "0999-swept-class-bug.erg").write_text("%erg 0.1\n")

    res = _preflight(wt)
    assert res.returncode != 0
    assert "0999-swept-class-bug.erg" in res.stderr
    assert "ExitWorktree" in res.stderr  # message names the gate it's guarding


def test_preflight_blocks_on_tracked_modification(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-mod", dirty=True)  # tracked-modified

    res = _preflight(wt)
    assert res.returncode != 0
    assert "work.txt" in res.stderr


def test_preflight_blocks_on_staged_uncommitted(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-staged", dirty=False)
    (wt / "new.txt").write_text("staged\n")
    git(wt, "add", "new.txt")

    res = _preflight(wt)
    assert res.returncode != 0
    assert "new.txt" in res.stderr


def test_preflight_passes_on_clean_worktree(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-clean-exit", dirty=False)

    res = _preflight(wt)
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""


@pytest.mark.integration
def test_preflight_defaults_to_cwd(origin):
    """No arg → check the current directory. Mirrors how skill prose invokes
    it from inside the worktree it is about to exit."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-cwd", dirty=False)
    (wt / "tickets").mkdir()
    (wt / "tickets" / "0998-draft.erg").write_text("%erg 0.1\n")

    res = subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh")],
        cwd=str(wt), capture_output=True, text=True,
    )
    assert res.returncode != 0
    assert "0998-draft.erg" in res.stderr


@pytest.mark.integration
def test_preflight_errors_on_missing_path():
    res = subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh"), "/no/such/dir"],
        capture_output=True, text=True,
    )
    assert res.returncode != 0


def test_gc_skips_locked_gone_worktree(origin):
    """A locked worktree is an in-use marker (molt's active-session guard
    reads it that way) — the GC must skip it, never unlock-and-remove: the
    pre-0355 unlock path defeated the one marker a session could set."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-locked", dirty=False)
    git(primary, "worktree", "lock", str(wt))
    make_branch_gone(remote, primary, "agent-locked")

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-locked (locked" in res.stdout
    assert str(wt) in _worktree_paths(primary)


@pytest.mark.integration
def test_gc_skips_live_process_cwd_worktree(origin):
    """A clean worktree on a gone branch whose dir is a live process's cwd is
    an ACTIVE session's base, not an abandoned tree — the exact state the
    2026-07-13 incident removed (ticket 0355). Must be skipped, in place."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-session", dirty=False)
    make_branch_gone(remote, primary, "agent-session")

    proc = subprocess.Popen(["sleep", "60"], cwd=str(wt))
    try:
        res = _gc(primary)
        assert res.returncode == 0
        assert "skip agent-session (live process cwd inside" in res.stdout
        assert str(wt) in _worktree_paths(primary)
    finally:
        proc.kill()
        proc.wait()
