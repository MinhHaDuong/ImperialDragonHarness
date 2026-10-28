"""Ticket 1271: scripts/forge.py, the gh and none backends, with gh absent and with a stub gh."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("forge", SCRIPTS / "forge.py")
assert spec and spec.loader
forge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(forge)

pytestmark = pytest.mark.integration

HEAD = "a" * 40
STUB = """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
log = os.environ["STUB_LOG"]
open(log, "a").write(json.dumps(args) + "\\n")
state = json.load(open(os.environ["STUB_STATE"]))
if args[:2] == ["pr", "view"]:
    fields = args[args.index("--json") + 1]
    if "-q" in args:
        if "autoMergeRequest != null" in args[-1]:
            print("true" if state.get("armed") else "false")
        else:
            print("OPEN " + state["head"] + " -")
    elif fields == "body":
        print(json.dumps({"body": state["body"]}))
    elif fields == "comments,reviews":
        print(json.dumps({"comments": [{"body": "c"}], "reviews": [{"body": "r"}]}))
    elif fields == "statusCheckRollup":
        print(json.dumps({"statusCheckRollup": state["rollup"]}))
    else:
        print(json.dumps({"number": 7, "state": "OPEN", "isDraft": True, "mergeable": "MERGEABLE",
                          "headRefName": "t1-x", "baseRefName": "main", "headRefOid": state["head"],
                          "body": state["body"]}))
elif args[:2] == ["api", "repos/{owner}/{repo}/pulls/7"]:
    state["body"] = json.loads(sys.stdin.read())["body"]
    json.dump(state, open(os.environ["STUB_STATE"], "w"))
elif args[:2] == ["pr", "merge"] and state.get("refuse"):
    print("not mergeable", file=sys.stderr)
    sys.exit(1)
elif args[:2] == ["pr", "create"]:
    print("https://github.com/o/r/pull/42")
