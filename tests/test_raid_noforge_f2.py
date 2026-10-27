"""Ticket 1276: raid Phases 6-7 end to end on the no-forge route (flow F2 of
conception/2026-10-27-review-merge-flows.md): review on notes, verify-gate verdict on notes, local
gated merge by raid_land.py under the main-update guard in enforce mode. Temp repositories only, `gh`
absent from PATH. The two LLM steps (gaze, verify-gate) are stood in for by the `answer` and `verdict`
entries they write through review_notes.py; the helpers around them are the real ones."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_raid_land_local import git, make_repo, rl

pytestmark = pytest.mark.integration

NOTES = Path(__file__).resolve().parents[1] / "scripts" / "review_notes.py"


def no_gh(tmp_path, monkeypatch):
    """PATH holds git and the gate's check alone: no gh."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    tools = ("git", "python3", "ps", "true", "tr", "cat", "sed", "grep", "awk", "env", "date", "uname",
             "dirname", "basename", "mktemp", "rm", "head", "sort", "wc", "cut", "id", "hostname")
    for tool in tools:  # the gate's check and what the main-update guard hook calls
        if shutil.which(tool):
            (bindir / tool).symlink_to(shutil.which(tool))
    monkeypatch.setenv("PATH", str(bindir))
    assert shutil.which("gh") is None


def notes(cwd, *args, check=True):
    p = subprocess.run([sys.executable, str(NOTES), "-C", str(cwd), *args], capture_output=True,
                       text=True, env=os.environ)
    if check and p.returncode != 0:
        raise AssertionError(f"review_notes {args}: {p.stderr}")
    return p


def answer(wt, rid, head):
    fields = {"run_id": "gz-e2e", "result": "REVIEWED", "seats": "panel",
              "coverage": {"scope": "full"}, "text": "result: REVIEWED"}
    return notes(wt, "add", "answer", "--review", rid, "--head", head, "--json", json.dumps(fields))


def test_gaze_gate_merge_chain_without_a_forge(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    no_gh(tmp_path, monkeypatch)
    rid = notes(wt, "open", "--branch", "feat", "--base-ref", "main", "--why", "e2e",
                "--intent", "verify the chain").stdout.split()[0]
    assert notes(wt, "find", "feat").stdout.split() == [rid]  # gaze resolves branch:feat this way

    # no gaze answer yet: the gate refuses
    assert notes(wt, "gate", rid, "HEAD", check=False).returncode == 1

    reviewed = git(wt, "rev-parse", "HEAD")
    answer(wt, rid, reviewed)

    # main moves, the branch is rebased between gaze and gate: same patch, admitted (spec §8)
    git(work, "config", "idh.mainGuard", "off")
    (work / "other.txt").write_text("o\n")
    git(work, "add", "other.txt")
    git(work, "commit", "-qm", "main moves elsewhere")
    git(work, "config", "idh.mainGuard", "enforce")
    git(wt, "rebase", "-q", "main")
    tip = git(wt, "rev-parse", "HEAD")
    assert tip != reviewed
    state = json.loads(notes(wt, "gate", rid, "HEAD").stdout)
    assert state["ready"] and state["round"] == 1

    notes(wt, "verdict", "--review", rid, "--session", "00000000-0000-4000-8000-000000000001",
          "--verdict", "APPROVED", "--head", tip)

    before = git(work, "rev-parse", "main")
    monkeypatch.chdir(wt)
    assert rl.main(["branch:feat", "--ruled-head", tip, "--ruled-claims", "-"]) == rl.OK
    assert git(work, "rev-parse", "main^1") == before and git(work, "rev-parse", "main^2") == tip
    assert git(work, "status", "--porcelain") == ""
    assert git(work, "rev-parse", "refs/notes/gate")


def test_origin_without_gh_refuses_and_main_stays(tmp_path, monkeypatch, capsys):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    git(work, "remote", "add", "origin", str(tmp_path / "unreachable"))  # present, never contacted
    no_gh(tmp_path, monkeypatch)
    tip = git(wt, "rev-parse", "HEAD")
    before = git(work, "rev-parse", "main")
    monkeypatch.chdir(wt)
    assert rl.main(["branch:feat", "--ruled-head", tip, "--ruled-claims", "-"]) == rl.REFUSED
    assert "origin remote and gh is not available" in capsys.readouterr().err
    assert git(work, "rev-parse", "main") == before
    assert git(work, "rev-parse", "--verify", "-q", "refs/notes/gate", check=False) == ""


def test_two_concurrent_appends_to_one_review_both_survive(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    no_gh(tmp_path, monkeypatch)
    rid = notes(wt, "open", "--branch", "feat", "--base-ref", "main").stdout.split()[0]
    # spec §8: both entries must survive
    procs = [subprocess.Popen([sys.executable, str(NOTES), "-C", str(wt), "add", "plan", "--review", rid,
                               "--json", json.dumps({"text": f"seat {i}"})], env=os.environ,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(8)]
    assert [p.wait() for p in procs] == [0] * 8
    shown = notes(wt, "show", rid).stdout
    assert all(f"seat {i}" in shown for i in range(8))

