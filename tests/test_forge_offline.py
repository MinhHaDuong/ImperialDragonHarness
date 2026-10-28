"""Ticket 1308: offline forge mode. Review reads wait a short bound and answer from the mapping
cached at first contact; a never-mapped PR stops; landing rechecks human and Copilot reviews
newer than the gate's forge read and refuses on an unresolved one."""

import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
from gaze_fixture import SETUP, fields, git, make_repo, run

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name, file=None):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (file or f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rn = _load("review_notes")
gaze_close = _load("gaze_close")
rl = _load("raid_land")

pytestmark = pytest.mark.integration

HANG = "#!/bin/sh\nexec sleep 60\n"  # exec: the timeout kills the process holding the pipes
NETFAIL = "#!/bin/sh\necho 'error connecting to api.github.com' >&2\nexit 1\n"


def offline(tmp_path, env, shim=HANG):
    (tmp_path / "bin" / "gh").write_text(shim)
    env["IDH_FORGE_READ_TIMEOUT"] = "1"
    return env


def drop_tree(primary):
    git(primary, "worktree", "remove", "--force", str(primary / ".claude" / "worktrees" / "review-7"))


# --- gaze ----------------------------------------------------------------------------------

def test_cached_pr_reviews_offline_without_forge_timeout(tmp_path):
    primary, env = make_repo(tmp_path)
    first = run(SETUP, ["7"], primary, env)
    assert first.returncode == 0, first.stderr
    assert fields(first.stdout)["forge"] == "read"
    drop_tree(primary)
    git(primary, "remote", "set-url", "origin", str(tmp_path / "gone"))
    offline(tmp_path, env)
    t0 = time.monotonic()
    r = run(SETUP, ["7"], primary, env)
    took = time.monotonic() - t0
    assert r.returncode == 0, r.stderr
    f = fields(r.stdout)
    assert f["forge"].startswith("unread (offline") and f["ci"] == "unread"
    assert f["review_id"] == fields(first.stdout)["review_id"]  # the local review, never a second one
    assert f["head"] == git(primary, "rev-parse", "refs/remotes/origin/feature")
    assert took < 10, f"setup waited {took:.1f}s on a hanging forge"  # one 1 s read, then the offline mark
    panel = Path(f["panel"])
    assert "forge: unread" in (panel / "comments.md").read_text()
    identity = json.loads((panel / "entry-state.json").read_text())
    assert identity["forge"].startswith("unread")
    # the answer says the forge context was unread, whatever the comment file held
    text = f"result: REVIEWED\nseats: self-only\nreviewed_head_sha: {f['head']}\nintent: default\n"
    assert gaze_close.record_answer(primary, "7", text, "", identity) == 0
    answer = [e for e in rn.entries(str(primary), f["review_id"]) if e["kind"] == "answer"][-1]
    assert answer["forge"].startswith("unread") and "\nforge: unread (offline" in answer["text"]


def test_first_review_offline_stops_cannot_map(tmp_path):
    primary, env = make_repo(tmp_path)
    offline(tmp_path, env)
    t0 = time.monotonic()
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 2 and "cannot map" in r.stderr, r.stderr
    assert time.monotonic() - t0 < 10
    assert rn.find_unit(str(primary), "pr:7") is None
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()


def test_network_error_is_unreachable_and_marks_offline(tmp_path, monkeypatch):
    forge = _load("forge")
    primary, env = make_repo(tmp_path)
    monkeypatch.setenv("PATH", env["PATH"])
    monkeypatch.setenv("MOCK_PR_JSON", env["MOCK_PR_JSON"])
    fg = forge.GhForge(str(primary))
    assert fg.resolve("7")["forge"] == "read"
    (tmp_path / "bin" / "gh").write_text(NETFAIL)
    rec = fg.resolve("7")
    assert rec["cached"] and rec["forge"].startswith("unread (offline: network")
    (tmp_path / "bin" / "gh").write_text("#!/bin/sh\necho called >> " + str(tmp_path / "calls") + "\nexit 1\n")
    with pytest.raises(forge.ForgeUnreachable):
        fg.comments("7")  # the offline mark: no network call at all
    fg.comment("7", "pointer")  # lenient: dropped
    assert not (tmp_path / "calls").exists()
    with pytest.raises(forge.ForgeRefusal):  # landing never answers from the cache
        forge.GhForge(str(primary), landing=True).resolve("7")
    assert (tmp_path / "calls").exists()


# --- verify-gate ---------------------------------------------------------------------------

def test_review_evidence_forge_unreachable_is_exit_4(tmp_path):
    primary, env = make_repo(tmp_path)
    offline(tmp_path, env)
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, str(SCRIPTS / "review_evidence.py"), "forge", "o/r", "7"],
                       cwd=primary, env=env, capture_output=True, text=True)
    assert r.returncode == 4 and "forge: unread (offline" in r.stdout, r.stdout + r.stderr
    assert time.monotonic() - t0 < 10


