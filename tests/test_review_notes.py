"""Ticket 1273: scripts/review_notes.py, the one door to refs/notes/review
(spec conception/2026-10-27-notes-review-spec.md). Temp repos and a local bare
remote only; nothing reaches a forge."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("review_notes", SCRIPTS / "review_notes.py")
assert spec and spec.loader
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)

pytestmark = pytest.mark.integration


def sh(cwd, *args, check=True):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    if check and done.returncode:
        raise AssertionError(f"git {args}: {done.stderr}")
    return done.stdout.strip()


def ident(repo):
    sh(repo, "config", "user.email", "t@example.com")
    sh(repo, "config", "user.name", "T")


@pytest.fixture(autouse=True)
def no_backoff(monkeypatch):
    monkeypatch.setenv("IDH_REVIEW_BACKOFF", "0")


@pytest.fixture
def world(tmp_path):
    """A bare remote with main and feature, and two clones A and B."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
    ident(seed)
    (seed / "f.py").write_text("def f():\n    return 1\n\n\n\n\n\ndef g():\n    return 2\n")
    (seed / "other.txt").write_text("x\n")
    sh(seed, "add", ".")
    sh(seed, "commit", "-qm", "base")
    sh(seed, "remote", "add", "origin", str(origin))
    sh(seed, "push", "-q", "origin", "main")
    sh(seed, "switch", "-qc", "feature")
    (seed / "f.py").write_text("def f():\n    return 10\n\n\n\n\n\ndef g():\n    return 2\n")
    sh(seed, "commit", "-qam", "feature edit")
    sh(seed, "push", "-q", "origin", "feature")
    clones = []
    for name in ("A", "B"):
        c = tmp_path / name
        subprocess.run(["git", "clone", "-q", str(origin), str(c)], check=True)
        ident(c)
        sh(c, "branch", "-q", "feature", "origin/feature")
        clones.append(c)
    return origin, clones[0], clones[1], seed


def raw_note(repo, review_id, ref="refs/notes/review"):
    return sh(repo, "notes", f"--ref={ref}", "show", rn.anchor(repo, review_id))


def test_open_writes_one_json_line_on_a_review_anchor(world):
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main", why="w", intent="i")
    anchor = rn.anchor(a, rid)
    assert subprocess.run(["git", "-C", str(a), "cat-file", "-e", anchor]).returncode != 0  # no stored object
    lines = [ln for ln in raw_note(a, rid).split("\n") if ln.strip()]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert list(entry)[0] == "ts"
    for key in rn.REQUIRED:
        assert key in entry, key
    assert entry["kind"] == "request" and entry["branch"] == "feature"
    assert entry["head"] == sh(a, "rev-parse", "feature")
    assert "available in the Git repository" in entry["what"]
    assert entry["range_patch_id"]


def test_readers_skip_blank_lines_and_newlines_stay_escaped(world):
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rn.add(a, "report", rid, {"run_id": "gz-1", "seat_id": "gz-1:a", "status": "ran",
                              "text": "two\nlines here"})
    raw = raw_note(a, rid)
    assert "\n\n" in raw  # notes append separates with a blank line
    assert all(json.loads(ln) for ln in raw.split("\n") if ln.strip())
    kinds = [e["kind"] for e in rn.entries(a, rid)]
    assert kinds == ["request", "report"]


def test_setup_is_idempotent_and_a_no_op_without_remote(world, tmp_path):
    _, a, _, _ = world
    assert rn.setup(a) == "origin"
    rn.setup(a)
    fetch = sh(a, "config", "--get-all", "remote.origin.fetch").splitlines()
    assert fetch.count("+refs/notes/review*:refs/notes/origin/review*") == 1
    assert "+refs/notes/review:refs/notes/origin/review" not in fetch  # ticket 1300: no exact spec
    assert fetch.count("refs/review-heads/*:refs/review-heads/*") == 1
    assert sh(a, "config", "notes.review.mergeStrategy") == "cat_sort_uniq"
    assert sh(a, "config", "--get-all", "remote.origin.push", check=False) == ""
    lone = tmp_path / "lone"
    subprocess.run(["git", "init", "-q", str(lone)], check=True)
    assert rn.setup(lone) is None
    assert sh(lone, "config", "--get-all", "remote.origin.fetch", check=False) == ""


