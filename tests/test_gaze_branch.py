"""Ticket 1273: gaze on `branch:<name>` with no forge records its result as an
`answer` entry in refs/notes/review, published to a local bare remote."""

import importlib.util
import subprocess
from pathlib import Path

import pytest
from gaze_fixture import CLOSE, SETUP, fields, git, make_repo, run

pytestmark = pytest.mark.integration

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("review_notes", SCRIPTS / "review_notes.py")
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)

def seat_panel(f):
    """A panel where one non-self seat reported: gaze_close accepts `seats: panel` (ticket 1287)."""
    panel = Path(f["panel"])
    panel.mkdir(parents=True, exist_ok=True)
    (panel / "manifest.txt").write_text("# budget: 10m\na\tm\topenai\theadless codex\n")
    (panel / "a.md").write_text("worker: model=m · family=openai\nverdict: clear\n")


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
    attr.write_text("")
    seat_panel(f)
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\nseats: panel\nreviewed_head_sha: {f['head']}\n"
                       "intent: default: the whole merge request\n{{plan_check}}\n{{seats}}\n{{duration}}\n")
    r = run(CLOSE, ["branch:feature", "--branch", "feature", "--token", f["clock"],
                    "--attribution-file", str(attr), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not tree.exists()
    assert "(local; background sync started)" in r.stdout  # ticket 1300: written locally, synced detached
    assert not (tmp_path / "gh.log").exists()  # nothing went to a forge
    answer = [e for e in rn.entries(primary, rid) if e["kind"] == "answer"][-1]
    assert answer["result"] == "REVIEWED" and answer["seats"] == "panel"
    assert answer["head"] == f["head"] and len(answer["attribution"]) == 1
    assert answer["attribution"][0].startswith(
        "reviewer: step=review · seat=a · runtime=codex · model=openai/m ·")  # ticket 1303: generated
    assert "plan check:" in answer["text"] and "{{" not in answer["text"]
    # where the gate reads it: coverage of the reviewed head, from a fresh clone of the remote
    cov = rn.coverage(primary, rid, f["head"])
    assert cov["match"] == "equal" and cov["result"] == "REVIEWED"
    origin = tmp_path / "origin.git"
    import time
    deadline = time.monotonic() + 20  # the detached sync delivers; nobody waits on it but this test
    while time.monotonic() < deadline and subprocess.run(
            ["git", "-C", str(origin), "rev-parse", "-q", "--verify", "refs/notes/review"],
            capture_output=True, text=True).stdout.strip() != git(primary, "rev-parse", "refs/notes/review"):
        time.sleep(0.2)
    assert git(origin, "rev-parse", "refs/notes/review") == git(primary, "rev-parse", "refs/notes/review")


def test_branch_review_reuses_the_hunt_request(tmp_path):
    primary, env = branch_repo(tmp_path)
    rid = rn.open_review(primary, "feature", "origin/main", why="hunt asked")
    r = run(SETUP, ["branch:feature"], primary, env)
    assert r.returncode == 0, r.stderr
    assert fields(r.stdout)["review_id"] == rid
    assert len([e for e in rn.entries(primary, rid) if e["kind"] == "request"]) == 1


def close_with(tmp_path, primary, env, f, intent_line):
    attr = tmp_path / "attr.txt"
    attr.write_text("")
    seat_panel(f)
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\nseats: panel\nreviewed_head_sha: {f['head']}\n{intent_line}"
                       "{{plan_check}}\n{{seats}}\n")
    return run(CLOSE, ["branch:feature", "--branch", "feature", "--token", f["clock"],
                       "--attribution-file", str(attr), "--comment-file", str(comment)], primary, env)


@pytest.mark.parametrize("intent_line,scope,match", [
    ("intent: default\n", "full", "equal"),
    ("intent: verify the fixes because they were the findings\n", "delta", "delta"),
    ("", "delta", "delta"),  # no intent line: never widened to full
    ("intent: default branch protections only\n", "delta", "delta"),  # a narrow intent starting "default"
    ("intent: default: the whole merge request\n", "full", "equal"),
    ("intent: verify x because y\nFindings:\nintent: default: quoted from an earlier result\n",
     "delta", "delta"),  # only the first intent line is the field
])
def test_answer_scope_follows_the_intent(tmp_path, intent_line, scope, match):
    primary, env = branch_repo(tmp_path)
    r = run(SETUP, ["branch:feature"], primary, env)
    assert r.returncode == 0, r.stderr
    f = fields(r.stdout)
    r = close_with(tmp_path, primary, env, f, intent_line)
    assert r.returncode == 0, r.stdout + r.stderr
    answer = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"][-1]
    assert answer["coverage"]["scope"] == scope
    assert rn.coverage(primary, f["review_id"], f["head"])["match"] == match


def test_malformed_trailer_claim_blocks_and_opens_nothing(tmp_path):
    primary, env = branch_repo(tmp_path)
    git(primary, "switch", "-q", "feature")
    git(primary, "commit", "-q", "--allow-empty", "-m", "x\n\nTicket: see-0042")
    git(primary, "switch", "-q", "main")
    r = run(SETUP, ["branch:feature"], primary, env)
    assert r.returncode == 1 and "claim" in r.stderr
    assert rn.find(primary, "feature") is None


def test_close_still_cleans_up(tmp_path):
    primary, env = branch_repo(tmp_path)
    r = run(SETUP, ["branch:feature"], primary, env)
    f = fields(r.stdout)
    attr = tmp_path / "attr.txt"
    attr.write_text("")
    r = run(CLOSE, ["branch:feature", "--branch", "feature", "--attribution-file", str(attr)], primary, env)
    assert "Traceback" not in r.stderr, r.stderr
    assert not (primary / ".claude" / "worktrees" / "review-branch-feature").exists()
    assert f["review_id"]


def test_a_delta_answer_carries_the_earlier_full_one(tmp_path):
    """Ticket 1274: verify-gate admits a delta answer only through `coverage.carried`."""
    primary, env = branch_repo(tmp_path)
    f = fields(run(SETUP, ["branch:feature"], primary, env).stdout)
    assert close_with(tmp_path, primary, env, f, "intent: default\n").returncode == 0
    full = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"][-1]
    f = fields(run(SETUP, ["branch:feature"], primary, env).stdout)
    r = close_with(tmp_path, primary, env, f, "intent: verify the fixes because they were the findings\n")
    assert r.returncode == 0, r.stdout + r.stderr
    delta = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"][-1]
    assert delta["coverage"] == {"scope": "delta", "carried": full["id"]}
    assert rn.gate_state(primary, f["review_id"], f["head"])["ready"]


def test_a_late_gaze_answer_stays_bound_to_the_request_it_reviewed(tmp_path):
    """Ticket 1281: gaze_setup freezes the request and run identity; a hunt request written while
    the gaze ran (round 2) does not capture the round-1 answer."""
    primary, env = branch_repo(tmp_path)
    f = fields(run(SETUP, ["branch:feature"], primary, env).stdout)
    r1 = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "request"][-1]
    assert f["request_id"] == r1["request_id"] and f["run_id"].startswith("gz-")
    git(primary, "switch", "-q", "feature")
    git(primary, "commit", "-q", "--allow-empty", "-m", "round 2")
    git(primary, "switch", "-q", "main")
    r2 = rn.request(primary, f["review_id"], "feature", "origin/main")
    r = close_with(tmp_path, primary, env, f, "intent: default\n")
    assert r.returncode == 0, r.stdout + r.stderr
    answer = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"][-1]
    assert answer["request_id"] == r1["request_id"] != r2["request_id"]
    assert answer["run_id"] == f["run_id"] and answer["head"] == r1["head"]