"""


@pytest.fixture
def stub(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "gh").write_text(STUB)
    (bindir / "gh").chmod(0o755)
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"head": HEAD, "body": "x\n**Ticket:** tickets/1271-a.erg\n", "rollup": []}))
    monkeypatch.setenv("STUB_LOG", str(tmp_path / "log"))
    monkeypatch.setenv("STUB_STATE", str(state))
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    # a repository of its own: the offline cache (ticket 1308) never lands in the enclosing checkout,
    # even when TMPDIR sits inside one
    subprocess.run(["git", "init", "-q", str(tmp_path / "cwd")], check=True)
    monkeypatch.chdir(tmp_path / "cwd")
    return state


@pytest.fixture
def nogh(tmp_path, monkeypatch):
    """PATH holding git and nothing else: gh is absent."""
    bindir = tmp_path / "nogh"
    bindir.mkdir()
    (bindir / "git").symlink_to(shutil.which("git"))
    monkeypatch.setenv("PATH", str(bindir))
    assert shutil.which("gh") is None


def sh(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    sh(r, "init", "-q", "-b", "main")
    sh(r, "config", "user.email", "t@t")
    sh(r, "config", "user.name", "t")
    (r / "f").write_text("1\n")
    sh(r, "add", "f")
    sh(r, "commit", "-q", "-m", "base")
    sh(r, "switch", "-q", "-c", "t1-x")
    (r / "g").write_text("2\n")
    sh(r, "add", "g")
    sh(r, "commit", "-q", "-m", "work\n\nTicket: tickets/1271-forge.erg")
    sh(r, "switch", "-q", "main")
    return r


def test_gh_resolve_record(stub):
    rec = forge.get_forge("gh").resolve("7")
    assert rec == {"id": "7", "branch": "t1-x", "base": "main", "head": HEAD, "state": "OPEN",
                   "mergeable": "MERGEABLE", "draft": True, "body": rec["body"], "claims": ["1271"],
                   "forge": "read"}


def test_gh_comments_checks_comment_and_ops(stub, tmp_path):
    f = forge.get_forge("gh")
    assert [c["body"] for c in f.comments("7")] == ["c", "r"]
    assert f.checks("7") == "none"
    stub.write_text(json.dumps({"head": HEAD, "body": "", "rollup": [{"name": "ci", "conclusion": "FAILURE"}]}))
    assert f.checks("7") == "failing: ci"
    stub.write_text(json.dumps({"head": HEAD, "body": "", "rollup": [{"name": "ci", "conclusion": "SUCCESS"}]}))
    assert f.checks("7") == "passing"
    assert f.auto_merge_armed("7") is False
    assert f.read_back("7") == f"OPEN {HEAD} -"
    assert f.create("b", "main", "t", "body") == "42"
    f.comment("7", "hello")
    f.ready("7")
    f.disarm("7")
    f.merge("7", HEAD, auto=False)
    log = [json.loads(line) for line in (tmp_path / "log").read_text().splitlines()]
    assert ["pr", "merge", "7", "--merge", "--match-head-commit", HEAD] in log
    assert ["pr", "comment", "7", "--body", "hello"] in log


def test_gh_merge_refusal_is_typed(stub):
    stub.write_text(json.dumps({"head": HEAD, "body": "", "refuse": True}))
    with pytest.raises(forge.MergeRefused, match="not mergeable"):
        forge.get_forge("gh").merge("7", HEAD, auto=True)


def test_gh_append_body_line_reads_back(stub):
    f = forge.get_forge("gh")
    f.append_body_line("7", "Reviewer: x")
    assert "Reviewer: x" in json.loads(stub.read_text())["body"].splitlines()
    f.append_body_line("7", "Reviewer: x")  # idempotent
    assert json.loads(stub.read_text())["body"].count("Reviewer: x") == 1


def test_gh_absent_is_a_typed_refusal(nogh):
    with pytest.raises(forge.ForgeRefusal, match="gh unavailable"):
        forge.GhForge().resolve("7")


def test_auto_reviewing_picks_by_ref(stub, nogh):
    assert isinstance(forge.get_forge("auto", "branch:t1-x"), forge.NoneForge)
    assert isinstance(forge.get_forge("auto", "7"), forge.NoneForge)  # gh absent
    with pytest.raises(forge.ForgeRefusal):
        forge.get_forge("bogus", "7")


def test_idh_forge_env_is_ignored(stub, monkeypatch):
    monkeypatch.setenv("IDH_FORGE", "none")
    assert isinstance(forge.get_forge(None, "7"), forge.GhForge)


def test_auto_takes_gh_for_a_number_when_present(stub):
    assert isinstance(forge.get_forge("auto", "7"), forge.GhForge)
    assert isinstance(forge.get_forge("auto", "branch:t1-x"), forge.NoneForge)


def test_landing_with_origin_never_local(repo, stub):
    sh(repo, "remote", "add", "origin", str(repo))
    assert isinstance(forge.get_forge(None, "7", cwd=str(repo), landing=True), forge.GhForge)
    with pytest.raises(forge.ForgeRefusal, match="origin"):
        forge.get_forge(None, "branch:t1-x", cwd=str(repo), landing=True)


def test_landing_with_origin_without_gh_refuses_naming_cause(repo, nogh):
    sh(repo, "remote", "add", "origin", str(repo))
    for ref in ("7", "branch:t1-x"):
        with pytest.raises(forge.ForgeRefusal, match="origin remote and gh is not available"):
            forge.get_forge(None, ref, cwd=str(repo), landing=True)


def test_landing_without_origin_is_the_local_merge(repo, nogh, stub):
    assert isinstance(forge.get_forge(None, "branch:t1-x", cwd=str(repo), landing=True), forge.NoneForge)


def test_reviewing_with_origin_is_unchanged(repo, nogh):
    sh(repo, "remote", "add", "origin", str(repo))
    assert isinstance(forge.get_forge(None, "branch:t1-x", cwd=str(repo)), forge.NoneForge)


def test_none_resolve_from_git_only(repo, nogh):
    f = forge.get_forge("none", cwd=str(repo))
    rec = f.resolve("branch:t1-x base=main")
    assert rec["head"] == sh(repo, "rev-parse", "t1-x")
    assert (rec["branch"], rec["base"], rec["state"], rec["mergeable"]) == ("t1-x", "main", "OPEN", "MERGEABLE")
    assert rec["claims"] == ["1271"]
    assert rec["id"] == "branch:t1-x"
    assert f.resolve("branch:main base=main")["state"] == "MERGED"
    assert f.resolve("branch:t1-x")["base"] == "main"  # no origin/main: falls back


def test_none_conflict_and_bad_refs(repo, nogh):
    sh(repo, "switch", "-q", "t1-x")
    (repo / "f").write_text("branch\n")
    sh(repo, "commit", "-qam", "edit f")
    sh(repo, "switch", "-q", "main")
    (repo / "f").write_text("main\n")
    sh(repo, "commit", "-qam", "edit f on main")
    f = forge.get_forge("none", cwd=str(repo))
    assert f.resolve("branch:t1-x base=main")["mergeable"] == "CONFLICTING"
    with pytest.raises(forge.ForgeRefusal):
        f.resolve("7")
    with pytest.raises(forge.ForgeRefusal):
        f.resolve("branch:nope base=main")


def test_none_noops_are_typed_and_unresolvable_merge_refuses(repo, nogh):
    f = forge.get_forge("none", cwd=str(repo))
    for result in (f.comment("x", "b"), f.append_body_line("x", "l"), f.ready("x"), f.disarm("x")):
        assert result is forge.NOOP and not result
    assert f.comments("x") == [] and f.checks("x") == "none" and f.auto_merge_armed("x") is False
    with pytest.raises(forge.ForgeRefusal):  # an unresolvable unit refuses, never reads back "merged"
        f.merge("x", HEAD, auto=False)
    with pytest.raises(forge.ForgeRefusal):
        f.read_back("x")


def test_cli_resolve_none(repo, nogh):
    done = subprocess.run([sys.executable, str(SCRIPTS / "forge.py"), "--forge", "none", "resolve",
                           "branch:t1-x base=main"], cwd=repo, capture_output=True, text=True,
                          env={"PATH": os.environ["PATH"]})
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["branch"] == "t1-x"
    bad = subprocess.run([sys.executable, str(SCRIPTS / "forge.py"), "--forge", "none", "resolve", "7"],
                         cwd=repo, capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
    assert bad.returncode == 1 and "forge:" in bad.stderr


def test_gh_checks_pending_is_not_passing(stub):
    f = forge.get_forge("gh")
    for status in ("IN_PROGRESS", "QUEUED", "PENDING"):
        stub.write_text(json.dumps({"head": HEAD, "body": "", "rollup": [
            {"name": "a", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "b", "status": status, "conclusion": ""}]}))
        assert f.checks("7") == "pending"


@pytest.mark.parametrize("body", ["Ticket: tickets/12-x", "Ticket: nonsense", "```\nTicket: tickets/1271-x\n"])
def test_parse_claims_malformed_is_a_stop(body):
    with pytest.raises(forge.ForgeRefusal):
        forge.parse_claims(body)


def test_parse_claims_none_is_not_malformed():
    assert forge.parse_claims("Ticket: none\nTicket: tickets/1271-x") == ["1271"]


def test_resolve_reports_a_malformed_claim_without_raising(stub):
    """Ticket 1272: each caller keeps its own order of refusals; parse_claims stays the one parser."""
    stub.write_text(json.dumps({"head": HEAD, "body": "Ticket: tickets/oops\n", "rollup": []}))
    rec = forge.get_forge("gh").resolve("7")
    assert rec["claims"] == [] and "canonical" in rec["claims_error"]


def test_append_body_line_edit_runs_every_attempt(stub):
    f = forge.get_forge("gh")
    f.append_body_line("7", "L1", edit=lambda body: body + "L1\n")
    f.append_body_line("7", "L1", edit=lambda body: body + "L1\n")  # the caller's edit decides: no skip
    assert json.loads(stub.read_text())["body"].count("L1") == 2


def test_comment_is_lenient_unless_strict(monkeypatch):
    f = forge.GhForge()
    monkeypatch.setattr(f, "_gh", lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "502"))
    f.comment("7", "x")
    with pytest.raises(forge.ForgeRefusal, match="502"):
        f.comment("7", "x", strict=True)


def test_merged_at_and_cwd(tmp_path, monkeypatch):
    seen = {}

    def run(cmd, **kw):
        seen.update(kw)
        return subprocess.CompletedProcess(cmd, 0, json.dumps({"mergedAt": "2026-10-27T21:04:00Z"}), "")

    monkeypatch.setattr(forge.subprocess, "run", run)
    f = forge.get_forge("gh", cwd=str(tmp_path))
    assert f.merged_at("7") == "2026-10-27T21:04:00Z" and seen["cwd"] == str(tmp_path)


def test_append_body_line_refuses_when_the_patch_fails(monkeypatch):
    f = forge.GhForge()

    def gh(*args, stdin=None, read=False):
        if args[0] == "api":
            return subprocess.CompletedProcess(args, 1, "", "HTTP 403")
        return subprocess.CompletedProcess(args, 0, json.dumps({"body": ""}), "")

    monkeypatch.setattr(f, "_gh", gh)
    with pytest.raises(forge.ForgeRefusal, match="403"):
        f.append_body_line("7", "L")


def test_comments_can_leave_reviews_out(stub):
    assert [c["body"] for c in forge.get_forge("gh").comments("7", reviews=False)] == []


def test_landing_without_origin_numeric_ref_is_local_even_with_gh(repo, stub):
    assert isinstance(forge.get_forge(None, "7", cwd=str(repo), landing=True), forge.NoneForge)
