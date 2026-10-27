"""Ticket 1227: one call cleans, reports containment and posts the comment."""

import pytest
from gaze_fixture import CLOSE, SETUP, fields, git, make_repo, run

pytestmark = pytest.mark.integration


def ATTR(tmp_path, text=""):
    f = tmp_path / "attr.txt"
    f.write_text(text)
    return ["--attribution-file", str(f)]


def forge_shim(tmp_path, env):
    """gh shim holding a PR body in a file: `pr view --json body`, `api` GET and PATCH."""
    body = tmp_path / "body.txt"
    body.write_text("Body\n```attribution\npr: 7 · merged pending · project: .agents\n```\n")
    shim = tmp_path / "bin" / "gh"
    shim.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = pr ] && [ "$2" = view ]; then cat "$MOCK_BODY"; exit 0; fi\n'
        'if [ "$1" = api ]; then\n'
        '  case "$*" in *PATCH*) python3 -c "import json,sys;open(sys.argv[1],\'w\').write(json.load(sys.stdin)[\'body\'])" "$MOCK_BODY" ;;\n'
        '  *) cat "$MOCK_BODY" ;; esac; exit 0; fi\n'
        'if [ "$2" = comment ]; then printf \'%s\\n\' "$5" >> "$MOCK_GH_LOG"; fi\n')
    env["MOCK_BODY"] = str(body)
    return body


SEAT = ("reviewer: step=review · seat: a · runtime=claude · family=anthropic · route=r · "
        "model=m · status: ran")


def opened(tmp_path):
    primary, env = make_repo(tmp_path)
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    return primary, env, fields(r.stdout)


def test_clean_tree_is_removed_and_comment_posted(tmp_path):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{duration}}\n{{containment}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--token", f["clock"], *ATTR(tmp_path), "--comment-file", str(comment)],
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
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 1 and "blocked" in r.stderr
    assert (tree / "f.txt").read_text() == "real wip\n"
    assert not (tmp_path / "gh.log").exists()


def test_foreign_file_in_session_tree_is_flagged(tmp_path):
    primary, env, f = opened(tmp_path)
    (primary / "stray.erg").write_text("x\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], primary, env)
    assert r.returncode == 4 and "FLAGGED" in r.stdout and "stray.erg" in r.stdout
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()


def test_blocked_cleanup_still_appends_attribution(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    (primary / ".claude" / "worktrees" / "review-7" / "f.txt").write_text("real wip\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n")], primary, env)
    assert r.returncode == 1 and "blocked" in r.stderr
    assert "calling gaze posts the ESCALATE comment" in r.stderr
    assert "attribution: appended" in r.stdout
    assert "seat: a" in body.read_text()
    assert not (tmp_path / "gh.log").exists()


def test_clean_close_appends_attribution_before_the_comment(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n"), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "seat: a" in body.read_text()


def test_call_without_attribution_file_fails_loudly(tmp_path):
    primary, env, f = opened(tmp_path)
    r = run(CLOSE, ["7", "--branch", "feature"], primary, env)
    assert r.returncode == 2 and "--attribution-file" in r.stderr
    assert (primary / ".claude" / "worktrees" / "review-7").exists()


def test_attribution_creates_the_block_when_the_body_has_none(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    body.write_text("Body without a block\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n")], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    text = body.read_text()
    assert "```attribution" in text and "seat: a" in text and f"project: {primary.name}" in text


def test_blocked_cleanup_with_failed_append_exits_2(tmp_path):
    primary, env, f = opened(tmp_path)
    (primary / ".claude" / "worktrees" / "review-7" / "f.txt").write_text("real wip\n")
    # the default shim answers `pr view` with PR json, not a body: the append fails
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n")], primary, env)
    assert "attribution: FAILED" in r.stdout and "blocked" in r.stderr
    assert r.returncode == 2


def test_close_from_inside_the_review_worktree_is_refused(tmp_path):
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], tree, env)
    assert r.returncode == 2 and "inside the review worktree" in r.stderr
    assert tree.exists()


def test_preexisting_untracked_primary_file_is_not_contamination(tmp_path):
    primary, env = make_repo(tmp_path)
    (primary / "docs").mkdir()
    (primary / "docs" / "draft.md").write_text("author work\n")
    caller = tmp_path / "caller"
    git(primary, "worktree", "add", "-b", "callerbr", str(caller))
    r = run(SETUP, ["7"], caller, env)
    assert r.returncode == 0, r.stderr
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], caller, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "clean" in r.stdout
