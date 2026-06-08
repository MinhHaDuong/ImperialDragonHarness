"""Tests for scripts/project-state.py — the per-collector parsers.

Each collector shells out via the module-level `run()`. We patch `run` with a
fake that returns canned CompletedProcess objects, so these tests pin the
parsing of git/gh porcelain output without touching a real repo.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))  # project-state imports git_utils
spec = importlib.util.spec_from_file_location(
    "project_state", SCRIPTS / "project-state.py"
)
ps = importlib.util.module_from_spec(spec)
sys.modules["project_state"] = ps
spec.loader.exec_module(ps)


def _cp(stdout="", returncode=0, stderr=""):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _patch_run(monkeypatch, responder):
    """responder(args) -> CompletedProcess; args is the command list."""
    monkeypatch.setattr(ps, "run", lambda args, cwd: responder(args))


# ── git_state ────────────────────────────────────────────────────────────────


def test_git_state_clean_repo(monkeypatch):
    def responder(args):
        if args[:2] == ["git", "rev-parse"]:
            return _cp("main\n")
        if args[:2] == ["git", "status"]:
            return _cp("")  # clean
        if "rev-list" in args and "--left-right" in args:
            return _cp("2\t1\n")
        if args[:2] == ["git", "log"]:
            return _cp("")
        return _cp("", 1)

    monkeypatch.setattr(ps, "time", ps.time)  # leave time as-is
    _patch_run(monkeypatch, responder)
    out = ps.git_state(Path("/proj"))
    assert out["branch"] == "main"
    assert out["clean"] is True
    assert out["dirty_files"] == []
    assert out["ahead"] == 2
    assert out["behind"] == 1


def test_git_state_dirty_repo(monkeypatch):
    def responder(args):
        if args[:2] == ["git", "rev-parse"]:
            return _cp("feature\n")
        if args[:2] == ["git", "status"]:
            return _cp(" M a.py\n?? b.txt\n")
        if "rev-list" in args:
            return _cp("0\t0\n")
        return _cp("")

    _patch_run(monkeypatch, responder)
    out = ps.git_state(Path("/proj"))
    assert out["clean"] is False
    assert out["dirty_files"] == ["M a.py", "?? b.txt"]


# ── worktree_state ───────────────────────────────────────────────────────────


def test_worktree_state_parses_porcelain(monkeypatch):
    porcelain = (
        "worktree /home/u/repo\nHEAD abcdef1234567890\nbranch refs/heads/main\n\n"
        "worktree /home/u/repo/.worktrees/t1\nHEAD 1122334455667788\n"
        "branch refs/heads/feature\nlocked busy\n\n"
        "worktree /home/u/repo/.worktrees/det\nHEAD 99887766\ndetached\n\n"
    )
    _patch_run(monkeypatch, lambda args: _cp(porcelain))
    wts = ps.worktree_state(Path("/proj"))
    assert wts[0]["path"] == "/home/u/repo"
    assert wts[0]["head"] == "abcdef12"  # truncated to 8
    assert wts[0]["branch"] == "main"
    assert wts[1]["locked"] is True
    assert wts[1]["lock_reason"] == "busy"
    assert wts[2]["branch"] is None  # detached


def test_worktree_state_returns_empty_on_error(monkeypatch):
    _patch_run(monkeypatch, lambda args: _cp("", 1))
    assert ps.worktree_state(Path("/proj")) == []


# ── pr_state ─────────────────────────────────────────────────────────────────


def test_pr_state_parses_gh_json(monkeypatch):
    payload = '[{"number": 7, "title": "Fix", "headRefName": "claude/fix"}]'
    _patch_run(monkeypatch, lambda args: _cp(payload))
    out = ps.pr_state(Path("/proj"))
    assert out["open"] == 1
    assert out["items"][0] == {"number": 7, "title": "Fix", "branch": "claude/fix"}


def test_pr_state_handles_gh_unavailable(monkeypatch):
    _patch_run(monkeypatch, lambda args: _cp("", 1, "gh: not logged in"))
    out = ps.pr_state(Path("/proj"))
    assert out["open"] is None
    assert "gh unavailable" in out["error"]


def test_pr_state_handles_bad_json(monkeypatch):
    _patch_run(monkeypatch, lambda args: _cp("not json"))
    out = ps.pr_state(Path("/proj"))
    assert out["open"] is None
    assert "parse error" in out["error"]


# ── ticket_state ─────────────────────────────────────────────────────────────


def test_ticket_state_no_tickets_dir(tmp_path):
    out = ps.ticket_state(tmp_path)  # no tickets/ subdir
    assert out["ready"] is None
    assert out["error"] == "no tickets/ directory"
    assert out["closed_unarchived"] == []  # key present in every return path


def test_ticket_state_erg_missing_falls_back_to_file_count(tmp_path, monkeypatch):
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    (tickets / "0001-open.erg").write_text("%erg 0.1\nTitle: open one\n")
    (tickets / "0002-closed.erg").write_text(
        "%erg 0.1\nClosed: 2026-01-01\nTitle: done\n"
    )
    # Make the erg lookup raise FileNotFoundError to exercise the fallback path.
    monkeypatch.setattr(ps.shutil, "which", lambda _x: None)

    def responder(args):
        raise FileNotFoundError("erg")

    monkeypatch.setattr(ps, "run", lambda args, cwd: responder(args))
    out = ps.ticket_state(tmp_path)
    assert out["error"] == "erg not found"
    assert out["open"] == 1  # only the non-Closed ticket counted
    # The closed ticket sits in tickets/ (not tickets/closed/) — unarchived.
    assert out["closed_unarchived"] == ["0002"]


def test_ticket_state_flags_closed_but_unarchived(tmp_path, monkeypatch):
    """A top-level tickets/*.erg carrying a Closed: header is the
    close-without-archive escape — flag its id, exclude it from `open`."""
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    (tickets / "closed").mkdir()
    # Two genuinely open, one closed-but-unarchived in tickets/, one properly archived.
    (tickets / "0010-open-a.erg").write_text("%erg 0.1\nTitle: A\n")
    (tickets / "0011-open-b.erg").write_text("%erg 0.1\nTitle: B\n")
    (tickets / "0012-done.erg").write_text("%erg 0.1\nClosed: 2026-06-01\nTitle: done\n")
    (tickets / "closed" / "0009-archived.erg").write_text(
        "%erg 0.1\nClosed: 2026-05-01\nTitle: archived\n"
    )
    erg_output = (
        '[{"id": "0010", "title": "A", "file": "0010-open-a.erg", "closed": null,'
        ' "refs": [], "tags": [], "blocked_by": []},'
        ' {"id": "0011", "title": "B", "file": "0011-open-b.erg", "closed": null,'
        ' "refs": [], "tags": [], "blocked_by": []}]'
    )
    monkeypatch.setattr(ps.shutil, "which", lambda _x: "/usr/bin/erg")
    monkeypatch.setattr(ps, "run", lambda args, cwd: _cp(erg_output))

    out = ps.ticket_state(tmp_path)
    assert out["closed_unarchived"] == ["0012"]  # only the unarchived closed one
    assert out["open"] == 2  # the archived ticket in closed/ is not scanned
    assert out["ready"] == 2


def test_ticket_state_ready_ids_populated(tmp_path, monkeypatch):
    """erg ready --json returns no 'ready' key; ready_ids must NOT filter on it."""
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    erg_output = '[{"id": "0042", "title": "Do thing", "file": "0042-do-thing.erg", "closed": null, "refs": [], "tags": [], "blocked_by": []}, {"id": "0043", "title": "Other thing", "file": "0043-other-thing.erg", "closed": null, "refs": [], "tags": [], "blocked_by": []}]'
    monkeypatch.setattr(ps.shutil, "which", lambda _x: "/usr/bin/erg")
    monkeypatch.setattr(ps, "run", lambda args, cwd: _cp(erg_output))

    (tickets / "0042-do-thing.erg").write_text("%erg 0.1\nTitle: Do thing\n")
    (tickets / "0043-other-thing.erg").write_text("%erg 0.1\nTitle: Other thing\n")

    out = ps.ticket_state(tmp_path)
    assert out["ready"] == 2, "ready_ids should include all erg-ready tickets"
    assert out["ready_ids"] == ["0042", "0043"]
