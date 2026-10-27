"""Ticket 1274: verify-gate rules on refs/notes/review with no forge
(spec conception/2026-10-27-notes-review-spec.md §1, §5, §8). The gate reads the
gaze `answer` entries of a review and appends `verdict` entries whose round the
helper derives from the verdicts already recorded, every session and clone
alike. Temp repos and a local bare remote only; nothing reaches a forge."""

import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("review_notes", SCRIPTS / "review_notes.py")
assert spec and spec.loader
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)

pytestmark = pytest.mark.integration


def sh(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    assert done.returncode == 0, f"git {args}: {done.stderr}"
    return done.stdout.strip()


def ident(repo):
    sh(repo, "config", "user.email", "t@example.com")
    sh(repo, "config", "user.name", "T")


@pytest.fixture(autouse=True)
def no_backoff(monkeypatch):
    monkeypatch.setenv("IDH_REVIEW_BACKOFF", "0")


def commit(repo, name, text, msg):
    (Path(repo) / name).write_text(text)
    sh(repo, "add", name)
    sh(repo, "commit", "-qm", msg)
    return sh(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    """A repository with no remote: main, and feature one commit ahead."""
    r = tmp_path / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    ident(r)
    commit(r, "f.py", "def f():\n    return 1\n\n\n\n\n\ndef g():\n    return 2\n", "base")
    commit(r, "other.txt", "x\n", "other")
    sh(r, "switch", "-qc", "feature")
    commit(r, "f.py", "def f():\n    return 10\n\n\n\n\n\ndef g():\n    return 2\n", "feature edit")
    sh(r, "switch", "-q", "main")
    return r


def answer(repo, rid, result="REVIEWED", scope="full", head="feature"):
    return rn.add(repo, "answer", rid, {"run_id": f"gz-{rn._hex(4)}", "result": result, "seats": "panel",
                                        "coverage": {"scope": scope}, "text": f"result: {result}"},
                  head=sh(repo, "rev-parse", head))


def session():
    return str(uuid.uuid4())


def test_no_answer_refuses_the_gate(repo):
    rid = rn.open_review(repo, "feature", "main")
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and "no completed review" in state["reason"]
    assert state["round"] == 1


def test_full_answer_on_the_head_admits_the_gate(repo):
    rid = rn.open_review(repo, "feature", "main")
    a = answer(repo, rid)
    state = rn.gate_state(repo, rid, "feature")
    assert state["ready"] and state["match"] == "equal" and state["answer"] == a["id"]
    assert state["head"] == sh(repo, "rev-parse", "feature") == state["reviewed_head"]


def test_latest_answer_escalate_refuses_the_gate(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    answer(repo, rid, result="ESCALATE")
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and "ESCALATE" in state["reason"]


def test_moved_head_is_stale_and_names_the_reviewed_head(repo):
    rid = rn.open_review(repo, "feature", "main")
    reviewed = answer(repo, rid)["head"]
    sh(repo, "switch", "-q", "feature")
    commit(repo, "f.py", "def f():\n    return 11\n\n\n\n\n\ndef g():\n    return 2\n", "fix")
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and state["match"] == "none"
    assert "stale" in state["reason"] and state["reviewed_head"] == reviewed


def test_delta_answer_counts_only_after_a_full_one(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid, scope="delta")
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and "no full review" in state["reason"]
    answer(repo, rid, scope="full")
    sh(repo, "switch", "-q", "feature")
    commit(repo, "f.py", "def f():\n    return 12\n\n\n\n\n\ndef g():\n    return 2\n", "fix")
    rn.request(repo, rid, "feature", "main")
    answer(repo, rid, scope="delta")
    state = rn.gate_state(repo, rid, "feature")
    assert state["ready"] and state["match"] == "delta"


def test_rebased_head_is_admitted_only_on_an_equal_patch_id(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    sh(repo, "switch", "-q", "main")
    commit(repo, "other.txt", "y\n", "main moves elsewhere")
    sh(repo, "switch", "-q", "feature")
    sh(repo, "rebase", "-q", "main")
    state = rn.gate_state(repo, rid, "feature")
    assert state["ready"] and state["match"] == "patch-id"
    # a whitespace-only change is a behaviour change in Python: a different verbatim id
    commit(repo, "f.py", "def f():\n  return 10\n\n\n\n\n\ndef g():\n    return 2\n", "indent")
    sh(repo, "reset", "-q", "--soft", "HEAD~2")
    sh(repo, "commit", "-qm", "squashed, re-indented")
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and state["match"] == "none"


def test_round_is_derived_from_verdicts_of_every_session_and_capped(repo):
    rid = rn.open_review(repo, "feature", "main")
    a = answer(repo, rid)
    first = rn.record_verdict(repo, rid, session(), "REROLL", "feature", evidence=[a["id"]])
    assert first["entry"]["round"] == 1 and first["entry"]["kind"] == "verdict"
    assert first["entry"]["evidence"] == [a["id"]]
    assert first["entry"]["head"] == sh(repo, "rev-parse", "feature")
    assert rn.gate_state(repo, rid, "feature")["round"] == 2
    second = rn.record_verdict(repo, rid, session(), "APPROVED", "feature")  # a fresh session: no reset
    assert second["entry"]["round"] == 2
    with pytest.raises(rn.Refusal, match="two rounds"):
        rn.record_verdict(repo, rid, session(), "APPROVED", "feature")
    assert [e["round"] for e in rn.entries(repo, rid) if e["kind"] == "verdict"] == [1, 2]


def test_round_two_cannot_reroll(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    s = session()
    rn.record_verdict(repo, rid, s, "REROLL", "feature")
    with pytest.raises(rn.Refusal, match="ESCALATE"):
        rn.record_verdict(repo, rid, s, "REROLL", "feature")


def test_verdict_fields_are_checked(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    with pytest.raises(rn.Refusal, match="verdict"):
        rn.record_verdict(repo, rid, session(), "LGTM", "feature")
    with pytest.raises(rn.Refusal, match="session"):
        rn.record_verdict(repo, rid, "not-a-uuid", "APPROVED", "feature")
    with pytest.raises(rn.Refusal, match="verdict"):  # the round is the helper's, never the caller's
        rn.add(repo, "verdict", rid, {"gate_session_id": session(), "round": 1, "verdict": "APPROVED"})
    assert not [e for e in rn.entries(repo, rid) if e["kind"] == "verdict"]


def test_rounds_count_verdicts_published_by_another_clone(tmp_path):
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
    ident(seed)
    commit(seed, "a.txt", "1\n", "base")
    sh(seed, "remote", "add", "origin", str(origin))
    sh(seed, "push", "-q", "origin", "main")
    sh(seed, "switch", "-qc", "feature")
    commit(seed, "a.txt", "2\n", "edit")
    sh(seed, "push", "-q", "origin", "feature")
    clones = []
    for name in ("A", "B"):
        c = tmp_path / name
        subprocess.run(["git", "clone", "-q", str(origin), str(c)], check=True)
        ident(c)
        sh(c, "branch", "-q", "feature", "origin/feature")
        clones.append(c)
    a, b = clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    done = rn.record_verdict(a, rid, session(), "REROLL", "feature")
    assert done["level"] == "retrievable"
    state = rn.gate_state(b, rid, "feature")  # B never saw the review: the gate syncs first
    assert state["ready"] and state["round"] == 2
    assert rn.record_verdict(b, rid, session(), "APPROVED", "feature")["entry"]["round"] == 2
    assert sh(origin, "rev-parse", "refs/notes/review") == sh(b, "rev-parse", "refs/notes/review")


def cli(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(repo), *args],
                          capture_output=True, text=True)


def test_cli_gate_and_verdict(repo):
    rid = rn.open_review(repo, "feature", "main")
    r = cli(repo, "gate", rid, "feature")
    assert r.returncode == 1 and json.loads(r.stdout)["ready"] is False
    a = answer(repo, rid)
    r = cli(repo, "gate", rid, "feature")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["answer"] == a["id"]
    text = Path(repo).parent / "verdict.md"
    text.write_text("/verify-gate round=1 verdict=APPROVED\nRationale: ok\n")
    r = cli(repo, "verdict", "--review", rid, "--session", session(), "--verdict", "APPROVED",
            "--head", "feature", "--evidence", a["id"], "--candidate", "0" * 40, "--text-file", str(text))
    assert r.returncode == 0, r.stderr
    eid, level = r.stdout.split()[:2]
    v = [e for e in rn.entries(repo, rid) if e["kind"] == "verdict"][-1]
    assert v["id"] == eid and level == "done-unpublished" and v["gate_candidate"] == "0" * 40
    assert v["text"].startswith("/verify-gate round=1 verdict=APPROVED") and v["round"] == 1
    r = cli(repo, "add", "verdict", "--review", rid, "--json", "{}")
    assert r.returncode != 0


def test_an_escalate_answer_covering_the_head_refuses_even_if_not_latest(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid, result="ESCALATE")  # on the current head
    sh(repo, "branch", "-q", "old", "feature~0")
    sh(repo, "switch", "-q", "feature")
    commit(repo, "f.py", "def f():\n    return 13\n\n\n\n\n\ndef g():\n    return 2\n", "later")
    answer(repo, rid, result="REVIEWED")  # latest, but on another head
    sh(repo, "reset", "-q", "--hard", "old")
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and "ESCALATE" in state["reason"]
