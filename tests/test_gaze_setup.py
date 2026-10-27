"""Ticket 1227: one call prints the facts gaze needs and creates the review tree."""

import pytest
from gaze_fixture import SETUP, fields, git, make_repo, run

pytestmark = pytest.mark.integration


def test_setup_missing_ticket_file_blocks(tmp_path):
    primary, env = make_repo(tmp_path, body="x\n**Ticket:** tickets/0001-a.erg")
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 1 and "nonexistent ticket" in r.stderr


def test_setup_ready_block(tmp_path):
    primary, env = make_repo(tmp_path)
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    f = fields(r.stdout)
    tree = primary / ".claude" / "worktrees" / "review-7"
    assert f["review_tree"] == str(tree) and tree.is_dir()
    assert f["head"] == git(tree, "rev-parse", "HEAD")
    assert f["ticket"] == "none" and f["ci"] == "passing"
    assert (tree / ".panel" / "7" / "comments.md").read_text().count("looks odd") == 1
    assert "f.txt" in r.stdout


def test_setup_second_call_sees_live_gaze(tmp_path):
    primary, env = make_repo(tmp_path)
    assert run(SETUP, ["7"], primary, env).returncode == 0
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 3 and "live" in r.stderr


def test_setup_conflicting_pr_blocks_before_worktree(tmp_path):
    import json
    primary, env = make_repo(tmp_path)
    meta = json.loads(env["MOCK_PR_JSON"])
    meta["mergeable"] = "CONFLICTING"
    env["MOCK_PR_JSON"] = json.dumps(meta)
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 1
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()


def test_setup_reads_close_claims_not_prose_mentions(tmp_path):
    body = ("See tickets/0009-prose.erg for background.\nTicket-ref: tickets/0008-ref.erg\n"
            "```\n**Ticket:** tickets/0007-fenced.erg\n```\n**Ticket:** tickets/closed/0001-a.erg\n")
    primary, env = make_repo(tmp_path, body=body)
    r = run(SETUP, ["7"], primary, env)
    # only the live claim is read: it is the one reported missing
    assert r.returncode == 1 and "0001-a.erg" in r.stderr
    for other in ("0009", "0008", "0007"):
        assert other not in r.stderr


def test_setup_reads_short_form_claim(tmp_path):
    primary, env = make_repo(tmp_path, body="x\nTicket: 0042\n")
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 1 and "0042" in r.stderr


def test_setup_prose_mention_alone_is_no_claim(tmp_path):
    primary, env = make_repo(tmp_path, body="Mentions tickets/0009-prose.erg in passing.\n")
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    assert fields(r.stdout)["ticket"] == "none"
