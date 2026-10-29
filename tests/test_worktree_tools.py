"""Tests for the worktree tooling scripts (tickets 0168, 0169, 0174).

Exercises:
  - scripts/worktree-salvage.sh         — commit + push WIP before removal
  - scripts/worktree-gc.sh              — GC stale worktrees (any path/name)
                                          on upstream-gone branches; rails:
                                          clean tree, gone branch, not the
                                          invoking worktree. Also report-only
                                          surfaces unregistered "husk" dirs
                                          under .claude/worktrees/ (ticket 0325).
  - scripts/worktree-exit-preflight.sh  — refuse worktree-exit while there are
                                          uncommitted files (incl. untracked).
                                          Closes the gap that lost the 0173
                                          draft (ticket 0174).
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from child_env import child_env

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

# Every test in this suite spawns git subprocesses (the `origin` fixture runs
# `git init`/`push`; each test calls `run()`/`git()`), so the whole file is
# `integration` by pytest.ini's definition — it does not belong in check-fast.
pytestmark = [
    pytest.mark.skipif(
        shutil.which("git") is None or shutil.which("jq") is None,
        reason="git and jq required",
    ),
    pytest.mark.integration,
]


def run(args, cwd=None, check=True, env=None):
    return subprocess.run(
        args, cwd=cwd, check=check, capture_output=True, text=True,
        env=child_env() if env is None else env,
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
    """Merge into main, delete the topic ref, and prune so it reads [gone]."""
    git(primary, "merge", "--no-ff", "-m", f"merge {name}", name)
    git(primary, "push", "origin", "main")
    git(remote, "update-ref", "-d", f"refs/heads/{name}")
    git(primary, "fetch", "--prune", "origin")


def delete_branch_without_merge(remote, primary, name):
    """Produce `[gone]` without integration, the fail-closed control."""
    git(remote, "update-ref", "-d", f"refs/heads/{name}")
    git(primary, "fetch", "--prune", "origin")


def _ignore_worktree_tmp(primary):
    common = Path(git(primary, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as stream:
        stream.write("\n/.tmp/\n")


def _gc(primary, *, gh_response="[]", gh_exit=0, extra_env=None):
    fake_bin = primary.parent / "fake-bin"
    fake_bin.mkdir(exist_ok=True)
    gh = fake_bin / "gh"
    gh.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "sys.stdout.write(os.environ.get('TEST_GH_RESPONSE', '[]'))\n"
        "sys.exit(int(os.environ.get('TEST_GH_EXIT', '0')))\n"
    )
    gh.chmod(0o755)
    env = child_env()
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
    env["TEST_GH_RESPONSE"] = gh_response
    env["TEST_GH_EXIT"] = str(gh_exit)
    env.pop("WORKTREE_GC_OWNERLESS_IDLE_HOURS", None)
    env.update(extra_env or {})
    return run([str(SCRIPTS / "worktree-gc.sh"), str(primary)], env=env)


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
# worktree-gc.sh
# --------------------------------------------------------------------------- #

def test_hunt_tmp_exclude_registration_uses_shared_git_metadata(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-tmp-register", push=False)
    helper = SCRIPTS / "worktree-tmp-guard.py"

    first = run([sys.executable, str(helper), "register", str(wt)], check=False)
    second = run([sys.executable, str(helper), "register", str(wt)], check=False)
    assert first.returncode == 0 and second.returncode == 0
    common = Path(git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    rules = (common / "info" / "exclude").read_text().splitlines()
    assert rules.count("/.tmp/") == 1
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "ignored.txt").write_text("scratch\n")
    assert git(wt, "status", "--porcelain", "--untracked-files=all").stdout.strip() == ""

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


def test_gc_keeps_excluded_tmp_when_other_wip_exists(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tmp-and-wip")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")
    (wt / "unfinished.txt").write_text("deliverable\n")
    make_branch_gone(remote, primary, "agent-tmp-and-wip")

    res = _gc(primary)
    assert "skip agent-tmp-and-wip (uncommitted WIP)" in res.stdout
    assert (wt / ".tmp" / "cache.bin").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_tmp_cited_by_pr_body(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tmp-pr-citation")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "audit.json").write_text("evidence\n")
    make_branch_gone(remote, primary, "agent-tmp-pr-citation")

    body = [{"number": 42, "title": "work", "body": "Review evidence: `.tmp/audit.json`"}]
    res = _gc(primary, gh_response=__import__("json").dumps(body))
    assert "citation" in res.stdout.lower()
    assert (wt / ".tmp" / "audit.json").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_tmp_cited_by_candidate_verdict(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tmp-verdict-citation")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "audit.json").write_text("evidence\n")
    (wt / ".panel" / "42").mkdir(parents=True)
    (wt / ".panel" / "42" / "gate.md").write_text("Reviewed `.tmp/audit.json`.\n")
    make_branch_gone(remote, primary, "agent-tmp-verdict-citation")

    res = _gc(primary, gh_response="[]")
    assert "citation" in res.stdout.lower()
    assert (wt / ".tmp" / "audit.json").exists()
    assert (wt / ".panel" / "42" / "gate.md").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_blocks_unreadable_registered_verdict_parent(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tmp-cross-verdict")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")
    (primary / ".panel").symlink_to(primary / "missing-panel-target")
    make_branch_gone(remote, primary, "agent-tmp-cross-verdict")

    response = [{"number": 42, "title": "work", "body": "No scratch citation."}]
    res = _gc(primary, gh_response=__import__("json").dumps(response))
    assert "verdict directory is unavailable" in res.stderr.lower()
    assert (wt / ".tmp" / "cache.bin").exists()
    assert str(wt) in _worktree_paths(primary)


def test_removal_guard_rejects_branch_mismatch(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-branch-mismatch")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")

    res = run([
        sys.executable, str(SCRIPTS / "worktree-tmp-guard.py"), "removal",
        str(primary), str(wt), "--branch", "main",
    ], check=False)
    assert res.returncode == 2
    assert "does not match" in res.stderr
    assert (wt / ".tmp" / "cache.bin").exists()


def test_gc_keeps_tmp_cited_by_topic_commit(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tmp-commit-citation")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "audit.json").write_text("evidence\n")
    git(wt, "commit", "--allow-empty", "-m", "preserve .tmp/audit.json evidence")
    git(wt, "push", "origin", "agent-tmp-commit-citation")
    make_branch_gone(remote, primary, "agent-tmp-commit-citation")

    res = _gc(primary)
    assert "citation" in res.stdout.lower()
    assert (wt / ".tmp" / "audit.json").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_tmp_if_citation_source_is_unavailable(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tmp-source-unavailable")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")
    make_branch_gone(remote, primary, "agent-tmp-source-unavailable")

    res = _gc(primary, gh_exit=1)
    assert "could not inspect citation sources" in res.stderr.lower()
    assert (wt / ".tmp" / "cache.bin").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_gone_branch_without_integration_ancestry(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-gone-unmerged")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")
    delete_branch_without_merge(remote, primary, "agent-gone-unmerged")

    res = _gc(primary)
    assert "not proven integrated" in (res.stdout + res.stderr).lower()
    assert (wt / ".tmp" / "cache.bin").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_counts_and_reports_tmp_before_eligible_removal(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-gone-with-tmp")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "one.bin").write_bytes(b"12345")
    make_branch_gone(remote, primary, "agent-gone-with-tmp")

    res = _gc(primary)
    assert res.returncode == 0
    line = next(line for line in res.stdout.splitlines() if ".tmp/" in line)
    assert "1 files" in line and "bytes" in line
    assert res.stdout.index(line) < res.stdout.index("removed agent-gone-with-tmp")
    assert str(wt) not in _worktree_paths(primary)


def test_gc_treats_tracked_tmp_as_wip_even_when_clean(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tracked-tmp")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "tracked.txt").write_text("retained\n")
    git(wt, "add", "-f", ".tmp/tracked.txt")
    git(wt, "commit", "-m", "track temp output")
    git(wt, "push", "origin", "agent-tracked-tmp")
    make_branch_gone(remote, primary, "agent-tracked-tmp")

    res = _gc(primary)
    assert "tracked .tmp content" in res.stderr.lower() or "uncommitted wip" in res.stdout.lower()
    assert (wt / ".tmp" / "tracked.txt").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_tmp_as_wip_when_common_exclude_is_missing(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-unexcluded-tmp")
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")
    make_branch_gone(remote, primary, "agent-unexcluded-tmp")

    res = _gc(primary)
    assert "common info/exclude lacks" in res.stderr
    assert (wt / ".tmp" / "cache.bin").exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_collects_gone_worktree_with_review_scratch(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-panel")
    (wt / ".panel" / "999").mkdir(parents=True)
    (wt / ".panel" / "999" / "report.md").write_text("review\n")
    (wt / "build" / "panel-head").mkdir(parents=True)
    (wt / "build" / "panel-head" / "README").write_text("base\n")
    make_branch_gone(remote, primary, "agent-panel")

    res = _gc(primary)
    assert res.returncode == 0
    assert "removed agent-panel" in res.stdout
    assert str(wt) not in _worktree_paths(primary)


def test_gc_preserves_dropped_deliverable_after_purging_scratch(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-dropped")
    (wt / ".panel" / "999").mkdir(parents=True)
    (wt / ".panel" / "999" / "report.md").write_text("review\n")
    (wt / "tests").mkdir()
    (wt / "tests" / "test_dropped.sh").write_text("#!/bin/sh\nexit 0\n")
    make_branch_gone(remote, primary, "agent-dropped")

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-dropped (uncommitted WIP" in res.stdout
    assert "tests/test_dropped.sh" in res.stdout
    assert str(wt) in _worktree_paths(primary)
    assert not (wt / ".panel").exists()
    assert (wt / "tests" / "test_dropped.sh").exists()


def test_gc_does_not_purge_scratch_in_locked_worktree(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-locked-panel")
    (wt / ".panel" / "999").mkdir(parents=True)
    (wt / ".panel" / "999" / "report.md").write_text("review\n")
    git(primary, "worktree", "lock", str(wt))
    make_branch_gone(remote, primary, "agent-locked-panel")

    res = _gc(primary)
    assert "skip agent-locked-panel (locked" in res.stdout
    assert (wt / ".panel" / "999" / "report.md").exists()


def test_gc_does_not_follow_build_symlink_outside_worktree(origin, tmp_path):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-linked-build")
    outside = tmp_path / "outside"
    (outside / "panel-head").mkdir(parents=True)
    (outside / "panel-head" / "keep.txt").write_text("keep\n")
    (wt / "build").symlink_to(outside, target_is_directory=True)
    make_branch_gone(remote, primary, "agent-linked-build")

    _gc(primary)
    assert (outside / "panel-head" / "keep.txt").exists()


def test_gc_keeps_modified_tracked_panel_file(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-tracked-panel")
    (wt / ".panel" / "999").mkdir(parents=True)
    report = wt / ".panel" / "999" / "report.md"
    report.write_text("committed\n")
    git(wt, "add", ".panel")
    git(wt, "commit", "-m", "track panel file")
    report.write_text("unsaved\n")
    make_branch_gone(remote, primary, "agent-tracked-panel")

    res = _gc(primary)
    assert "skip agent-tracked-panel (uncommitted WIP)" in res.stdout
    assert report.read_text() == "unsaved\n"
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_live_branch_worktree(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-live", dirty=False)  # branch still on origin

    res = _gc(primary)
    assert res.returncode == 0
    assert str(wt) in _worktree_paths(primary)


def test_gc_still_reports_real_wip_on_live_branch(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-live-wip")
    (wt / "tests").mkdir()
    (wt / "tests" / "test_dropped.sh").write_text("#!/bin/sh\nexit 0\n")

    res = _gc(primary)
    assert "skip agent-live-wip (uncommitted WIP)" in res.stdout
    assert "tests/test_dropped.sh" in res.stdout
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
# A /roar sweep that Write's a ticket draft and then leaves its worktree
# drops the draft (0173, under the runtime's ExitWorktree). The preflight
# script is the skill-level gate: invoked by the roar and lair skills before
# they leave the worktree, it refuses when the worktree has any uncommitted
# state (tracked or untracked).

def _preflight(path):
    return subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh"), str(path)],
        capture_output=True, text=True, env=child_env(),
    )


def test_preflight_blocks_on_untracked_ticket_draft(origin):
    """The exact failure mode that lost the 0173 draft: a /roar sweep
    Write's a new ticket file (untracked, never `git add`'d) and step 9 then
    removes the worktree. The preflight must refuse before the removal."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-sweep", dirty=False)
    (wt / "tickets").mkdir()
    (wt / "tickets" / "0999-swept-class-bug.erg").write_text("%erg 0.1\n")

    res = _preflight(wt)
    assert res.returncode != 0
    assert "0999-swept-class-bug.erg" in res.stderr
    assert "removing the worktree" in res.stderr  # names what it guards


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