def test_review_evidence_forge_read_prints_its_time(tmp_path):
    primary, env = make_repo(tmp_path)
    page = {"pageInfo": {"hasNextPage": False}, "nodes": []}
    payload = {"data": {"repository": {"pullRequest": {"reviews": page, "comments": page, "reviewThreads": page}}}}
    (tmp_path / "bin" / "gh").write_text(f"#!/bin/sh\necho '{json.dumps(payload)}'\n")
    r = subprocess.run([sys.executable, str(SCRIPTS / "review_evidence.py"), "forge", "o/r", "7"],
                       cwd=primary, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("forge-read: 20") and r.stdout.strip().endswith("Z")


def test_verdict_records_forge_read(tmp_path):
    primary, env = make_repo(tmp_path)
    head = git(primary, "rev-parse", "origin/feature")
    rid = rn.open_review(str(primary), "feature", "origin/main", unit="pr:7", head=head)
    rn.add(str(primary), "answer", rid, {"run_id": "gz-x", "result": "REVIEWED", "seats": "panel",
                                         "coverage": {"scope": "full"}, "text": "t"}, head=head)
    done = rn.record_verdict(str(primary), rid, str(uuid.uuid4()), "APPROVED", head,
                             forge_read="2026-10-28T12:00:00Z")
    assert done["entry"]["forge_read"] == "2026-10-28T12:00:00Z"


# --- landing recheck -----------------------------------------------------------------------

class Forge:
    def __init__(self, blocking):
        self.blocking = blocking

    def review_state(self, pr):
        if isinstance(self.blocking, Exception):
            raise self.blocking
        return self.blocking


def verdict_at(tmp_path, forge_read):
    primary, _ = make_repo(tmp_path)
    head = git(primary, "rev-parse", "origin/feature")
    rid = rn.open_review(str(primary), "feature", "origin/main", unit="pr:7", head=head)
    rn.add(str(primary), "answer", rid, {"run_id": "gz-x", "result": "REVIEWED", "seats": "panel",
                                         "coverage": {"scope": "full"}, "text": "t"}, head=head)
    rn.record_verdict(str(primary), rid, str(uuid.uuid4()), "APPROVED", head, forge_read=forge_read)
    return primary, head


CR = {"what": "changes requested by MinhHaDuong", "at": "2026-10-28T13:00:00Z"}
THREAD = {"what": "unresolved thread on a.py (last by copilot)", "at": "2026-10-28T11:00:00Z"}


def test_landing_refuses_review_newer_than_gate_read(tmp_path):
    primary, head = verdict_at(tmp_path, "2026-10-28T12:00:00Z")
    with pytest.raises(rl.Refusal, match="changes requested"):
        rl.recheck_reviews(Forge([CR, THREAD]), "7", primary, head)
    rl.recheck_reviews(Forge([THREAD]), "7", primary, head)  # the gate read it: its ruling stands


def test_landing_after_offline_gate_counts_every_unresolved(tmp_path):
    primary, head = verdict_at(tmp_path, "unread")
    with pytest.raises(rl.Refusal, match="never read the forge.*unresolved thread"):
        rl.recheck_reviews(Forge([THREAD]), "7", primary, head)
    rl.recheck_reviews(Forge([]), "7", primary, head)


def test_landing_recheck_unreadable_refuses(tmp_path):
    primary, head = verdict_at(tmp_path, "2026-10-28T12:00:00Z")
    with pytest.raises(rl.Refusal, match="unreadable at landing"):
        rl.recheck_reviews(Forge(rl.forge.ForgeRefusal("gh timed out")), "7", primary, head)


def test_gh_review_state_parses_and_fails_closed(tmp_path, monkeypatch):
    forge = _load("forge")
    payload = {"data": {"repository": {"pullRequest": {
        "reviews": {"pageInfo": {"hasPreviousPage": False}, "nodes": [
            {"author": {"login": "h"}, "state": "CHANGES_REQUESTED", "submittedAt": "2026-10-28T10:00:00Z"},
            {"author": {"login": "h"}, "state": "APPROVED", "submittedAt": "2026-10-28T11:00:00Z"},
            {"author": {"login": "k"}, "state": "CHANGES_REQUESTED", "submittedAt": "2026-10-28T12:00:00Z"}]},
        "reviewThreads": {"pageInfo": {"hasNextPage": False}, "nodes": [
            {"isResolved": True, "path": "x", "comments": {"pageInfo": {"hasPreviousPage": False}, "nodes": [
                {"author": {"login": "c"}, "createdAt": "2026-10-28T09:00:00Z"}]}},
            {"isResolved": False, "path": "a.py", "comments": {"pageInfo": {"hasPreviousPage": False}, "nodes": [
                {"author": {"login": "c"}, "createdAt": "2026-10-28T09:00:00Z"},
                {"author": {"login": "h"}, "createdAt": "2026-10-28T09:30:00Z"}]}}]}}}}}
    bindir = tmp_path / "bin"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text(f"#!/bin/sh\ncat <<'EOF'\n{json.dumps(payload)}\nEOF\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    got = forge.GhForge(str(tmp_path), landing=True).review_state("7")
    assert got == [{"what": "changes requested by k", "at": "2026-10-28T12:00:00Z"},
                   {"what": "unresolved thread on a.py (last by h)", "at": "2026-10-28T09:30:00Z"}]
    payload["data"]["repository"]["pullRequest"]["reviewThreads"]["pageInfo"]["hasNextPage"] = True
    gh.write_text(f"#!/bin/sh\ncat <<'EOF'\n{json.dumps(payload)}\nEOF\n")
    with pytest.raises(forge.ForgeRefusal, match="more than one page"):
        forge.GhForge(str(tmp_path), landing=True).review_state("7")
