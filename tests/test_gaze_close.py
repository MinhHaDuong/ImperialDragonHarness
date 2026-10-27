"""Ticket 1227: one call cleans, reports containment and posts the comment."""

import pytest
from gaze_fixture import CLOSE, SETUP, fields, make_repo, run

pytestmark = pytest.mark.integration


def opened(tmp_path):
    primary, env = make_repo(tmp_path)
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    return primary, env, fields(r.stdout)


def test_clean_tree_is_removed_and_comment_posted(tmp_path):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{duration}}\n{{containment}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--token", f["clock"], "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()
    posted = (tmp_path / "gh.log").read_text()
    assert "result: REVIEWED" in posted and "duration:" in posted and "containment: toplevel" in posted
    assert "{{" not in posted


def test_dirty_tracked_file_preserves_tree_and_blocks(tmp_path):
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    (tree / "f.txt").write_text("real wip\n")
    comment = tmp_path / "c.md"
    comment.write_text("x\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--comment-file", str(comment)], primary, env)
    assert r.returncode == 1 and "blocked" in r.stderr
    assert (tree / "f.txt").read_text() == "real wip\n"
    assert not (tmp_path / "gh.log").exists()


def test_foreign_file_in_session_tree_is_flagged(tmp_path):
    primary, env, f = opened(tmp_path)
    (primary / "stray.erg").write_text("x\n")
    r = run(CLOSE, ["7", "--branch", "feature"], primary, env)
    assert r.returncode == 4 and "FLAGGED" in r.stdout and "stray.erg" in r.stdout
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()
