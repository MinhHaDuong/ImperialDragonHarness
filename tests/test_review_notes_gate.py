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
    # In-process verdicts start no detached sync here (ticket 1300): each test syncs when it
    # means to; the CLI tests run the real background sync.
    monkeypatch.setattr(rn, "sync_background", lambda cwd, remote="origin": False)


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


def answer(repo, rid, result="REVIEWED", head="feature", **legacy):
    """An answer as gaze_close writes it; `legacy` adds fields of old entries (e.g. coverage)."""
    oid = sh(repo, "rev-parse", head)
    on_head = [e for e in rn.entries(repo, rid) if e["kind"] == "request" and e["head"] == oid]
    rq = on_head[-1] if on_head else rn.request(repo, rid, "feature", "main", head=oid)  # as gaze_setup does (1281)
    return rn.add(repo, "answer", rid, {"run_id": f"gz-{rn._hex(4)}", "result": result, "seats": "panel",
                                        "text": f"result: {result}", **legacy},
                  head=oid, request_id=rq["request_id"])


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


def fix(repo, n):
    sh(repo, "switch", "-q", "feature")
    commit(repo, "f.py", f"def f():\n    return {n}\n\n\n\n\n\ndef g():\n    return 2\n", f"fix {n}")
    sh(repo, "switch", "-q", "main")


