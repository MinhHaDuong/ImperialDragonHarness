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
    assert fetch.count("+refs/notes/review:refs/notes/origin/review") == 1
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