def test_a_second_clone_resumes_the_published_review(tmp_path):
    """Ticket 1281: a fresh clone after the documented bootstrap (setup, git fetch) resumes the
    review instead of opening a duplicate."""
    primary, env = branch_repo(tmp_path)
    rid = rn.open_review(primary, "feature", "origin/main", why="hunt asked")
    assert rn.publish(primary, [rn.entries(primary, rid)[0]["id"]]) == "retrievable"
    second = tmp_path / "second"
    git(tmp_path, "clone", "-q", str(tmp_path / "origin.git"), str(second))
    git(second, "config", "user.email", "t@example.com")
    git(second, "config", "user.name", "T")
    git(second, "branch", "feature", "origin/feature")
    rn.setup(second)
    git(second, "fetch", "-q", "origin")
    r = run(SETUP, ["branch:feature"], second, env)
    assert r.returncode == 0, r.stderr
    assert fields(r.stdout)["review_id"] == rid
    assert len([e for e in rn.entries(second, rid) if e["kind"] == "request"]) == 1


def test_setup_binds_the_request_on_the_reviewed_head_not_the_latest(tmp_path):
    """gaze 1817 finding 1: the request is chosen by the head gaze reviews; a later request on
    another head (written in the setup window, or before a rollback) never captures the run."""
    primary, env = branch_repo(tmp_path)
    rid = rn.open_review(primary, "feature", "origin/main", why="round 1")
    r1 = rn.entries(primary, rid)[0]
    git(primary, "switch", "-q", "feature")
    git(primary, "commit", "-q", "--allow-empty", "-m", "round 2")
    rn.request(primary, rid, "feature", "origin/main")
    git(primary, "reset", "-q", "--hard", r1["head"])  # the branch is back on round 1's head
    git(primary, "switch", "-q", "main")
    f = fields(run(SETUP, ["branch:feature"], primary, env).stdout)
    assert f["review_id"] == rid and f["request_id"] == r1["request_id"]


def test_setup_writes_a_request_when_none_names_the_reviewed_head(tmp_path):
    """The branch moved past the hunt request with no new one: gaze requests the head it reviews,
    so the answer binds to it and its review-head is retained."""
    primary, env = branch_repo(tmp_path)
    rid = rn.open_review(primary, "feature", "origin/main", why="round 1")
    git(primary, "switch", "-q", "feature")
    git(primary, "commit", "-q", "--allow-empty", "-m", "unrequested")
    head = git(primary, "rev-parse", "HEAD")
    git(primary, "switch", "-q", "main")
    f = fields(run(SETUP, ["branch:feature"], primary, env).stdout)
    reqs = [e for e in rn.entries(primary, rid) if e["kind"] == "request"]
    assert f["review_id"] == rid and len(reqs) == 2
    assert f["request_id"] == reqs[-1]["request_id"] and reqs[-1]["head"] == head
    assert git(primary, "rev-parse", f"refs/review-heads/{rid}/{f['request_id']}") == head