def test_publish_reads_back_and_without_remote_stays_local(world, tmp_path):
    _, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    ids = [e["id"] for e in rn.entries(a, rid)]
    assert rn.publish(a, ids) == "retrievable"
    assert sh(a, "ls-remote", "origin", "refs/notes/review").split()[0] == sh(a, "rev-parse", "refs/notes/review")
    rn.sync(b)
    assert rn.find(b, "feature") == rid
    lone = tmp_path / "lone"
    subprocess.run(["git", "init", "-q", "-b", "main", str(lone)], check=True)
    ident(lone)
    (lone / "x").write_text("1\n")
    sh(lone, "add", "x")
    sh(lone, "commit", "-qm", "x")
    sh(lone, "switch", "-qc", "feat")
    (lone / "x").write_text("2\n")
    sh(lone, "commit", "-qam", "y")
    rid2 = rn.open_review(lone, "feat", "main")
    assert rn.publish(lone, [e["id"] for e in rn.entries(lone, rid2)]) == "done-unpublished"


def test_concurrent_appends_to_one_review_from_two_clones_lose_nothing(world):
    _, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rn.publish(a, [])
    rn.sync(b)
    ea = rn.add(a, "report", rid, {"run_id": "gz-a", "seat_id": "gz-a:x", "status": "ran", "text": "A"})
    eb = rn.add(b, "report", rid, {"run_id": "gz-b", "seat_id": "gz-b:y", "status": "ran", "text": "B"})
    assert rn.publish(a, [ea["id"]]) == "retrievable"
    assert rn.publish(b, [eb["id"]]) == "retrievable"  # rejected once, merged, pushed
    rn.sync(a)
    for repo in (a, b):
        got = [e["id"] for e in rn.entries(repo, rid)]
        assert len(got) == len(set(got)) == 3
        assert ea["id"] in got and eb["id"] in got
    # never a forced update: the remote tip descends from both publications
    tip = sh(a, "ls-remote", "origin", "refs/notes/review").split()[0]
    assert sh(a, "rev-parse", "refs/notes/review") == tip


def test_coverage_equal_patch_id_and_misses(world):
    _, a, _, seed = world
    rid = rn.open_review(a, "feature", "origin/main")
    head = sh(a, "rev-parse", "feature")
    rn.add(a, "answer", rid, {"run_id": "gz-1", "result": "REVIEWED", "seats": "panel",
                              "coverage": {"scope": "full"}})
    assert rn.coverage(a, rid, head)["match"] == "equal"
    # a clean rebase onto a base that changed another file keeps the verbatim patch-id
    sh(seed, "switch", "-q", "main")
    (seed / "other.txt").write_text("y\n")
    sh(seed, "commit", "-qam", "base moves")
    sh(seed, "push", "-q", "origin", "main")
    sh(a, "fetch", "-q", "origin")
    sh(a, "switch", "-q", "feature")
    sh(a, "rebase", "-q", "origin/main")
    rebased = sh(a, "rev-parse", "HEAD")
    assert rebased != head
    assert rn.coverage(a, rid, rebased)["match"] == "patch-id"
    # an indentation-only change is a different verbatim id
    (a / "f.py").write_text((a / "f.py").read_text().replace("    return 10", "\treturn 10"))
    sh(a, "commit", "-qam", "tabs")
    assert rn.coverage(a, rid, sh(a, "rev-parse", "HEAD"))["match"] == "none"


def test_empty_range_never_matches(world):
    _, a, _, _ = world
    sh(a, "branch", "-q", "empty", "origin/main")
    rid = rn.open_review(a, "empty", "origin/main")
    rn.add(a, "answer", rid, {"run_id": "gz-1", "result": "REVIEWED", "seats": "panel",
                              "coverage": {"scope": "full"}})
    assert rn.entries(a, rid)[-1]["range_patch_id"] == ""
    sh(a, "switch", "-qc", "empty2", "origin/main")
    sh(a, "commit", "-q", "--allow-empty", "-m", "nothing")
    assert rn.coverage(a, rid, sh(a, "rev-parse", "HEAD"))["match"] == "none"


