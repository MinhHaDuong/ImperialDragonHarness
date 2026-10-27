"""Ticket 1273: gaze on `branch:<name>` with no forge records its result as an
`answer` entry in refs/notes/review, published to a local bare remote."""

import importlib.util
from pathlib import Path

import pytest
from gaze_fixture import CLOSE, SETUP, fields, git, make_repo, run

pytestmark = pytest.mark.integration

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("review_notes", SCRIPTS / "review_notes.py")
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)

SEAT = ("reviewer: step=review · seat: a · runtime=codex · family=openai · route=r · "
        "model=m · status: ran")


def branch_repo(tmp_path):
    primary, env = make_repo(tmp_path)
    git(primary, "config", "user.email", "t@example.com")
    git(primary, "config", "user.name", "T")
    git(primary, "branch", "feature", "origin/feature")
    env["IDH_REVIEW_BACKOFF"] = "0"
    return primary, env


def test_branch_review_records_an_answer_in_the_notes(tmp_path):
    primary, env = branch_repo(tmp_path)
    r = run(SETUP, ["branch:feature"], primary, env)
    assert r.returncode == 0, r.stderr
    f = fields(r.stdout)
    tree = primary / ".claude" / "worktrees" / "review-branch-feature"
    assert f["review_tree"] == str(tree) and tree.is_dir()
    assert f["head"] == git(tree, "rev-parse", "HEAD") == git(primary, "rev-parse", "feature")
    rid = f["review_id"]
    assert rid.startswith("rv-") and "f.txt" in r.stdout
    attr = tmp_path / "attr.txt"
    attr.write_text(SEAT + "\n")
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\nseats: panel\nreviewed_head_sha: {f['head']}\n"
                       "{{plan_check}}\n{{duration}}\n")
    r = run(CLOSE, ["branch:feature", "--branch", "feature", "--token", f["clock"],
                    "--attribution-file", str(attr), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not tree.exists()
    assert "(retrievable)" in r.stdout
    assert not (tmp_path / "gh.log").exists()  # nothing went to a forge
    answer = [e for e in rn.entries(primary, rid) if e["kind"] == "answer"][-1]
    assert answer["result"] == "REVIEWED" and answer["seats"] == "panel"
    assert answer["head"] == f["head"] and answer["attribution"] == [SEAT]
    assert "plan check:" in answer["text"] and "{{" not in answer["text"]
    # where the gate reads it: coverage of the reviewed head, from a fresh clone of the remote
    cov = rn.coverage(primary, rid, f["head"])
    assert cov["match"] == "equal" and cov["result"] == "REVIEWED"
    origin = tmp_path / "origin.git"
    assert git(origin, "rev-parse", "refs/notes/review") == git(primary, "rev-parse", "refs/notes/review")


def test_branch_review_reuses_the_hunt_request(tmp_path):
    primary, env = branch_repo(tmp_path)
    rid = rn.open_review(primary, "feature", "origin/main", why="hunt asked")
    r = run(SETUP, ["branch:feature"], primary, env)
    assert r.returncode == 0, r.stderr
    assert fields(r.stdout)["review_id"] == rid
    assert len([e for e in rn.entries(primary, rid) if e["kind"] == "request"]) == 1
