"""Ticket 1487: a project's check target leaves git-ignored build products in
the review copy; gaze and the gate removed it only through the strict 1212
residue rule, so a clean review turned into ESCALATE. `--ignored-ok` lets a
throwaway review-*/gate-* tree drop ignored (`!!`) records, and nothing else."""

import subprocess
from pathlib import Path

import pytest
from gaze_fixture import CLOSE, SETUP, fields, git, make_repo, run
from run_checked import run_checked

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "worktree-exit-preflight.sh"


def tree(tmp_path, name):
    """A primary repo ignoring `*.stamp` and one linked worktree named `name`."""
    primary = tmp_path / "primary"
    if not primary.exists():
        primary.mkdir()
        git(primary, "init", "-b", "main")
        git(primary, "config", "user.email", "t@example.com")
        git(primary, "config", "user.name", "T")
        (primary / ".gitignore").write_text("*.stamp\n")
        git(primary, "add", ".gitignore")
        git(primary, "commit", "-m", "base")
    wt = tmp_path / "wt" / name
    run_checked(["git", "-C", str(primary), "worktree", "add", "--detach", str(wt)])
    return wt


def preflight(*args):
    return subprocess.run([str(PREFLIGHT), *map(str, args)], capture_output=True, text=True)


def test_ignored_build_file_passes_with_the_flag(tmp_path):
    wt = tree(tmp_path, "review-7")
    (wt / "out.stamp").write_text("built\n")
    r = preflight("--removal", "--ignored-ok", wt)
    assert r.returncode == 0, r.stderr


def test_untracked_unignored_file_still_blocks_with_the_flag(tmp_path):
    """Positive control: the flag must not hide real work."""
    wt = tree(tmp_path, "gate-7-s-r1")
    (wt / "out.stamp").write_text("built\n")
    (wt / "draft.txt").write_text("wip\n")
    r = preflight("--removal", "--ignored-ok", wt)
    assert r.returncode == 1
    assert "draft.txt" in r.stderr and "out.stamp" not in r.stderr


def test_ignored_file_blocks_without_the_flag(tmp_path):
    """Ticket 1212's rule stands for every other caller."""
    wt = tree(tmp_path, "review-7")
    (wt / "out.stamp").write_text("built\n")
    r = preflight("--removal", wt)
    assert r.returncode == 1 and "out.stamp" in r.stderr


def test_flag_refused_outside_a_review_or_gate_tree(tmp_path):
    wt = tree(tmp_path, "t1487-session")
    (wt / "out.stamp").write_text("built\n")
    r = preflight("--removal", "--ignored-ok", wt)
    assert r.returncode == 2 and "--ignored-ok" in r.stderr and "review-*" in r.stderr
    assert (wt / "out.stamp").exists()


def opened(tmp_path):
    primary, env = make_repo(tmp_path)
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    rt = primary / ".claude" / "worktrees" / "review-7"
    exclude = Path(git(primary, "rev-parse", "--absolute-git-dir")) / "info" / "exclude"
    with exclude.open("a") as stream:
        stream.write("\n*.stamp\n")
    (rt / "out.stamp").write_text("built\n")
    return primary, env, fields(r.stdout), rt


def close(tmp_path, primary, env):
    attr = tmp_path / "attr.txt"
    attr.write_text("")
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    return run(CLOSE, ["7", "--branch", "feature", "--attribution-file", str(attr),
                       "--comment-file", str(comment)], primary, env)


def test_gaze_close_removes_a_tree_holding_only_ignored_build_output(tmp_path):
    primary, env, _, rt = opened(tmp_path)
    r = close(tmp_path, primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ESCALATE" not in r.stdout + r.stderr
    assert not rt.exists()


def test_gaze_close_still_escalates_on_an_untracked_unignored_file(tmp_path):
    primary, env, _, rt = opened(tmp_path)
    (rt / "draft.txt").write_text("wip\n")
    r = close(tmp_path, primary, env)
    assert r.returncode == 1 and "ESCALATE" in r.stderr
    assert "draft.txt" in r.stderr
    assert rt.exists()


def test_verify_gate_removal_passes_the_flag_after_removal():
    text = (ROOT / "skills" / "verify-gate" / "SKILL.md").read_text()
    assert 'worktree-exit-preflight.sh --removal --ignored-ok "$gate_tree"' in text