def test_delta_answer_alone_is_not_full(world):
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    head = sh(a, "rev-parse", "feature")
    rn.add(a, "answer", rid, {"run_id": "gz-1", "result": "REVIEWED", "seats": "panel",
                              "coverage": {"scope": "delta"}})
    assert rn.coverage(a, rid, head)["match"] == "delta"


def test_review_head_is_kept_published_and_checked(world, tmp_path):
    origin, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rq = rn.entries(a, rid)[0]["request_id"]
    ref = f"refs/review-heads/{rid}/{rq}"
    head = sh(a, "rev-parse", "feature")
    assert sh(a, "rev-parse", ref) == head
    rn.publish(a, [])
    assert sh(a, "ls-remote", "origin", ref).split()[0] == head
    # someone moves the remote review-head
    sh(b, "fetch", "-q", "origin")
    sh(b, "push", "-q", "-f", "origin", f"origin/main:{ref}")
    report = rn.sync(a)
    assert any("review-head" in w and "moved" in w for w in report["warnings"]), report


def test_rewritten_remote_is_detected_and_entries_republished(world):
    origin, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rn.publish(a, [])
    ids = {e["id"] for e in rn.entries(a, rid)}
    # B forges a fresh, unrelated notes history and force-pushes it
    other = rn.open_review(b, "feature", "origin/main")
    sh(b, "push", "-q", "-f", "origin", "refs/notes/review:refs/notes/review")
    report = rn.sync(a)
    assert any("rewritten" in w for w in report["warnings"]), report
    rn.sync(b)
    assert ids <= {e["id"] for e in rn.entries(b, rid)}
    assert rn.find(b, "feature") in (rid, other)


def test_dropped_entry_under_a_descendant_is_detected(world):
    origin, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    e2 = rn.add(a, "report", rid, {"run_id": "gz-1", "seat_id": "gz-1:x", "status": "ran", "text": "t"})
    rn.publish(a, [])
    rn.sync(b)
    keep = [ln for ln in raw_note(b, rid).split("\n") if ln.strip() and e2["id"] not in ln]
    sh(b, "notes", "--ref=review", "add", "-f", "-m", "\n".join(keep), rn.anchor(b, rid))
    sh(b, "push", "-q", "origin", "refs/notes/review:refs/notes/review")  # fast-forward
    report = rn.sync(a)
    assert any("missing" in w for w in report["warnings"]), report
    sh(b, "fetch", "-q", "origin", "+refs/notes/review:refs/notes/origin/review")
    assert e2["id"] in sh(b, "notes", "--ref=refs/notes/origin/review", "show", rn.anchor(b, rid))


def test_content_replaced_under_an_unchanged_id_is_rejected(world):
    origin, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rn.add(a, "answer", rid, {"run_id": "gz-1", "result": "FINDINGS", "seats": "panel",
                              "coverage": {"scope": "full"}})
    rn.publish(a, [])
    rn.sync(b)
    forged = raw_note(b, rid).replace('"FINDINGS"', '"REVIEWED"')
    sh(b, "notes", "--ref=review", "add", "-f", "-m", forged, rn.anchor(b, rid))
    sh(b, "push", "-q", "origin", "refs/notes/review:refs/notes/review")
    with pytest.raises(rn.Tamper):
        rn.sync(a)
    assert '"FINDINGS"' in raw_note(a, rid) and '"REVIEWED"' not in raw_note(a, rid)


def test_findings_open_set_over_the_whole_history(world):
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rn.add(a, "report", rid, {"run_id": "gz-1", "seat_id": "gz-1:x", "status": "ran", "text": "t",
                              "findings": [{"finding_id": "gz-1/x/1"}, {"finding_id": "gz-1/x/2"}]})
    rn.request(a, rid, "feature", "origin/main", responses=[{"finding_id": "gz-1/x/1", "disposition": "fixed"}])
    rn.request(a, rid, "feature", "origin/main", responses=[])
    assert [f["finding_id"] for f in rn.open_findings(a, rid)] == ["gz-1/x/2"]