@pytest.mark.parametrize("scratch", ["draft.md", "notes/plan.md"])
def test_preflight_blocks_on_ignored_draft_under_star_ignore(origin, scratch):
    """Ticket 1212: under a `*` ignore rule plain status reads clean, yet
    `git worktree remove` deletes the ignored draft. The preflight refuses."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-ign-draft", dirty=False)
    _ignore_everything(primary)
    target = wt / scratch
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("in progress\n")

    res = _preflight(wt)
    assert res.returncode == 1
    assert scratch.split("/")[0] in res.stderr
    assert target.exists()


def test_preflight_passes_on_ignored_caches_only(origin):
    """Regenerable caches and the root .venv are not work: same list as gc."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-ign-cache", dirty=False)
    _ignore_everything(primary)
    (wt / "__pycache__").mkdir()
    (wt / "__pycache__" / "m.pyc").write_bytes(b"\0")
    (wt / ".venv" / "bin").mkdir(parents=True)
    (wt / ".venv" / "bin" / "python").write_text("")

    res = _preflight(wt)
    assert res.returncode == 0, res.stderr


@pytest.mark.parametrize("egg", ["pkg.egg-info", "src/pkg.egg-info"])
def test_preflight_passes_on_uv_run_build_output(origin, egg):
    """Ticket 1345: `uv run` in a packaged project leaves an egg-info beside
    the .venv and caches; setuptools rebuilds it, so it is not work. The
    ignore list is a package's own (DOIfetch's), not `*`: under `*` an
    untracked src/ collapses to one entry and rightly blocks."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-ign-egg", dirty=False)
    exclude = Path(git(primary, "rev-parse", "--absolute-git-dir").stdout.strip()) / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as stream:
        stream.write("\n.venv/\n*.egg-info/\n.pytest_cache/\n")
    (wt / egg).mkdir(parents=True)
    (wt / egg / "PKG-INFO").write_text("Name: pkg\n")
    (wt / ".pytest_cache").mkdir()
    (wt / ".pytest_cache" / "README.md").write_text("")
    (wt / ".venv" / "bin").mkdir(parents=True)
    (wt / ".venv" / "bin" / "python").write_text("")

    res = _preflight(wt)
    assert res.returncode == 0, res.stderr


def _exclude(primary, text):
    exclude = Path(git(primary, "rev-parse", "--absolute-git-dir").stdout.strip()) / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as stream:
        stream.write(f"\n{text}\n")


def _removal(path):
    return subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh"), "--removal", str(path)],
        capture_output=True, text=True, env=child_env(),
    )


def test_preflight_passes_on_ignored_setuptools_build(origin):
    """Ticket 1357: git prints the ignored directory as `!! build/`; only
    lib*, bdist.* and temp.* inside it are regenerable."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-build", dirty=False)
    _exclude(primary, "build/")
    for p in ("build/lib/pkg/m.py", "build/bdist.linux-x86_64/x", "build/temp.linux-x86_64/o"):
        (wt / p).parent.mkdir(parents=True, exist_ok=True)
        (wt / p).write_text("x\n")
    res = _preflight(wt)
    assert res.returncode == 0, res.stderr


