"""Ticket 1307: notes are the one attribution record. Writers record `writer` entries locally,
gaze answers carry the reviewer lines, and the block is assembled from notes for landing
(rendered into a PR body just before the merge) and for roar's capture, in both modes."""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import review_notes as rn  # noqa: E402

spec = importlib.util.spec_from_file_location("attribution_record", SCRIPTS / "attribution_record.py")
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)

WRITER = ("writer: step=execute · runtime=claude-code · model=anthropic/claude-opus-5-5 · effort=not-stated"
          " · route=opus · independence=not-stated")
PLANNER = WRITER.replace("step=execute", "step=plan")
REVIEWER = ("reviewer: step=review · seat=a · runtime=codex · model=openai/gpt-6-luna · effort=not-stated"
            " · route=headless · independence=not-stated · status: ran")
FINDING = "  finding: verifiable · scripts/x.py:3 · adopted: yes"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=child_env()).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A clone whose origin is unreachable: any network call would fail loudly."""
    work = tmp_path / "work"
    work.mkdir()
    git(work, "init", "-q", "-b", "main")
    git(work, "config", "user.email", "t@example.org")
    git(work, "config", "user.name", "T")
    (work / "a.txt").write_text("a\n")
    git(work, "add", "a.txt")
    git(work, "commit", "-qm", "base")
    git(work, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(work, "remote", "add", "origin", str(tmp_path / "unreachable.git"))
    git(work, "switch", "-qc", "feat")
    (work / "b.txt").write_text("b\n")
    git(work, "add", "b.txt")
    git(work, "commit", "-qm", "feat")
    monkeypatch.chdir(work)
    return work


@pytest.fixture
def offline(monkeypatch):
    """Every git call review_notes makes, recorded; a network verb fails the test."""
    calls = []
    real = rn._git

    def spy(cwd, *args, **kw):
        calls.append(args)
        assert args[0] not in ("fetch", "push", "ls-remote", "pull"), f"network call: git {args}"
        assert not (args[0] == "request-pull" and "unreachable" in " ".join(args)), f"network call: git {args}"
        return real(cwd, *args, **kw)

    monkeypatch.setattr(rn, "_git", spy)
    monkeypatch.setattr(ar.forge, "get_forge", lambda *a, **k: pytest.fail("forge call on the writer path"))
    return calls


def writers_of(repo, rid):
    return [e["line"] for e in rn.entries(str(repo), rid) if e["kind"] == "writer"]


@pytest.mark.parametrize("unit", ["pr:7", "branch:feat"])
def test_record_writer_is_local_both_modes(repo, offline, unit):
    rid = ar.record_writer(str(repo), WRITER, unit, branch="feat")
    assert writers_of(repo, rid) == [WRITER]
    if unit.startswith("pr:"):
        assert rn.find_unit(str(repo), unit) == rid
    else:
        assert rn.find(str(repo), "feat") == rid
    assert offline  # the spy saw git calls: a positive control for the network assertions


def test_record_writer_reuses_the_review_gaze_opened(repo, offline):
    rid = rn.open_review(str(repo), "feat", "origin/main", unit="pr:7", remote="")
    assert ar.record_writer(str(repo), PLANNER, "pr:7") == rid
    assert ar.record_writer(str(repo), WRITER, "pr:7") == rid
    assert writers_of(repo, rid) == [PLANNER, WRITER]


@pytest.mark.parametrize("line", ["writer: runtime=x · effort=y · model=bare", REVIEWER, "nonsense"])
def test_record_writer_refuses_a_malformed_line(repo, offline, line):
    with pytest.raises(ValueError):
        ar.record_writer(str(repo), line, "pr:7", branch="feat")
    assert rn.find_unit(str(repo), "pr:7") is None


def test_record_writer_cli_exit_codes(repo):
    run = [sys.executable, str(SCRIPTS / "attribution_record.py"), "--record-writer"]
    ok = subprocess.run([*run, WRITER, "--unit", "branch:feat"], cwd=repo, capture_output=True, text=True,
                        env=child_env())
    assert ok.returncode == 0, ok.stderr
    assert ok.stdout.strip().startswith("rv-")
    bad = subprocess.run([*run, "writer: nope", "--unit", "branch:feat"], cwd=repo, capture_output=True,
                         text=True, env=child_env())
    assert bad.returncode == 1 and "attribution-record" in bad.stderr


def gazed(repo, unit, attribution=(REVIEWER, FINDING)):
    """A review with writer lines and one gaze answer carrying the reviewer lines."""
    rid = ar.record_writer(str(repo), PLANNER, unit, branch="feat")
    ar.record_writer(str(repo), WRITER, unit, branch="feat")
    rn.add(str(repo), "answer", rid, {"run_id": "gz-1", "result": "REVIEWED", "seats": "panel",
                                      "coverage": {"scope": "full"}, "attribution": list(attribution),
                                      "text": "result: REVIEWED\n"})
    return rid


@pytest.mark.parametrize("unit,pr_line", [("pr:7", "pr: 7 · merged pending · project: work"),
                                          ("branch:feat", "pr: branch:feat · merged pending · project: work")])
def test_block_from_notes_parses_strict(repo, unit, pr_line):
    gazed(repo, unit)
    text, status = ar.notes_block(str(repo), unit, "work")
    assert status == "ok"
    assert text.splitlines() == ["kind: review-attribution", pr_line, PLANNER, WRITER, REVIEWER, FINDING]
    record = ar.parse_record(text, strict=True)
    assert record["writer"]["step"] == "execute" and record["reviewers"][0]["seat"] == "a"


def test_block_from_notes_keeps_the_latest_writer_per_step_and_every_attempt(repo):
    rid = gazed(repo, "pr:7")
    later = WRITER.replace("route=opus", "route=sonnet")
    ar.record_writer(str(repo), later, "pr:7")
    rn.add(str(repo), "answer", rid, {"run_id": "gz-2", "result": "REVIEWED", "seats": "panel",
                                      "coverage": {"scope": "full"}, "attribution": [REVIEWER], "text": "x"})
    text, status = ar.notes_block(str(repo), "pr:7", "work")
    assert status == "ok", status
    lines = text.splitlines()
    assert later in lines and WRITER not in lines
    assert lines.count(REVIEWER) == 2  # one line per review attempt, as the body carried them


def test_block_from_notes_missing_and_invalid(repo):
    assert ar.notes_block(str(repo), "pr:7", "work") == (None, "missing")
    ar.record_writer(str(repo), WRITER, "pr:7", branch="feat")  # a writer, no gaze answer yet
    text, status = ar.notes_block(str(repo), "pr:7", "work")
    assert text is None and status.startswith("invalid: ")


def test_put_block_replaces_or_creates_the_single_block():
    record = "kind: review-attribution\npr: 7 · merged pending · project: work\n" + WRITER + "\n" + REVIEWER + "\n"
    body = "Summary\n\n**Ticket:** tickets/1307-x.erg\n\n```attribution\nkind: review-attribution\nstale\n```\ntail\n"
    out = ar.put_block(body, record)
    assert "stale" not in out and "tail" in out and "**Ticket:** tickets/1307-x.erg" in out
    assert ar.parse_pr_body(out)["reviewers"][0]["seat"] == "a"
    fresh = ar.put_block("Summary only\n", record)
    assert fresh.startswith("Summary only\n") and ar.parse_pr_body(fresh)["pr"] == 7
    with pytest.raises(ValueError):
        ar.put_block("```attribution\nopen forever\n", record)


@pytest.mark.parametrize("unit,slug", [("pr:7", "review-attribution-pr7"),
                                       ("branch:feat", "review-attribution-branch-feat")])
def test_capture_unit_from_notes(repo, monkeypatch, unit, slug):
    gazed(repo, unit)
    captured = {}
    monkeypatch.setattr(ar, "merged_date", lambda cwd, u: "2026-10-28")
    monkeypatch.setattr(ar, "capture_record",
                        lambda text, record, repository, audience: captured.update(
                            text=text, record=record, slug=ar.capture_slug(record)) or "captured")
    args = argparse.Namespace(capture_unit=unit, capture=repo, audience="public", project="work")
    assert ar.capture_unit(args) == 0
    assert "merged 2026-10-28" in captured["text"] and "pending" not in captured["text"]
    assert captured["slug"] == slug
    assert captured["record"]["reviewers"][0]["findings"][0]["anchor"] == "scripts/x.py:3"


def test_capture_unit_refuses_an_unmerged_unit(repo, monkeypatch):
    gazed(repo, "pr:7")
    monkeypatch.setattr(ar, "merged_date", lambda cwd, u: None)
    args = argparse.Namespace(capture_unit="pr:7", capture=repo, audience="public", project="work")
    with pytest.raises(ValueError, match="not merged"):
        ar.capture_unit(args)


def test_capture_unit_for_a_branch_deleted_by_cleanup(repo, monkeypatch):
    """Gaze finding on PR #1874: raid_land --cleanup deletes the merged branch; the merge date
    comes from the review's retained head and the landing merge, not from the branch."""
    gazed(repo, "branch:feat")
    git(repo, "switch", "-q", "main")
    git(repo, "-c", "core.hooksPath=/dev/null", "merge", "-q", "--no-ff", "-m", "land feat", "feat")
    git(repo, "branch", "-d", "feat")
    landed = git(repo, "show", "-s", "--format=%cs", "HEAD")
    captured = {}
    monkeypatch.setattr(ar, "capture_record",
                        lambda text, record, repository, audience: captured.update(text=text) or "captured")
    args = argparse.Namespace(capture_unit="branch:feat", capture=repo, audience="public", project="work")
    assert ar.capture_unit(args) == 0
    assert f"pr: branch:feat · merged {landed} · project: work" in captured["text"]


def test_branch_unit_not_landed_has_no_merge_date(repo):
    gazed(repo, "branch:feat")
    assert ar.merged_date(str(repo), "branch:feat") is None


def test_capture_unit_for_a_rebased_landing(repo, monkeypatch):
    """Gaze round 2 on PR #1874: the gate admits a rebased head H' by patch-id with no new
    request; raid_land merges H'. The reviewed head H never lands, yet the merge is found by
    the patch-id of its second parent's range, after the branch is deleted."""
    gazed(repo, "branch:feat")
    reviewed = git(repo, "rev-parse", "feat")
    git(repo, "switch", "-q", "main")
    (repo / "c.txt").write_text("c\n")
    git(repo, "add", "c.txt")
    git(repo, "commit", "-qm", "main moved")
    git(repo, "rebase", "-q", "main", "feat")
    assert git(repo, "rev-parse", "feat") != reviewed
    git(repo, "switch", "-q", "main")
    git(repo, "-c", "core.hooksPath=/dev/null", "merge", "-q", "--no-ff", "-m", "land feat", "feat")
    git(repo, "branch", "-D", "feat")
    landed = git(repo, "show", "-s", "--format=%cs", "HEAD")
    assert ar.merged_date(str(repo), "branch:feat") == landed