def test_find_takes_the_latest_request_naming_the_branch(world):
    _, a, _, _ = world
    first = rn.open_review(a, "feature", "origin/main")
    second = rn.open_review(a, "feature", "origin/main")
    assert first != second and rn.find(a, "feature") == second
    assert rn.find(a, "nope") is None


def test_export_import_round_trip(world, tmp_path):
    _, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rn.add(a, "plan", rid, {"run_id": "gz-1", "manifest": "m"})
    dump = tmp_path / "x.jsonl"
    dump.write_text(rn.export(a, rid))
    assert rn.import_file(b, dump) == 2
    assert rn.import_file(b, dump) == 0
    assert [e["id"] for e in rn.entries(b, rid)] == [e["id"] for e in rn.entries(a, rid)]


def test_prune_is_refused(world):
    _, a, _, _ = world
    done = subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(a), "prune"],
                          capture_output=True, text=True)
    assert done.returncode == 2 and "forbidden" in done.stderr


def test_cli_open_add_show_coverage(world):
    _, a, _, _ = world
    def cli(*args):
        return subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(a), *args],
                              capture_output=True, text=True)
    rid = cli("open", "--branch", "feature", "--base-ref", "origin/main", "--why", "w").stdout.strip()
    assert rid.startswith("rv-")
    head = sh(a, "rev-parse", "feature")
    r = cli("add", "answer", "--review", rid, "--json", json.dumps(
        {"run_id": "gz-1", "result": "REVIEWED", "seats": "panel", "coverage": {"scope": "full"}}))
    assert r.returncode == 0, r.stderr
    cov = json.loads(cli("coverage", rid, head).stdout)
    assert cov["match"] == "equal" and cov["result"] == "REVIEWED"
    assert cli("find", "feature").stdout.strip() == rid
    assert len(cli("show", rid).stdout.strip().splitlines()) == 2


def test_none_forge_resolve_carries_the_review_id(world):
    _, a, _, _ = world
    fspec = importlib.util.spec_from_file_location("forge", SCRIPTS / "forge.py")
    forge = importlib.util.module_from_spec(fspec)
    fspec.loader.exec_module(forge)
    f = forge.get_forge("none", cwd=str(a))
    assert f.resolve("branch:feature")["review_id"] is None
    rid = rn.open_review(a, "feature", "origin/main")
    assert f.resolve("branch:feature")["review_id"] == rid


def test_none_forge_resolve_surfaces_a_tampered_store(world):
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    line = raw_note(a, rid).strip()
    sh(a, "notes", "--ref=review", "append", "-m", line.replace('"hunt"', '"forged"'), rn.anchor(a, rid))
    fspec = importlib.util.spec_from_file_location("forge", SCRIPTS / "forge.py")
    forge = importlib.util.module_from_spec(fspec)
    fspec.loader.exec_module(forge)
    with pytest.raises(forge.ForgeRefusal, match="(?i)tamper"):
        forge.get_forge("none", cwd=str(a)).resolve("branch:feature")


# --- ticket 1281: retained heads verified, reader bootstrap, request identity frozen ---------

def forge_module():
    fspec = importlib.util.spec_from_file_location("forge", SCRIPTS / "forge.py")
    forge = importlib.util.module_from_spec(fspec)
    fspec.loader.exec_module(forge)
    return forge


def hook(origin, refuse):
    """An update hook on the bare origin that rejects every ref matching the shell glob `refuse`."""
    h = origin / "hooks" / "update"
    h.write_text(f'#!/bin/sh\ncase "$1" in {refuse}) echo "refused $1" >&2; exit 1;; esac\nexit 0\n')
    h.chmod(0o755)


def test_publish_is_not_retrievable_when_the_review_heads_are_rejected(world, capsys):
    origin, a, _, _ = world
    hook(origin, "refs/review-heads/*")
    rid = rn.open_review(a, "feature", "origin/main")
    req = rn.entries(a, rid)[0]
    ref = f"refs/review-heads/{rid}/{req['request_id']}"
    level = rn.publish(a, [req["id"]])
    assert level != "retrievable"
    assert sh(a, "ls-remote", "origin", "refs/review-heads/*") == ""  # the reject stood
    assert sh(a, "ls-remote", "origin", "refs/notes/review")  # the notes went through
    assert ref in capsys.readouterr().err  # the failure is visible, naming the ref
    # all local evidence stays for a retry: the entry and the kept head
    assert [e["id"] for e in rn.entries(a, rid)] == [req["id"]]
    assert sh(a, "rev-parse", ref) == req["head"]
    (origin / "hooks" / "update").unlink()
    assert rn.publish(a, [req["id"]]) == "retrievable"


