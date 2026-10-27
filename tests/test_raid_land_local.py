"""Ticket 1275: raid_land.py lands a branch with no forge (design D3 of 1252), under the real
main-update guard in enforce mode, on temp repositories only."""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("raid_land_local", SCRIPTS / "raid_land.py")
assert spec and spec.loader
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)
import forge  # noqa: E402


def env():
    e = {k: v for k, v in child_env().items() if not k.startswith("GIT_")}
    e.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", LC_ALL="C",
             GIT_AUTHOR_NAME="F", GIT_AUTHOR_EMAIL="f@example.invalid",
             GIT_COMMITTER_NAME="F", GIT_COMMITTER_EMAIL="f@example.invalid")
    return e


def git(cwd, *args, check=True):
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env())
    if check and p.returncode != 0:
        raise AssertionError(f"git {args}: {p.stderr}")
    return p.stdout.strip()


def make_repo(tmp_path, monkeypatch, remote: bool, check_argv=("true",)):
    """work: main checked out, hook enforcing; wt: linked worktree on branch feat with one commit."""
    for k, v in env().items():
        monkeypatch.setenv(k, v)
    for k in [k for k in os.environ if k.startswith("GIT_") and k not in env()]:
        monkeypatch.delenv(k)
    monkeypatch.setenv("PATH", os.environ["PATH"].replace(str(Path.home() / ".local/bin"), ""))
    work = tmp_path / "work"
    git(tmp_path, "init", "-q", "-b", "main", str(work))
    (work / "hooks").mkdir()
    shutil.copy2(ROOT / "hooks" / "reference-transaction", work / "hooks" / "reference-transaction")
    (work / "scripts").mkdir()
    shutil.copy2(SCRIPTS / "merge-gate.py", work / "scripts" / "merge-gate.py")
    (work / ".merge-gate.json").write_text(
        '{"gate":"on","scope":"t","checks":[{"name":"c","argv":%s}]}' % str(list(check_argv)).replace("'", '"'))
    (work / "a.txt").write_text("a\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "base")
    origin = tmp_path / "origin.git"
    if remote:
        git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
        git(work, "remote", "add", "origin", str(origin))
        git(work, "push", "-q", "origin", "main")
    git(work, "config", "core.hooksPath", "hooks")
    git(work, "config", "idh.mainGuard", "enforce")
    git(work, "config", "idh.afterMerge", "off")
    wt = tmp_path / "wt"
    git(work, "worktree", "add", "-q", "-b", "feat", str(wt), "main")
    (wt / "b.txt").write_text("b\n")
    git(wt, "add", "b.txt")
    git(wt, "commit", "-qm", "feat")
    return work, wt, origin


def land(wt, ruled=None, claims=(), out=None):
    out = [] if out is None else out
    fg = forge.NoneForge(str(wt))
    code = rl.land(fg, "branch:feat base=main", ruled or git(wt, "rev-parse", "HEAD"), "main", wt,
                   out=out.append, ruled_claims=list(claims))
    return code, out


def test_gated_merge_with_no_remote_lands_pinned_and_reads_back(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    tip = git(wt, "rev-parse", "HEAD")
    code, out = land(wt)
    assert code == 0, out
    assert git(work, "rev-parse", "main^2") == tip
    assert (work / "b.txt").exists()  # the checked-out main followed the ref
    assert git(work, "status", "--porcelain") == ""
    assert git(work, "rev-parse", "refs/notes/gate")  # the record is where the guard reads it
    assert any(line.startswith("no remote:") for line in out)
    back = forge.NoneForge(str(wt))
    assert back.read_back("branch:feat base=main") == f"MERGED {tip} -"
    assert back.merged_at("branch:feat base=main")


def test_gated_merge_pushes_main_to_the_remote(tmp_path, monkeypatch):
    work, wt, origin = make_repo(tmp_path, monkeypatch, remote=True)
    tip = git(wt, "rev-parse", "HEAD")
    code, out = land(wt)
    assert code == 0, out
    assert git(origin, "rev-parse", "main^2") == tip
    assert git(origin, "rev-parse", "main") == git(work, "rev-parse", "main")


def test_main_not_checked_out_moves_by_compare_and_swap(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    git(work, "switch", "-q", "--detach")
    tip = git(wt, "rev-parse", "HEAD")
    code, out = land(wt)
    assert code == 0, out
    assert git(work, "rev-parse", "main^2") == tip


def test_failing_gate_check_refuses_and_main_stays(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False, check_argv=("false",))
    before = git(work, "rev-parse", "main")
    with pytest.raises(rl.Refusal):
        land(wt)
    assert git(work, "rev-parse", "main") == before


def test_merge_without_a_gate_record_is_refused_by_the_guard(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    before = git(work, "rev-parse", "main")
    fg = forge.NoneForge(str(wt))
    with pytest.raises(forge.MergeRefused):
        fg.merge("branch:feat base=main", git(wt, "rev-parse", "HEAD"), auto=False)
    assert git(work, "rev-parse", "main") == before
    assert fg.read_back("branch:feat base=main").startswith("OPEN ")


def test_merge_is_pinned_to_the_head_oid(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    old_tip = git(wt, "rev-parse", "HEAD")
    (wt / "c.txt").write_text("c\n")
    git(wt, "add", "c.txt")
    git(wt, "commit", "-qm", "more")
    with pytest.raises(forge.MergeRefused, match="pinned"):
        forge.NoneForge(str(wt)).merge("branch:feat base=main", old_tip, auto=False)


def test_head_beyond_the_ruled_tip_refuses(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    ruled = git(wt, "rev-parse", "HEAD")
    (wt / "c.py").write_text("print(1)\n")
    git(wt, "add", "c.py")
    git(wt, "commit", "-qm", "unreviewed code")
    before = git(work, "rev-parse", "main")
    with pytest.raises(rl.Refusal, match="more than bookkeeping"):
        land(wt, ruled=ruled)
    assert git(work, "rev-parse", "main") == before


def test_claimed_ticket_must_be_closed_on_the_branch(tmp_path, monkeypatch):
    work, wt, _ = make_repo(tmp_path, monkeypatch, remote=False)
    (wt / "tickets").mkdir()
    (wt / "tickets" / "1275-x.erg").write_text("%erg 0.1\nTitle: x\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "work\n\nTicket: tickets/1275-x.erg")
    ruled = git(wt, "rev-parse", "HEAD")
    before = git(work, "rev-parse", "main")
    with pytest.raises(rl.Refusal, match="not closed on the branch"):
        land(wt, ruled=ruled, claims=["1275"])
    assert git(work, "rev-parse", "main") == before


def test_local_base_behind_origin_refuses(tmp_path, monkeypatch):
    work, wt, origin = make_repo(tmp_path, monkeypatch, remote=True)
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(origin), str(other))
    (other / "z").write_text("z\n")
    git(other, "add", "z")
    git(other, "commit", "-qm", "elsewhere")
    git(other, "push", "-q", "origin", "main")
    with pytest.raises(rl.Refusal, match="differs from origin"):
        land(wt)


def test_local_base_ahead_of_origin_refuses(tmp_path, monkeypatch):
    work, wt, origin = make_repo(tmp_path, monkeypatch, remote=True)
    git(work, "config", "idh.mainGuard", "off")
    (work / "unreviewed").write_text("u\n")
    git(work, "add", "unreviewed")
    git(work, "commit", "-qm", "unpushed local main")
    git(work, "config", "idh.mainGuard", "enforce")
    before = git(origin, "rev-parse", "main")
    with pytest.raises(rl.Refusal, match="differs from origin"):
        land(wt)
    assert git(origin, "rev-parse", "main") == before


def test_failed_push_after_the_move_is_exit_6_not_a_remerge(tmp_path, monkeypatch):
    work, wt, origin = make_repo(tmp_path, monkeypatch, remote=True)
    hook = origin / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nwhile read o n r; do [ \"$r\" = refs/heads/main ] && exit 1; done\nexit 0\n")
    hook.chmod(0o755)
    tip = git(wt, "rev-parse", "HEAD")
    out = []
    code = rl.main_land(forge.NoneForge(str(wt)), "branch:feat base=main", tip, [], "main", wt, out.append)
    assert code == rl.UNKNOWN
    assert any("push failed" in line for line in out)
    assert git(work, "rev-parse", "main^2") == tip  # moved locally, reported, never re-merged


def test_remote_base_deleted_refuses_and_is_not_recreated(tmp_path, monkeypatch):
    work, wt, origin = make_repo(tmp_path, monkeypatch, remote=True)
    git(work, "push", "-q", "origin", "main:spare")
    git(origin, "update-ref", "-d", "refs/heads/main")  # a plain fetch does not prune the cached origin/main
    with pytest.raises(rl.Refusal, match="cannot read origin/main"):
        land(wt)
    assert git(origin, "rev-parse", "--verify", "-q", "refs/heads/main", check=False) == ""


def test_cli_with_origin_and_no_gh_refuses_cleanly(tmp_path, monkeypatch, capsys):
    work, wt, origin = make_repo(tmp_path, monkeypatch, remote=True)
    bindir = tmp_path / "nogh"
    bindir.mkdir()
    (bindir / "git").symlink_to(shutil.which("git"))
    monkeypatch.setenv("PATH", str(bindir))
    monkeypatch.chdir(work)
    assert rl.main(["7", "--ruled-head", "-", "--ruled-claims", "-"]) == rl.REFUSED
    assert "origin remote and gh is not available" in capsys.readouterr().err
