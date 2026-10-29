"""Ticket 1227: one call prints the facts gaze needs and creates the review tree."""

import importlib.util
import json
from pathlib import Path

import pytest
from gaze_fixture import SETUP, fields, git, make_repo, run

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_spec = importlib.util.spec_from_file_location("review_notes", SCRIPTS / "review_notes.py")
rn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rn)

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


def test_setup_reruns_after_closed_marker(tmp_path):
    """Ticket 1357: a fresh tree whose run already closed is dead, not live."""
    primary, env = make_repo(tmp_path)
    assert run(SETUP, ["7"], primary, env).returncode == 0
    tree = primary / ".claude" / "worktrees" / "review-7"
    (Path(git(tree, "rev-parse", "--absolute-git-dir")) / "gaze-closed").write_text("closed\n")
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    assert not (Path(git(tree, "rev-parse", "--absolute-git-dir")) / "gaze-closed").exists()


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


def test_setup_slug_form_is_no_claim_like_merge(tmp_path):
    """/merge: only a 4-digit ID alone qualifies; `NNNN-slug` closes nothing."""
    primary, env = make_repo(tmp_path, body="x\nTicket: 0042-some-slug\n")
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    assert fields(r.stdout)["ticket"] == "none"


def test_setup_malformed_ticket_path_stops_like_merge(tmp_path):
    """/merge: a malformed `Ticket: tickets/...` path is a stop, not a silent skip."""
    primary, env = make_repo(tmp_path, body="x\n**Ticket:** tickets/0042-a.md\n")
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 1 and "malformed" in r.stderr


# --- ticket 1300: a PR unit's review lives in refs/notes/review, keyed by the PR number ----------

def test_pr_setup_freezes_notes_identity(tmp_path):
    primary, env = make_repo(tmp_path)
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    f = fields(r.stdout)
    assert f["review_id"] and f["request_id"] and f["run_id"].startswith("gz-")
    assert rn.find_unit(primary, "pr:7") == f["review_id"]
    req = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "request"][-1]
    assert req["unit"] == "pr:7" and req["head"] == f["head"] and req["request_id"] == f["request_id"]
    state = json.loads((primary / ".claude" / "worktrees" / "review-7" / ".panel" / "7" / "entry-state.json").read_text())
    assert {k: state[k] for k in ("review_id", "request_id", "run_id")} == \
        {k: f[k] for k in ("review_id", "request_id", "run_id")}


def test_pr_setup_on_reused_branch_opens_new_review(tmp_path):
    primary, env = make_repo(tmp_path)
    old_pr = rn.open_review(str(primary), "feature", "origin/main", unit="pr:6", head="origin/feature")
    plain = rn.open_review(str(primary), "feature", "origin/main", head="origin/feature")
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    rid = fields(r.stdout)["review_id"]
    assert rid not in (old_pr, plain)
    assert len([e for e in rn.entries(primary, old_pr) if e["kind"] == "request"]) == 1


def test_pr_first_gaze_with_unreadable_origin_stops_and_opens_nothing(tmp_path):
    # a PR gaze reads its head from origin before any notes lookup; without origin it stops and opens
    # no review, so a unit never holds two reviews whose verdicts would split the round count. The
    # stale-but-local reader case is covered by test_resolve_stale_returns_local_review (raid 2026-10-28)
    primary, env = make_repo(tmp_path)
    git(primary, "remote", "set-url", "origin", str(tmp_path / "gone"))
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 2, r.stderr
    assert rn.find_unit(str(primary), "pr:7") is None