def test_publish_reports_a_moved_remote_review_head_and_never_forces_it(world, capsys):
    origin, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    req = rn.entries(a, rid)[0]
    ref = f"refs/review-heads/{rid}/{req['request_id']}"
    sh(b, "commit", "-q", "--allow-empty", "-m", "unrelated")  # not a descendant of the head
    squatter = sh(b, "rev-parse", "HEAD")
    sh(b, "push", "-q", "origin", f"HEAD:{ref}")
    assert rn.publish(a, [req["id"]]) != "retrievable"
    assert sh(a, "ls-remote", "origin", ref).split()[0] == squatter  # not overwritten
    assert "moved" in capsys.readouterr().err
    assert sh(a, "rev-parse", ref) == req["head"]


def test_a_fresh_clone_bootstrap_finds_the_published_review(world):
    origin, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    assert rn.publish(a, [rn.entries(a, rid)[0]["id"]]) == "retrievable"
    # B has an unpublished entry of its own, then follows the documented bootstrap
    sh(b, "switch", "-qc", "side", "origin/main")
    sh(b, "commit", "-q", "--allow-empty", "-m", "side")
    mine = rn.open_review(b, "side", "origin/main")
    rn.setup(b)
    sh(b, "fetch", "-q", "origin")
    hook(origin, "refs/*")  # a reader: no push needed, and none happens
    tip = sh(origin, "rev-parse", "refs/notes/review")
    assert rn.resolve(b, "feature") == rid
    assert forge_module().get_forge("none", cwd=str(b)).resolve("branch:feature")["review_id"] == rid
    assert rn.find(b, "side") == mine and rn.entries(b, mine)  # local unpublished entry kept
    assert sh(origin, "rev-parse", "refs/notes/review") == tip


