"""No-forge listings read local notes without conflating missing or unreadable evidence."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("listing_review_notes", SCRIPTS / "review_notes.py")
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)
pytestmark = pytest.mark.integration


def git(repo, *args, stdin=None):
    return subprocess.run(["git", "-C", str(repo), *args], input=stdin,
                          capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def project(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "tracked").write_text("base\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    git(repo, "switch", "-qc", "feature")
    (repo / "tracked").write_text("feature\n")
    git(repo, "commit", "-qam", "feature")
    return repo


def listing(project, state="all", *extra):
    return subprocess.run([sys.executable, str(SCRIPTS / "forge.py"), "--forge", "none",
                           "list", "--state", state, *extra], cwd=project,
                          capture_output=True, text=True)


def opened(project):
    rid = rn.open_review(project, "feature", "main", why="Review this", intent="Check behavior")
    req = rn.entries(project, rid)[-1]
    return rid, req


def abandon(project, rid, req):
    fn = getattr(rn, "abandon", None)
    assert callable(fn), "explicit per-request abandonment is not implemented"
    return fn(project, rid, req["request_id"], "No longer needed")


def test_listing_open_row_and_filters_without_transport(project):
    rid, req = opened(project)
    git(project, "remote", "add", "origin", "/unreachable/fixture-only.git")
    before = git(project, "config", "--list")
    result = listing(project, "open")
    assert result.returncode == 0, result.stderr
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    assert rows[0] == {"number": rid, "branch": "feature", "title": "Review this",
                       "body": "Check behavior", "auto": False, "mergedAt": None,
                       "cross_repository": False, "head_repository": None,
                       "state": "OPEN", "review_id": rid, "request_id": req["request_id"]}
    assert git(project, "config", "--list") == before
    assert json.loads(listing(project, "merged").stdout) == []
    assert json.loads(listing(project, "all", "--head", "other").stdout) == []
    assert json.loads(listing(project, "all", "--limit", "0").stdout) == []


def test_missing_store_is_three_but_readable_empty_is_answer(project):
    assert listing(project).returncode == 3
    tree = git(project, "mktree", stdin="")
    commit = git(project, "commit-tree", tree, "-m", "empty notes")
    git(project, "update-ref", rn.REF, commit)
    result = listing(project)
    assert result.returncode == 0
    assert json.loads(result.stdout) == []


@pytest.mark.parametrize("damage", ["json", "schema", "conflicting-id", "wrong-object"])
def test_unreadable_store_never_answers_empty(project, damage):
    rid, req = opened(project)
    if damage == "wrong-object":
        blob = git(project, "hash-object", "-w", "--stdin", stdin="not a notes commit")
        git(project, "update-ref", rn.REF, blob)
    else:
        payload = "{" if damage == "json" else json.dumps({"id": "incomplete"})
        if damage == "conflicting-id":
            payload = json.dumps({**req, "why": "changed under same ID"})
        git(project, "notes", f"--ref={rn.REF}", "append", "-m", payload, rn.anchor(project, rid))
    result = listing(project)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr


def test_pinned_request_head_not_current_branch_tip_defines_merge(project):
    rid, req = opened(project)
    git(project, "switch", "main")
    git(project, "merge", "--ff-only", "feature")
    git(project, "switch", "feature")
    (project / "tracked").write_text("unrequested change\n")
    git(project, "commit", "-qam", "later branch tip")
    result = listing(project, "merged")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["number"] == rid
    assert json.loads(result.stdout)[0]["state"] == "MERGED"
    assert req["head"] != git(project, "rev-parse", "feature")


def test_deleted_branch_remains_open(project):
    opened(project)
    git(project, "switch", "main")
    git(project, "branch", "-D", "feature")
    result = listing(project, "open")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["state"] == "OPEN"


def test_abandon_is_explicit_request_bound_append_and_new_request_reopens(project):
    rid, req = opened(project)
    before = rn.entries(project, rid)
    entry = abandon(project, rid, req)
    assert entry["kind"] == "abandon" and entry["request_id"] == req["request_id"]
    assert rn.entries(project, rid)[:-1] == before
    assert json.loads(listing(project).stdout)[0]["state"] == "ABANDONED"
    assert json.loads(listing(project, "open").stdout) == []
    rn.request(project, rid, "feature", "main")
    assert json.loads(listing(project, "open").stdout)[0]["state"] == "OPEN"
    # Repeating abandonment of the older request cannot close the new one.
    abandon(project, rid, req)
    assert json.loads(listing(project, "open").stdout)[0]["state"] == "OPEN"


def test_abandon_cli_requires_explicit_request_and_preserves_pinned_binding(project):
    rid, req = opened(project)
    command = [sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(project),
               "abandon", "--review", rid, "--request", req["request_id"], "--reason", "withdrawn"]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    event = rn.entries(project, rid)[-1]
    assert event["kind"] == "abandon"
    assert all(event[k] == req[k] for k in ("head", "base", "base_ref", "merge_base", "range_patch_id"))
    bad = subprocess.run([*command[:-3], "missing", "--reason", "withdrawn"], capture_output=True)
    assert bad.returncode != 0


def test_native_and_ever_adopted_pr_units_never_mix(project):
    native, _ = opened(project)
    adopted, _ = opened(project)
    rn.request(project, adopted, "feature", "main", unit="pr:7")
    assert {r["number"] for r in json.loads(listing(project).stdout)} == {native}


def test_branch_reuse_and_latest_request_per_review(project):
    first, _ = opened(project)
    rn.request(project, first, "feature", "main")
    second, _ = opened(project)
    rows = json.loads(listing(project).stdout)
    assert len(rows) == 2 and {r["number"] for r in rows} == {first, second}
    assert len(json.loads(listing(project, "all", "--limit", "1").stdout)) == 1


def test_missing_base_is_unknown_not_empty_even_with_filter(project):
    opened(project)
    git(project, "branch", "-D", "main")
    result = listing(project, "all", "--head", "other")
    assert result.returncode == 2 and result.stdout == ""


def test_unreadable_blob_and_non_utf8_are_could_not_look(project):
    rid, _ = opened(project)
    blob = git(project, "notes", f"--ref={rn.REF}", "list").split()[0]
    (project / ".git" / "objects" / blob[:2] / blob[2:]).unlink()
    result = listing(project)
    assert result.returncode == 2 and result.stdout == ""


def test_invalid_utf8_note_is_could_not_look(project):
    rid, _ = opened(project)
    blob = subprocess.run(["git", "-C", str(project), "hash-object", "-w", "--stdin"],
                          input=b"\xff", capture_output=True, check=True).stdout.decode().strip()
    git(project, "notes", f"--ref={rn.REF}", "add", "-f", "-C", blob, rn.anchor(project, rid))
    result = listing(project)
    assert result.returncode == 2 and result.stdout == ""


def test_limit_orders_by_latest_request_not_review_creation(project):
    first, _ = opened(project)
    opened(project)
    rn.request(project, first, "feature", "main")
    result = listing(project, "all", "--limit", "1")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["number"] == first