def test_bookkeeping_after_the_reviewed_head_is_admitted(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    sh(repo, "switch", "-q", "feature")
    (Path(repo) / "tickets").mkdir()
    commit(repo, "tickets/0001-x.erg", "%erg 0.1\n", "ticket(1): close")
    state = rn.gate_state(repo, rid, "feature")
    assert state["ready"] and state["match"] == "bookkeeping"


def test_a_branch_review_on_the_landing_head_is_the_prs_review(repo):
    """Ticket 1379: gaze answered `branch:feature`; the PR opened on that head carries the answer."""
    branch_rid = rn.open_review(repo, "feature", "main")
    answer(repo, branch_rid)
    pr_rid = rn.open_review(repo, "feature", "main", unit="pr:7")
    assert pr_rid == branch_rid and rn.find_unit(repo, "pr:7") == branch_rid
    state = rn.gate_state(repo, pr_rid, "feature")
    assert state["ready"] and state["match"] == "equal"


def test_a_branch_review_carries_over_a_bookkeeping_delta(repo):
    branch_rid = rn.open_review(repo, "feature", "main")
    answer(repo, branch_rid)
    sh(repo, "switch", "-q", "feature")
    (Path(repo) / "tickets").mkdir()
    commit(repo, "tickets/0001-x.erg", "%erg 0.1\n", "ticket(1): close")
    sh(repo, "switch", "-q", "main")
    pr_rid = rn.open_review(repo, "feature", "main", unit="pr:7")
    assert pr_rid == branch_rid
    assert rn.gate_state(repo, pr_rid, "feature")["ready"]


def test_a_reused_branch_name_never_finds_the_adopted_review(repo):
    branch_rid = rn.open_review(repo, "feature", "main")
    answer(repo, branch_rid)
    assert rn.open_review(repo, "feature", "main", unit="pr:7") == branch_rid
    assert rn.find(repo, "feature") is None


def test_a_branch_review_on_an_older_head_is_discarded_for_the_pr(repo):
    branch_rid = rn.open_review(repo, "feature", "main")
    answer(repo, branch_rid)
    fix(repo, 14)
    pr_rid = rn.open_review(repo, "feature", "main", unit="pr:7")
    assert pr_rid != branch_rid
    state = rn.gate_state(repo, pr_rid, "feature")
    assert not state["ready"] and "no completed review" in state["reason"]
    assert rn.find(repo, "feature") == branch_rid  # the branch review is left as it was


def test_round_two_rules_the_fix_of_a_round_one_reroll(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    rn.record_verdict(repo, rid, session(), "REROLL", "feature")
    fix(repo, 14)
    state = rn.gate_state(repo, rid, "feature")
    assert state["ready"] and state["match"] == "reroll-fix" and state["round"] == 2


def test_an_escalate_verdict_ends_the_gate(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    rn.record_verdict(repo, rid, session(), "ESCALATE", "feature")
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and "author" in state["reason"]
    with pytest.raises(rn.Refusal, match="ESCALATE"):
        rn.record_verdict(repo, rid, session(), "APPROVED", "feature")


def test_a_verdict_needs_an_admitted_head(repo):
    rid = rn.open_review(repo, "feature", "main")
    with pytest.raises(rn.Refusal, match="no completed review"):
        rn.record_verdict(repo, rid, session(), "APPROVED", "feature")
    answer(repo, rid)
    fix(repo, 15)
    with pytest.raises(rn.Refusal, match="stale"):
        rn.record_verdict(repo, rid, session(), "APPROVED", "feature")
    assert not [e for e in rn.entries(repo, rid) if e["kind"] == "verdict"]


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


@pytest.fixture
def two_clones(tmp_path):
    """A bare remote with main and feature, and two clones A and B."""
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
    return origin, clones[0], clones[1]


def test_rounds_count_verdicts_published_by_another_clone(two_clones):
    origin, a, b = two_clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    done = rn.record_verdict(a, rid, session(), "REROLL", "feature")
    assert done["level"] == "local"  # ticket 1300: the write is local, delivery comes later
    rn.sync(a)  # what the background sync (or the landing push) delivers
    state = rn.gate_state(b, rid, "feature")  # B never saw the review: the gate refreshes first
    assert state["ready"] and state["round"] == 2
    assert rn.record_verdict(b, rid, session(), "APPROVED", "feature")["entry"]["round"] == 2
    rn.sync(b)
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
    assert v["id"] == eid and level == "local" and v["gate_candidate"] == "0" * 40
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


def test_two_gate_runs_ruling_at_once_report_the_conflict(two_clones, monkeypatch):
    origin, a, b = two_clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    rn.record_verdict(a, rid, session(), "REROLL", "feature")
    rn.sync(a)
    real = rn.refresh
    calls = []

    def stale_once(cwd, remote="origin"):  # B's first refresh misses A's verdict, as in a race
        calls.append(cwd)
        if len(calls) == 1:
            sh(cwd, "fetch", "-q", "origin", rn.FETCH_NOTES)
            rn._integrate(cwd)
            sh(cwd, "update-ref", "refs/notes/review", "refs/notes/review~1")
            return {"status": "fetched", "warnings": []}
        return real(cwd, remote)

    monkeypatch.setattr(rn, "refresh", stale_once)
    done = rn.record_verdict(b, rid, session(), "REROLL", "feature")
    assert done["entry"]["round"] == 1  # the write is local (ticket 1300): no conflict seen yet
    rn.sync(b)  # the two round-1 verdicts meet
    assert len([v for v in rn._verdicts(b, rid) if v["round"] == 1]) == 2
    state = rn.gate_state(b, rid, "feature")
    assert state["round"] == 3 and not state["ready"]  # fails closed: past the cap


def test_an_old_scope_label_is_ignored(repo):
    """Ticket 1305 deleted the scope label and its carried chain; entries written before still
    carry `coverage`. Readers ignore it: an old uncarried delta on the head admits the gate."""
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid, coverage={"scope": "delta", "carried": None})
    state = rn.gate_state(repo, rid, "feature")
    assert state["ready"] and state["match"] == "equal"
    sh(repo, "switch", "-q", "feature")
    (Path(repo) / "tickets").mkdir()
    commit(repo, "tickets/0001-x.erg", "%erg 0.1\n", "ticket(1): close")
    state = rn.gate_state(repo, rid, "feature")
    assert state["ready"] and state["match"] == "bookkeeping"


def test_reroll_fix_must_descend_from_the_rerolled_head(repo):
    rid = rn.open_review(repo, "feature", "main")
    answer(repo, rid)
    rn.record_verdict(repo, rid, session(), "REROLL", "feature")
    sh(repo, "branch", "-q", "-f", "feature", "main")  # a head unrelated to the ruled one
    fix(repo, 16)
    state = rn.gate_state(repo, rid, "feature")
    assert not state["ready"] and state["match"] == "none"


# --- ticket 1291: the gate reads through refresh; the verdict write is the only push ---------

def logging_hook(origin, log):
    """An update hook on the bare origin that logs every pushed ref and rejects them all."""
    h = origin / "hooks" / "update"
    h.write_text(f'#!/bin/sh\necho "$1" >> {log}\necho "refused $1" >&2\nexit 1\n')
    h.chmod(0o755)


def test_gate_state_never_pushes_to_a_read_only_remote(two_clones, tmp_path):
    origin, a, b = two_clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    assert rn.publish(a, [e["id"] for e in rn.entries(a, rid)]) == "retrievable"
    rn.open_review(b, "feature", "origin/main")  # unpublished local entry: the old sync would push it
    tip = sh(origin, "rev-parse", "refs/notes/review")
    log = tmp_path / "pushed.log"
    logging_hook(origin, log)
    state = rn.gate_state(b, rid, "feature")
    assert state["ready"], state
    assert not log.exists()  # nothing was even attempted
    assert sh(origin, "rev-parse", "refs/notes/review") == tip
    r = cli(b, "gate", rid, "feature")
    assert r.returncode == 0, r.stderr
    assert not log.exists()
    # the verdict is written locally (ticket 1300); only its sync pushes: refused by the hook
    done = rn.record_verdict(b, rid, session(), "APPROVED", "feature")
    assert done["level"] == "local"
    assert not log.exists()
    with pytest.raises(rn.Refusal):
        rn.sync(b)
    assert log.exists() and log.read_text().strip()  # positive control: the hook log fires
    assert sh(origin, "rev-parse", "refs/notes/review") == tip


# --- ticket 1300: stale reads reported, the verdict write is local ----------------------------

def test_gate_state_stale_read_reports_staleness(two_clones, tmp_path):
    _, a, _ = two_clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    assert rn.gate_state(a, rid, "feature")["stale"] == ""
    sh(a, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    state = rn.gate_state(a, rid, "feature")
    assert state["ready"] and state["stale"]  # rules on local entries, says the round may be undercounted
    done = rn.record_verdict(a, rid, session(), "APPROVED", "feature")
    assert done["entry"]["round"] == 1 and done["stale"]


def test_failed_background_push_does_not_block_the_verdict(two_clones):
    import time
    origin, a, _ = two_clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    h = origin / "hooks" / "pre-receive"
    h.write_text("#!/bin/sh\nsleep 6\nexit 1\n")
    h.chmod(0o755)
    t0 = time.monotonic()
    r = cli(a, "verdict", "--review", rid, "--session", session(), "--verdict", "APPROVED", "--head", "feature")
    elapsed = time.monotonic() - t0
    assert r.returncode == 0, r.stderr
    assert elapsed < 5, elapsed
    assert r.stdout.split()[1] == "local"
    assert [e for e in rn.entries(a, rid) if e["kind"] == "verdict"]


# --- gaze 1855: two clones ruling one round are caught at the landing door -----------------

def test_push_for_landing_refuses_two_verdicts_for_one_round(two_clones):
    origin, a, b = two_clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    rn.sync(a)
    rn.refresh(b)
    assert rn.record_verdict(a, rid, session(), "APPROVED", "feature")["entry"]["round"] == 1
    assert rn.record_verdict(b, rid, session(), "REROLL", "feature")["entry"]["round"] == 1
    rn.sync(b)  # B's round-1 verdict reaches origin; A's is still local
    with pytest.raises(rn.Refusal, match="round 1"):
        rn.push_for_landing(a, "feature")


def test_push_for_landing_passes_a_single_verdict_per_round(two_clones):
    origin, a, b = two_clones
    rid = rn.open_review(a, "feature", "origin/main")
    answer(a, rid)
    rn.record_verdict(a, rid, session(), "APPROVED", "feature")
    assert "refs/notes/review" in rn.push_for_landing(a, "feature")
    assert sh(origin, "rev-parse", "refs/notes/review") == sh(a, "rev-parse", "refs/notes/review")