def test_a_fetch_failure_is_not_read_as_no_review(world, tmp_path):
    _, _, b, _ = world
    sh(b, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    with pytest.raises(rn.Refusal):
        rn.resolve(b, "feature")
    forge = forge_module()
    with pytest.raises(forge.ForgeRefusal):
        forge.get_forge("none", cwd=str(b)).resolve("branch:feature")


def two_rounds(a):
    rid = rn.open_review(a, "feature", "origin/main")
    r1 = rn.entries(a, rid)[0]
    sh(a, "switch", "-q", "feature")
    sh(a, "commit", "-q", "--allow-empty", "-m", "round 2")
    r2 = rn.request(a, rid, "feature", "origin/main")
    assert r2["head"] != r1["head"]
    return rid, r1, r2


def test_a_late_answer_from_round_one_is_not_bound_to_round_two(world):
    _, a, _, _ = world
    rid, r1, r2 = two_rounds(a)
    fields = {"run_id": "gz-r1", "result": "REVIEWED", "seats": "panel", "coverage": {"scope": "full"}}
    with pytest.raises(rn.Refusal, match="request"):
        rn.add(a, "answer", rid, fields, head=r1["head"])  # no request named: never inferred as latest
    late = rn.add(a, "answer", rid, fields, head=r1["head"], request_id=r1["request_id"])
    assert late["request_id"] == r1["request_id"] and late["head"] == r1["head"]
    with pytest.raises(rn.Refusal, match="no request"):
        rn.add(a, "report", rid, {"run_id": "gz-r1"}, request_id="rq-nope")
    plan = rn.add(a, "plan", rid, {"run_id": "gz-r2"}, request_id=r2["request_id"])
    assert plan["request_id"] == r2["request_id"] and plan["head"] == r2["head"]


def test_a_named_request_on_another_head_is_refused(world):
    """gaze 1817 finding 1: an explicit request id never binds an entry on another head."""
    _, a, _, _ = world
    rid, r1, r2 = two_rounds(a)
    with pytest.raises(rn.Refusal, match="head"):
        rn.add(a, "answer", rid, {"run_id": "gz-x"}, head=r1["head"], request_id=r2["request_id"])


def test_an_entry_on_another_head_is_refused_even_with_one_request(world):
    """gaze 1817 round 2: the implicit path binds the latest request only on its own head."""
    _, a, _, _ = world
    sh(a, "switch", "-q", "feature")
    old = sh(a, "rev-parse", "HEAD")
    sh(a, "commit", "-q", "--allow-empty", "-m", "later")
    rid = rn.open_review(a, "feature", "origin/main")  # its only request is on the later head
    with pytest.raises(rn.Refusal, match="head"):
        rn.add(a, "answer", rid, {"run_id": "gz-x"}, head=old)


def test_a_symbolic_head_is_resolved_once(world, monkeypatch):
    """gaze 1817 round 3: the ref checked against the request is the commit bound, even if the
    branch moves between the check and the write."""
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    req = rn.entries(a, rid)[0]
    sh(a, "switch", "-q", "feature")
    sh(a, "commit", "-q", "--allow-empty", "-m", "moved")
    moved = sh(a, "rev-parse", "HEAD")
    sh(a, "reset", "-q", "--hard", req["head"])
    real, calls = rn._rev, []

    def racing(cwd, ref):  # the branch moves right after its first resolution
        calls.append(ref)
        return moved if ref == "feature" and calls.count("feature") > 1 else real(cwd, ref)
    monkeypatch.setattr(rn, "_rev", racing)
    e = rn.add(a, "answer", rid, {"run_id": "gz-x"}, head="feature", request_id=req["request_id"])
    assert e["head"] == req["head"]


def _lock_path(repo):
    return Path(sh(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "idh-review-notes.lock"



def _add(repo, rid, env):
    import os
    return subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(repo), "add", "plan",
                           "--review", rid, "--json", json.dumps({"text": "x"})],
                          capture_output=True, text=True, env={**os.environ, **env})


def _rid(repo):
    out = subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(repo), "open",
                          "--branch", "feature", "--base-ref", "main"], capture_output=True, text=True, check=True)
    return out.stdout.split()[0]