def test_preflight_blocks_on_hand_made_file_under_ignored_build(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-build-notes", dirty=False)
    _exclude(primary, "build/")
    (wt / "build" / "lib").mkdir(parents=True)
    (wt / "build" / "lib" / "m.py").write_text("x\n")
    (wt / "build" / "notes.txt").write_text("keep me\n")
    res = _preflight(wt)
    assert res.returncode == 1 and "build/" in res.stderr


def test_removal_keeps_unignored_build_output(origin):
    """The scrub only deletes what the repository ignores: an unignored build/lib is work."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-build-unignored", dirty=False)
    (wt / "build" / "lib").mkdir(parents=True)
    (wt / "build" / "lib" / "draft.txt").write_text("mine\n")
    res = _removal(wt)
    assert res.returncode == 1
    assert (wt / "build" / "lib" / "draft.txt").exists()


def test_preflight_blocks_on_symlinked_build(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-build-link", dirty=False)
    _exclude(primary, "build")
    (primary.parent / "elsewhere" / "lib").mkdir(parents=True)
    (wt / "build").symlink_to(primary.parent / "elsewhere")
    assert _preflight(wt).returncode == 1


def _plain_venv(wt):
    (wt / ".venv" / "bin").mkdir(parents=True)
    (wt / ".venv" / "bin" / "python").write_text("")
    (wt / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin\n")


def test_gate_sequence_removes_tree_with_unignored_venv_without_force(origin):
    """Ticket 1357: a venv without its own .gitignore (not uv's) is untracked,
    so a plain `git worktree remove` refuses; the removal preflight scrubs it first."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-venv", dirty=False)
    _plain_venv(wt)
    assert git(primary, "worktree", "remove", str(wt), check=False).returncode != 0
    res = _removal(wt)
    assert res.returncode == 0, res.stderr
    assert git(primary, "worktree", "remove", str(wt), check=False).returncode == 0
    assert not wt.exists()


def test_preflight_keeps_venv_without_pyvenv_cfg_as_residue(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-venv-hand", dirty=False)
    (wt / ".venv").mkdir()
    (wt / ".venv" / "mine.txt").write_text("hand made\n")
    res = _removal(wt)
    assert res.returncode == 1 and ".venv" in res.stderr
    assert (wt / ".venv" / "mine.txt").exists()


def test_preflight_keeps_symlinked_venv_as_residue(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-venv-link", dirty=False)
    target = primary.parent / "shared-venv"
    target.mkdir()
    (target / "pyvenv.cfg").write_text("home = /usr/bin\n")
    (wt / ".venv").symlink_to(target)
    res = _removal(wt)
    assert res.returncode == 1
    assert (target / "pyvenv.cfg").exists()


def test_preflight_reports_ignored_tmp_without_purging_it(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-preflight-tmp", dirty=False)
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")

    res = _preflight(wt)
    assert res.returncode == 0
    assert ".tmp/" in res.stdout and "1 files" in res.stdout and "bytes" in res.stdout
    assert (wt / ".tmp" / "cache.bin").exists()


def test_preflight_tolerates_ignored_panel_beside_tmp_before_removal(origin):
    """With a .tmp/ present the non-removal run keeps .panel/ (cited review
    scratch, removed only at the removal gate). Ignored, it must not block."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-panel-tmp", dirty=False)
    _ignore_worktree_tmp(primary)
    exclude = Path(git(primary, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()) / "info" / "exclude"
    with exclude.open("a") as stream:
        stream.write("\n/.panel/\n")
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")
    (wt / ".panel" / "1").mkdir(parents=True)
    (wt / ".panel" / "1" / "review.md").write_text("report\n")

    res = _preflight(wt)
    assert res.returncode == 0, res.stderr
    assert (wt / ".panel" / "1" / "review.md").exists()


def test_preflight_preserves_cited_panel_until_removal_gate(origin):
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-preflight-cited-panel")
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "evidence.txt").write_text("evidence\n")
    verdict = wt / ".panel" / "manual" / "review.md"
    verdict.parent.mkdir(parents=True)
    verdict.write_text("This review cites `.tmp/evidence.txt`.\n")
    make_branch_gone(remote, primary, "agent-preflight-cited-panel")

    preflight = _preflight(wt)
    assert preflight.returncode != 0
    assert verdict.exists()

    fake_bin = primary.parent / "fake-gh-bin"
    fake_bin.mkdir()
    gh = fake_bin / "gh"
    gh.write_text("#!/bin/sh\nprintf '%s\\n' '[]'\n")
    gh.chmod(0o755)
    env = child_env()
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
    removal = subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh"), "--removal",
         "--branch", "agent-preflight-cited-panel", str(wt)],
        capture_output=True, text=True, env=env,
    )

    assert removal.returncode != 0
    assert "citation found" in removal.stdout.lower()
    assert verdict.exists()
    assert (wt / ".tmp" / "evidence.txt").exists()


def test_preflight_blocks_tracked_tmp_even_if_worktree_is_clean(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-preflight-tracked-tmp", dirty=False)
    _ignore_worktree_tmp(primary)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "retained.txt").write_text("tracked\n")
    git(wt, "add", "-f", ".tmp/retained.txt")
    git(wt, "commit", "-m", "track temporary path")

    res = _preflight(wt)
    assert res.returncode != 0
    assert "tracked .tmp content" in res.stderr.lower()
    assert (wt / ".tmp" / "retained.txt").exists()


def test_preflight_missing_common_exclude_keeps_tmp_as_wip(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-preflight-unexcluded-tmp", dirty=False)
    (wt / ".tmp").mkdir()
    (wt / ".tmp" / "cache.bin").write_bytes(b"scratch")

    res = _preflight(wt)
    assert res.returncode != 0
    assert "common info/exclude lacks the /.tmp/ rule" in res.stderr
    assert (wt / ".tmp" / "cache.bin").exists()


def test_preflight_purges_review_scratch_and_passes(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-panel-exit")
    (wt / ".panel" / "999").mkdir(parents=True)
    (wt / ".panel" / "999" / "report.md").write_text("review\n")
    (wt / "build" / "panel-head").mkdir(parents=True)
    (wt / "build" / "panel-head" / "README").write_text("base\n")

    res = _preflight(wt)
    assert res.returncode == 0
    assert not (wt / ".panel").exists()
    assert not (wt / "build" / "panel-head").exists()


def test_preflight_preserves_dropped_deliverable_with_scratch(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-dropped-exit")
    (wt / ".panel" / "999").mkdir(parents=True)
    (wt / ".panel" / "999" / "report.md").write_text("review\n")
    (wt / "tests").mkdir()
    (wt / "tests" / "test_dropped.sh").write_text("#!/bin/sh\nexit 0\n")

    res = _preflight(wt)
    assert res.returncode == 1
    assert "tests/test_dropped.sh" in res.stderr
    assert ".panel" not in res.stderr
    assert not (wt / ".panel").exists()
    assert (wt / "tests" / "test_dropped.sh").exists()


def test_preflight_does_not_follow_build_symlink_outside_worktree(origin, tmp_path):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-linked-build-exit")
    outside = tmp_path / "outside"
    (outside / "panel-head").mkdir(parents=True)
    (outside / "panel-head" / "keep.txt").write_text("keep\n")
    (wt / "build").symlink_to(outside, target_is_directory=True)

    _preflight(wt)
    assert (outside / "panel-head" / "keep.txt").exists()


def test_preflight_keeps_modified_tracked_panel_file(origin):
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-tracked-panel-exit")
    (wt / ".panel" / "999").mkdir(parents=True)
    report = wt / ".panel" / "999" / "report.md"
    report.write_text("committed\n")
    git(wt, "add", ".panel")
    git(wt, "commit", "-m", "track panel file")
    report.write_text("unsaved\n")

    res = _preflight(wt)
    assert res.returncode == 1
    assert report.read_text() == "unsaved\n"


def test_preflight_never_purges_non_git_directory(tmp_path):
    folder = tmp_path / "not-a-worktree"
    (folder / ".panel" / "999").mkdir(parents=True)
    report = folder / ".panel" / "999" / "report.md"
    report.write_text("keep\n")
    (folder / "build" / "panel-head").mkdir(parents=True)
    base = folder / "build" / "panel-head" / "README"
    base.write_text("keep\n")

    res = _preflight(folder)
    assert res.returncode != 0
    assert report.read_text() == "keep\n"
    assert base.read_text() == "keep\n"


def test_preflight_defaults_to_cwd(origin):
    """No arg → check the current directory. Mirrors how skill prose invokes
    it from inside the worktree it is about to exit."""
    _, primary = origin
    wt = make_agent_worktree(primary, "agent-cwd", dirty=False)
    (wt / "tickets").mkdir()
    (wt / "tickets" / "0998-draft.erg").write_text("%erg 0.1\n")

    res = subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh")],
        cwd=str(wt), capture_output=True, text=True, env=child_env(),
    )
    assert res.returncode != 0
    assert "0998-draft.erg" in res.stderr


def test_preflight_errors_on_missing_path():
    res = subprocess.run(
        [str(SCRIPTS / "worktree-exit-preflight.sh"), "/no/such/dir"],
        capture_output=True, text=True, env=child_env(),
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


def test_gc_unlocks_and_removes_dead_pid_locked_worktree(origin):
    """A harness lock records the owning session's pid in its reason; a lock
    whose pid is dead is a stale in-use marker, not an active session — the
    GC unlocks it and lets the rails decide (2026-09-28: a dead-pid lock had
    frozen a worktree holding the last on-disk copy of purged T2 memory)."""
    remote, primary = origin
    dead = subprocess.Popen(["true"], env=child_env())
    dead.wait()  # pid exists no more (no live process holds it)
    wt = make_agent_worktree(primary, "agent-dead-lock", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason",
        f"claude session agent-dead-lock (pid {dead.pid} start 1)")
    make_branch_gone(remote, primary, "agent-dead-lock")

    res = _gc(primary)
    assert res.returncode == 0
    assert f"unlocked agent-dead-lock (lock pid {dead.pid} dead" in res.stdout
    assert "removed agent-dead-lock" in res.stdout
    assert str(wt) not in _worktree_paths(primary)


def test_gc_keeps_pid_1_locked_worktree(origin):
    """A lock recording pid 1 names no owner: inside a pid namespace (a
    sandboxed runtime) `$PPID` reads 1, and that session may still be live
    while the live-cwd rail cannot see it. While its tree was active within
    the idle threshold, the GC keeps it, even with the branch gone and the
    tree clean."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-pid1-lock", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason",
        "hunt t2204 (pid 1; observed tool-parent runtime)")
    make_branch_gone(remote, primary, "agent-pid1-lock")

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-pid1-lock (locked, no visible owner, idle 0h < 72h" in res.stdout
    assert "removed agent-pid1-lock" not in res.stdout
    assert str(wt) in _worktree_paths(primary)
    porcelain = git(primary, "worktree", "list", "--porcelain").stdout
    assert f"worktree {wt}\n" in porcelain
    assert "locked hunt t2204 (pid 1;" in porcelain


@pytest.mark.parametrize("reason", [
    "claude a (pid 4242) then claude b (pid 99999)",
    "claude a (pid 4242) then claude b (pid)",
    "claude a (pid 4242) then claude b (pid\t3)",
    "claude a (pid\t3) then claude b (pid 4242)",
    "claude agent (pid 4194305)",
    "claude agent (pid 9999999)",
    "claude agent (pid 12345678)",
    "claude agent (pid 99999999999999999999)",
])
def test_gc_keeps_lock_with_ambiguous_or_out_of_range_pid(origin, reason):
    """Two `(pid` groups or a pid past the pid_max ceiling (4194304) name no
    owner the GC can check: read as no recorded pid and kept, never unlocked
    as dead."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-odd-pid", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", reason)
    make_branch_gone(remote, primary, "agent-odd-pid")

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-odd-pid (locked — treated as in use)" in res.stdout
    assert "integer expected" not in res.stderr
    assert str(wt) in _worktree_paths(primary)
    porcelain = git(primary, "worktree", "list", "--porcelain").stdout
    # git C-quotes a reason holding a control character, so match the record.
    assert "\nlocked " in porcelain


def test_gc_skips_removal_when_live_cwd_scan_reads_nothing(origin):
    """The live-cwd rail fails closed: a scan that returns no cwd at all
    (here python3 exits 1) cannot rule out an active session, so the GC
    keeps the tree instead of reading the silence as "nothing live"."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-blind", dirty=False)
    make_branch_gone(remote, primary, "agent-blind")
    fake_bin = primary.parent / "fake-bin"
    fake_bin.mkdir(exist_ok=True)
    py = fake_bin / "python3"
    py.write_text("#!/bin/sh\nexit 1\n")
    py.chmod(0o755)

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-blind (live-cwd scan read nothing" in res.stderr
    assert str(wt) in _worktree_paths(primary)


def _age_worktree_metadata(wt, hours):
    """Backdate the git metadata `worktree-gc` reads for idleness."""
    gitdir = Path(git(wt, "rev-parse", "--absolute-git-dir").stdout.strip())
    then = time.time() - hours * 3600
    for name in ("HEAD", "index", "logs/HEAD", "locked"):
        f = gitdir / name
        if f.exists():
            os.utime(f, (then, then))


@pytest.mark.parametrize("reason", [
    "hunt t2204 (pid 1; observed tool-parent runtime)",
    "hunt t2204 (owner pid not visible)",
])
def test_gc_reclaims_idle_ownerless_harness_lock(origin, reason):
    """A harness lock naming no owner is reclaimed once its tree has sat idle
    past the threshold (72 h by default): the remaining rails decide, so a
    sandboxed session that died without /roar leaves nothing to clean by hand."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-ownerless-idle", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", reason)
    make_branch_gone(remote, primary, "agent-ownerless-idle")
    _age_worktree_metadata(wt, 100)

    res = _gc(primary)
    assert res.returncode == 0
    assert "unlocked agent-ownerless-idle (lock no visible owner, idle 100h" in res.stdout
    assert "removed agent-ownerless-idle" in res.stdout
    assert str(wt) not in _worktree_paths(primary)


@pytest.mark.parametrize("reason", [
    "keep: author review",
    "hunt t1 (pid 1) and (pid 1)",
    "hunt t1 (owner pid not visible) (pid)",
    "claude agent (pid 0)",
    "claude agent (pid 4194305)",
    "manual hold (pid 01)",
    "manual hold (pid 1)",
    "note: hunt t1 (owner pid not visible)",
    "hunt t1 note quoting (pid 1)",
])
def test_gc_keeps_idle_lock_that_is_not_a_harness_ownerless_shape(origin, reason):
    """Only the harness shapes are reclaimed by age: `(hunt|claude) … (pid 1`
    digit-exact, or the whole reason `hunt t<id> (owner pid not visible)`. A
    hand-made lookalike, an ambiguous, out-of-range or pid-0 lock stays an
    opaque in-use marker, however long the tree has been idle."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-opaque-lock", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", reason)
    make_branch_gone(remote, primary, "agent-opaque-lock")
    _age_worktree_metadata(wt, 1000)

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-opaque-lock (locked" in res.stdout
    assert "removed agent-opaque-lock" not in res.stdout
    assert str(wt) in _worktree_paths(primary)


@pytest.mark.parametrize("scratch", ["work.txt", ".panel/1/review.md"])
def test_gc_keeps_lock_of_idle_ownerless_tree_with_uncommitted_files(origin, scratch):
    """Quiet git metadata is not proof a sandboxed session ended: one editing
    files without git looks idle. A tree holding any uncommitted file, review
    scratch included, keeps both its files and its lock, so the idle check
    runs again on the next pass."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-ownerless-wip", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", "hunt t7 (owner pid not visible)")
    make_branch_gone(remote, primary, "agent-ownerless-wip")
    target = wt / scratch
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("in progress\n")
    _age_worktree_metadata(wt, 100)

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-ownerless-wip (locked, no visible owner, idle 100h, tree not clean" in res.stdout
    assert target.exists()
    porcelain = git(primary, "worktree", "list", "--porcelain").stdout
    assert "locked hunt t7 (owner pid not visible)" in porcelain


def _ignore_everything(primary):
    """Mimic a repo whose .gitignore is `*`: every untracked file is ignored."""
    exclude = Path(git(primary, "rev-parse", "--git-common-dir").stdout.strip())
    if not exclude.is_absolute():
        exclude = primary / exclude
    exclude = exclude / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as stream:
        stream.write("\n*\n")


@pytest.mark.parametrize("scratch", ["draft.md", ".panel/1/review.md"])
def test_gc_keeps_idle_ownerless_tree_holding_ignored_files(origin, scratch):
    """`git worktree remove` deletes ignored files, and a repo may ignore `*`:
    an ignored draft or review scratch keeps an owner-less tree and its lock."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-ownerless-ign", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", "hunt t9 (owner pid not visible)")
    make_branch_gone(remote, primary, "agent-ownerless-ign")
    _ignore_everything(primary)
    target = wt / scratch
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("in progress\n")
    _age_worktree_metadata(wt, 100)

    res = _gc(primary)
    assert res.returncode == 0
    assert "skip agent-ownerless-ign (locked, no visible owner, idle 100h, tree not clean" in res.stdout
    assert target.exists()
    assert str(wt) in _worktree_paths(primary)


def test_gc_reclaims_idle_ownerless_tree_holding_only_caches(origin):
    """Regenerable caches are not work: an owner-less tree holding only an
    ignored __pycache__ and a root .venv (rebuilt from the lock) is still
    reclaimed once idle."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-ownerless-cache", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", "hunt t10 (owner pid not visible)")
    make_branch_gone(remote, primary, "agent-ownerless-cache")
    _ignore_everything(primary)
    (wt / "__pycache__").mkdir()
    (wt / "__pycache__" / "m.cpython-311.pyc").write_bytes(b"\0")
    (wt / ".venv" / "bin").mkdir(parents=True)
    (wt / ".venv" / "bin" / "python").write_text("")
    _age_worktree_metadata(wt, 100)

    res = _gc(primary)
    assert res.returncode == 0
    assert "removed agent-ownerless-cache" in res.stdout
    assert str(wt) not in _worktree_paths(primary)


def test_gc_status_read_does_not_restart_idle_clock(origin):
    """The GC's own status read of a live-branch tree must not rewrite its
    index: that would reset the idle clock of an owner-less tree each pass."""
    _remote, primary = origin
    wt = make_agent_worktree(primary, "agent-ownerless-clock", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", "hunt t11 (owner pid not visible)")
    _age_worktree_metadata(wt, 100)
    index = Path(git(wt, "rev-parse", "--absolute-git-dir").stdout.strip()) / "index"
    before = index.stat().st_mtime

    res = _gc(primary)
    assert res.returncode == 0
    assert index.stat().st_mtime == before


def test_gc_restores_ownerless_lock_when_removal_fails(origin):
    """An owner-less lock is lifted only with the tree: if `worktree remove`
    fails, the lock is back and the next pass decides again."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-ownerless-stuck", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", "hunt t12 (owner pid not visible)")
    make_branch_gone(remote, primary, "agent-ownerless-stuck")
    _age_worktree_metadata(wt, 100)
    # A git that refuses `worktree remove` up front, as it does for a tree
    # holding an initialised submodule, and runs everything else.
    real_git = shutil.which("git")
    wrap = primary.parent / "refusing-git"
    wrap.mkdir()
    (wrap / "git").write_text(
        "#!/usr/bin/env bash\n"
        'for a in "$@"; do [ "$a" = remove ] && { echo refused >&2; exit 128; }; done\n'
        f'exec {real_git} "$@"\n'
    )
    (wrap / "git").chmod(0o755)
    fake_bin = primary.parent / "fake-bin"  # _gc's fake gh stays first after the wrapper
    res = _gc(primary, extra_env={"PATH": f"{wrap}:{fake_bin}:{os.environ.get('PATH', '')}"})
    assert res.returncode == 0
    assert "could not remove agent-ownerless-stuck" in res.stderr
    assert str(wt) in _worktree_paths(primary)
    porcelain = git(primary, "worktree", "list", "--porcelain").stdout
    assert "locked hunt t12 (owner pid not visible)" in porcelain


def test_gc_oversized_idle_threshold_falls_back_to_default(origin):
    """A threshold too long to compare must not switch the idle check off:
    it falls back to 72 h, so a tree idle 10 h keeps its owner-less lock."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-ownerless-env", dirty=False)
    git(primary, "worktree", "lock", str(wt), "--reason", "hunt t8 (owner pid not visible)")
    make_branch_gone(remote, primary, "agent-ownerless-env")
    _age_worktree_metadata(wt, 10)

    res = _gc(primary, extra_env={"WORKTREE_GC_OWNERLESS_IDLE_HOURS": "99999999999999999999"})
    assert res.returncode == 0
    assert "idle 10h < 72h" in res.stdout
    assert "integer expression expected" not in res.stderr
    assert str(wt) in _worktree_paths(primary)


def test_gc_keeps_live_pid_locked_worktree(origin):
    """The pid half of the lock rail: a harness lock whose recorded pid is
    live is an active session — skipped in place, never unlocked."""
    remote, primary = origin
    live = subprocess.Popen(["sleep", "30"], env=child_env())
    try:
        wt = make_agent_worktree(primary, "agent-live-lock", dirty=False)
        git(primary, "worktree", "lock", str(wt), "--reason",
            f"claude session agent-live-lock (pid {live.pid} start 1)")
        make_branch_gone(remote, primary, "agent-live-lock")

        res = _gc(primary)
        assert res.returncode == 0
        assert f"skip agent-live-lock (locked, pid {live.pid} live" in res.stdout
        assert str(wt) in _worktree_paths(primary)
    finally:
        live.kill()
        live.wait()


def test_gc_skips_live_process_cwd_worktree(origin):
    """A clean worktree on a gone branch whose dir is a live process's cwd is
    an ACTIVE session's base, not an abandoned tree — the exact state the
    2026-07-13 incident removed (ticket 0355). Must be skipped, in place."""
    remote, primary = origin
    wt = make_agent_worktree(primary, "agent-session", dirty=False)
    (wt / ".panel" / "999").mkdir(parents=True)
    report = wt / ".panel" / "999" / "report.md"
    report.write_text("live review\n")
    make_branch_gone(remote, primary, "agent-session")

    proc = subprocess.Popen(["sleep", "60"], cwd=str(wt), env=child_env())
    try:
        res = _gc(primary)
        assert res.returncode == 0
        assert "skip agent-session (live process cwd inside" in res.stdout
        assert str(wt) in _worktree_paths(primary)
        assert report.read_text() == "live review\n"
    finally:
        proc.kill()
        proc.wait()


# --- hunt § Worktree recipe: no shared-$PPID collision (ticket 1328) --------

HUNT_SKILL = REPO_ROOT / "skills" / "hunt" / "SKILL.md"


def _hunt_worktree_recipe():
    """The bash block under hunt § Worktree's "Otherwise create one", verbatim."""
    text = HUNT_SKILL.read_text()
    tail = text.split("**Otherwise create one**", 1)[1]
    return tail.split("```bash\n", 1)[1].split("```", 1)[0]


def _run_hunt_recipe(primary, ticket, branch, prelude=""):
    script = _hunt_worktree_recipe().replace(
        "t$ID-short-description", branch)
    # Each call is its own bash child of this pytest process: the two share
    # one $PPID, as a spawner and its subagent share the runtime process.
    out = run(["bash", "-c", f"ID={ticket}\n{prelude}{script}"], cwd=primary,
              check=False)
    assert out.returncode == 0, f"recipe failed for {branch}: {out.stderr}"
    return Path(out.stdout.strip().splitlines()[-1])


def test_hunt_recipe_two_callers_sharing_ppid_get_distinct_paths(origin):
    _, primary = origin
    git(primary, "fetch", "origin")
    ppid = os.getpid()
    # The spawner's session tree, named the old way from the shared $PPID.
    spawner = primary / ".claude" / "worktrees" / f"t7-{ppid}"
    git(primary, "worktree", "add", str(spawner), "-b", "spawner", "main")

    first = _run_hunt_recipe(primary, 7, "t7-first")
    second = _run_hunt_recipe(primary, 7, "t7-second")

    assert len({spawner, first, second}) == 3
    porcelain = git(primary, "worktree", "list", "--porcelain").stdout
    for wt in (first, second):
        assert wt.is_dir()
        assert f"worktree {wt}\n" in porcelain
    # The lock keeps the bare pid that worktree-gc parses.
    assert porcelain.count(f"locked hunt t7 (pid {ppid})\n") == 2


def test_hunt_recipe_redraws_when_path_exists(origin):
    _, primary = origin
    git(primary, "fetch", "origin")
    seed = "RANDOM=1328\n"
    taken = _run_hunt_recipe(primary, 8, "t8-first", prelude=seed)
    # Same seed, same first draw: the recipe must not land on the held tree.
    again = _run_hunt_recipe(primary, 8, "t8-second", prelude=seed)
    assert again != taken
    assert git(again, "branch", "--show-current").stdout.strip() == "t8-second"
    assert git(taken, "branch", "--show-current").stdout.strip() == "t8-first"