def test_add_refuses_when_lock_held(world):
    import fcntl
    _, a, _, _ = world
    rid = _rid(a)
    before = raw_note(a, rid)
    with open(_lock_path(a), "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        done = _add(a, rid, {"IDH_NOTES_LOCK_WAIT": "0.3"})
    assert done.returncode != 0 and "idh-review-notes.lock" in done.stderr
    assert raw_note(a, rid) == before


def test_add_waits_then_writes(world):
    import fcntl
    import threading
    import time
    _, a, _, _ = world
    rid = _rid(a)
    fh = open(_lock_path(a), "a")
    fcntl.flock(fh, fcntl.LOCK_EX)

    def release():
        time.sleep(0.5)
        fcntl.flock(fh, fcntl.LOCK_UN)
    t = threading.Thread(target=release)
    t.start()
    done = _add(a, rid, {"IDH_NOTES_LOCK_WAIT": "10"})
    t.join()
    fh.close()
    assert done.returncode == 0, done.stderr
    assert raw_note(a, rid).count('"kind": "plan"') + raw_note(a, rid).count('"kind":"plan"') == 1


def test_integrate_creating_the_ref_takes_the_lock(world, monkeypatch):
    import fcntl
    _, a, _, _ = world
    sh(a, "update-ref", rn.TRACK, sh(a, "rev-parse", "HEAD"))
    monkeypatch.setenv("IDH_NOTES_LOCK_WAIT", "0.2")
    with open(_lock_path(a), "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        with pytest.raises(rn.Refusal, match="idh-review-notes.lock"):
            rn._integrate(a)
    assert sh(a, "rev-parse", "--verify", "-q", rn.REF, check=False) == ""


# --- ticket 1299: push_for_landing -------------------------------------------------

def _two_reviews(a):
    sh(a, "branch", "-q", "other", "feature")
    r1 = rn.open_review(str(a), "feature", "origin/main")
    r2 = rn.open_review(str(a), "other", "origin/main")
    return r1, r2


def test_push_for_landing_pushes_only_the_branchs_review_heads(world):
    origin, a, _b, _seed = world
    r1, r2 = _two_reviews(a)
    pushed = rn.push_for_landing(str(a), "feature")
    assert rn.REF in pushed and len(pushed) == 2
    heads = sh(origin, "for-each-ref", "--format=%(refname)", f"{rn.HEADS}/").splitlines()
    assert len(heads) == 1 and f"/{r1}/" in heads[0] and r2 not in heads[0]
    assert sh(origin, "rev-parse", rn.REF) == sh(a, "rev-parse", rn.REF)


def test_push_for_landing_raises_when_the_remote_rejects(world, no_backoff):
    origin, a, _b, _seed = world
    _two_reviews(a)
    hook = origin / "hooks" / "pre-receive"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text("#!/bin/sh\nwhile read o n r; do case \"$r\" in refs/notes/*) exit 1;; esac; done\nexit 0\n")
    hook.chmod(0o755)
    with pytest.raises(rn.Refusal):
        rn.push_for_landing(str(a), "feature")


def test_push_for_landing_no_remote_and_no_notes_are_no_ops(world, tmp_path):
    origin, a, _b, _seed = world
    assert rn.push_for_landing(str(a), "feature") == []  # remote, no review for the branch
    assert sh(origin, "for-each-ref", "refs/notes/", f"{rn.HEADS}/") == ""
    lone = tmp_path / "lone"
    subprocess.run(["git", "init", "-q", "-b", "main", str(lone)], check=True)
    ident(lone)
    (lone / "x").write_text("x\n")
    sh(lone, "add", ".")
    sh(lone, "commit", "-qm", "x")
    assert rn.push_for_landing(str(lone), "main") == []


# --- ticket 1300: PR units, lenient readers, background sync ----------------------------------

def test_setup_fetch_refspecs_tolerate_a_notes_less_origin(world):
    """PR #1852: an exact refs/notes/review refspec made every plain `git fetch origin` exit 128
    while origin had no notes. The positive control shows the old spec failing on this origin."""
    _, a, b, _ = world
    sh(b, "config", "--add", "remote.origin.fetch", "+refs/notes/review:refs/notes/origin/review")
    assert subprocess.run(["git", "-C", str(b), "fetch", "-q", "origin"], capture_output=True).returncode
    rn.setup(b)  # migrates the exact spec away
    assert subprocess.run(["git", "-C", str(b), "fetch", "-q", "origin"], capture_output=True).returncode == 0
    rn.setup(a)
    assert subprocess.run(["git", "-C", str(a), "fetch", "-q", "origin"], capture_output=True).returncode == 0


def test_refresh_unreachable_remote_is_stale_not_refusal(world, tmp_path):
    _, a, _, _ = world
    sh(a, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    report = rn.refresh(a)
    assert report["status"] == "stale" and report["warnings"]


def test_resolve_stale_returns_local_review(world, tmp_path, capsys):
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    pr = rn.open_review(a, "feature", "origin/main", unit="pr:7")
    sh(a, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    assert rn.resolve(a, "feature") == rid
    assert rn.resolve_unit(a, "pr:7") == pr
    assert "stale" in capsys.readouterr().err


def test_resolve_stale_without_local_refuses_naming_remote(world, tmp_path):
    _, _, b, _ = world
    sh(b, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    with pytest.raises(rn.Refusal, match="remote unreadable, no local review"):
        rn.resolve(b, "feature")
    with pytest.raises(rn.Refusal, match="remote unreadable, no local review"):
        rn.resolve_unit(b, "pr:7")


def test_tamper_still_raises_under_lenient_refresh(world):
    origin, a, b, _ = world
    rid = rn.open_review(a, "feature", "origin/main")
    rn.add(a, "answer", rid, {"run_id": "gz-1", "result": "FINDINGS", "seats": "panel",
                              "coverage": {"scope": "full"}})
    rn.sync(a)
    rn.sync(b)
    forged = raw_note(b, rid).replace('"FINDINGS"', '"REVIEWED"')
    sh(b, "notes", "--ref=review", "add", "-f", "-m", forged, rn.anchor(b, rid))
    sh(b, "push", "-q", "origin", "refs/notes/review:refs/notes/review")
    with pytest.raises(rn.Tamper):
        rn.refresh(a)


def test_find_unit_ignores_reused_branch_name(world):
    """A PR number is never reused; a branch name is (merge never deletes branches)."""
    _, a, _, _ = world
    plain = rn.open_review(a, "feature", "origin/main")
    old = rn.open_review(a, "feature", "origin/main", unit="pr:6")
    assert rn.find_unit(a, "pr:7") is None
    new = rn.open_review(a, "feature", "origin/main", unit="pr:7")
    assert rn.find_unit(a, "pr:7") == new and rn.find_unit(a, "pr:6") == old
    assert rn.find(a, "feature") == plain  # a branch unit never binds a PR review
    later = rn.request(a, new, "feature", "origin/main")
    assert later["unit"] == "pr:7"  # a later round inherits its review's unit
    r = subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(a), "find",
                        "--unit", "pr:6"], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == old


def test_sync_if_idle_skips_busy_lock(world):
    import fcntl
    import time
    _, a, _, _ = world
    rn.open_review(a, "feature", "origin/main")
    lock = Path(sh(a, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "idh-review-sync.lock"
    with open(lock, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        t0 = time.monotonic()
        done = subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(a), "sync",
                               "--if-idle"], capture_output=True, text=True)
        elapsed = time.monotonic() - t0
    assert done.returncode == 0 and "skipped: lock busy" in done.stdout
    assert elapsed < 2


def test_push_for_landing_refuses_a_missing_review_head(world):
    """gaze on PR #1852: once notes are merge evidence, a landed review's head ref must exist."""
    _, a, _, _ = world
    rid = rn.open_review(str(a), "feature", "origin/main")
    rq = rn.entries(a, rid)[0]["request_id"]
    sh(a, "update-ref", "-d", f"{rn.HEADS}/{rid}/{rq}")
    with pytest.raises(rn.Refusal, match="missing"):
        rn.push_for_landing(str(a), "feature")


# --- ticket 1301: readers take the PR review's answers from notes, not from comments -------------

def test_answers_latest_matches_stale_head(world):
    """`answers` gives every answer's text (attribution's seat source) and, with --latest, the
    newest answer's result, seats and reviewed head: a poller sees the head it reviewed, so a
    branch that moved since is visibly stale."""
    _, a, _, _ = world
    rid = rn.open_review(a, "feature", "origin/main", unit="pr:7")
    head = sh(a, "rev-parse", "feature")
    rn.add(a, "answer", rid, {"run_id": "gz-1", "result": "FINDINGS", "seats": "self-only",
                              "coverage": {"scope": "full"}, "text": "result: FINDINGS\nseat: one"})
    rn.add(a, "answer", rid, {"run_id": "gz-2", "result": "REVIEWED", "seats": "panel",
                              "coverage": {"scope": "full"}, "text": "result: REVIEWED\nseat: two"})
    assert rn.answer_texts(a, rid) == ["result: FINDINGS\nseat: one", "result: REVIEWED\nseat: two"]
    latest = rn.latest_answer(a, rid)
    assert (latest["result"], latest["seats"], latest["reviewed_head_sha"]) == ("REVIEWED", "panel", head)
    sh(a, "switch", "-q", "feature")
    (a / "other.txt").write_text("moved\n")
    sh(a, "commit", "-qam", "moved on")
    moved = sh(a, "rev-parse", "HEAD")

    def cli(*args):
        return subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(a), "answers",
                               "--unit", "pr:7", *args], capture_output=True, text=True)
    r = cli("--latest", "--json", "--head", moved)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["review_id"] == rid and out["reviewed_head_sha"] == head and out["current"] is False
    assert json.loads(cli("--latest", "--json", "--head", head).stdout)["current"] is True
    texts = cli()
    assert texts.returncode == 0 and "seat: one" in texts.stdout and "seat: two" in texts.stdout
    none = subprocess.run([sys.executable, str(SCRIPTS / "review_notes.py"), "-C", str(a), "answers",
                           "--unit", "pr:8", "--latest"], capture_output=True, text=True)
    assert none.returncode == 1 and "no review" in none.stderr
