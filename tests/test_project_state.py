"""Tests for scripts/project-state.py — the per-collector parsers.

Each collector shells out via the module-level `run()`. We patch `run` with a
fake that returns canned CompletedProcess objects, so these tests pin the
parsing of git/gh porcelain output without touching a real repo.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

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
    monkeypatch.setattr(ps, "run", lambda args, cwd, timeout=30: responder(args))


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


def _forge_listing(monkeypatch, rows=None, refusal=None):
    import forge

    class Backend:
        def list_requests(self, *args, **kwargs):
            if refusal:
                raise forge.ForgeRefusal(refusal)
            return forge.NOOP if rows is None else rows

    monkeypatch.setattr(forge, "get_forge_listing", lambda choice=None, cwd=None: Backend())


def test_pr_state_reads_the_forge_listing(monkeypatch):
    _forge_listing(monkeypatch, [{"number": 7, "title": "Fix", "branch": "claude/fix"}])
    out = ps.pr_state(Path("/proj"))
    assert out["open"] == 1
    assert out["items"][0] == {"number": 7, "title": "Fix", "branch": "claude/fix"}


def test_pr_state_handles_forge_unavailable(monkeypatch):
    _forge_listing(monkeypatch, refusal="gh: not logged in")
    out = ps.pr_state(Path("/proj"))
    assert out["open"] is None
    assert "forge unavailable" in out["error"]


def test_pr_state_no_forge_is_not_inspected_never_zero(monkeypatch):
    _forge_listing(monkeypatch, rows=None)
    out = ps.pr_state(Path("/proj"))
    assert out["open"] is None
    assert "no forge" in out["error"]



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


def test_ticket_state_prefers_vendored_erg_over_path(tmp_path, monkeypatch):
    """The project's tickets/erg reads its tickets' format; an older erg on
    PATH would report false violations, so the vendored binary wins."""
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    vendored = tickets / "erg"
    vendored.write_text("#!/bin/sh\n")
    vendored.chmod(0o755)
    monkeypatch.setattr(ps.shutil, "which", lambda _x: "/usr/local/bin/erg")
    seen = []

    def responder(args):
        seen.append(args[0])
        return _cp(returncode=1)

    monkeypatch.setattr(ps, "run", lambda args, cwd: responder(args))
    ps.ticket_state(tmp_path)
    assert seen[0] == str(vendored)


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


# ── hooks_state (ticket 0260: stale-hook-in-worktree trap) ───────────────────


def _hooks_responder(config_out, config_rc=0, toplevel="/proj",
                     common_dir="/proj/.git", diff_out="", diff_rc=0):
    def responder(args):
        if args[:3] == ["git", "config", "core.hooksPath"]:
            return _cp(config_out, config_rc)
        if "--show-toplevel" in args:
            return _cp(toplevel + "\n")
        if "--git-common-dir" in args:
            return _cp(common_dir + "\n")
        if args[:2] == ["git", "diff"]:
            return _cp(diff_out, diff_rc)
        return _cp("", 1)

    return responder


def test_hooks_state_silent_when_hookspath_unset(monkeypatch):
    _patch_run(monkeypatch, _hooks_responder("", config_rc=1))
    out = ps.hooks_state(Path("/proj"))
    assert out["in_worktree"] is False
    assert out["stale_files"] == []


def test_hooks_state_silent_when_hookspath_under_git_dir(monkeypatch):
    _patch_run(monkeypatch, _hooks_responder(".git/hooks\n"))
    out = ps.hooks_state(Path("/proj"))
    assert out["in_worktree"] is False
    assert out["stale_files"] == []


def test_hooks_state_reports_drift(monkeypatch):
    _patch_run(
        monkeypatch,
        _hooks_responder("hooks\n", diff_out="hooks/pre-commit\nhooks/pre-push\n"),
    )
    monkeypatch.setattr(ps, "_default_branch", lambda _p: "main")
    out = ps.hooks_state(Path("/proj"))
    assert out["in_worktree"] is True
    assert out["stale_files"] == ["hooks/pre-commit", "hooks/pre-push"]


def test_hooks_state_silent_when_hooks_match_default_branch(monkeypatch):
    _patch_run(monkeypatch, _hooks_responder("hooks\n", diff_out=""))
    monkeypatch.setattr(ps, "_default_branch", lambda _p: "main")
    out = ps.hooks_state(Path("/proj"))
    assert out["in_worktree"] is True
    assert out["stale_files"] == []
    assert "error" not in out


def test_hooks_state_degrades_without_remote(monkeypatch):
    _patch_run(
        monkeypatch,
        _hooks_responder(
            "hooks\n",
            diff_out="",
            diff_rc=128,
        ),
    )
    monkeypatch.setattr(ps, "_default_branch", lambda _p: "main")
    out = ps.hooks_state(Path("/proj"))
    assert out["in_worktree"] is True
    assert out["stale_files"] == []
    assert "error" in out


def test_hooks_state_wired_into_collectors():
    import inspect

    source = inspect.getsource(ps.main)
    assert '"hooks": hooks_state' in source, (
        "hooks_state must be a collector so the yawn skill sees it"
    )


def test_disk_space_state_warns_without_blocking(monkeypatch):
    monkeypatch.setattr(ps, "_disk_readings", lambda: {
        "/tmp": {"total": 100, "free": 5},
        "/home": {"total": 1000, "free": 400},
    })
    out = ps.disk_space_state(Path("/proj"))
    assert out["status"] == "warn"
    assert out["warnings"] == ["/tmp has 5% free"]


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.mark.integration
def test_state_fingerprint_ignores_branch_cut_and_tracks_state(tmp_path):
    """molt reuses a yawn report on an equal fingerprint: its own housekeeping
    branch cut must not move it; a commit or an edit must."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "f").write_text("1\n")
    _git(repo, "add", "f")
    _git(repo, "commit", "-qm", "one")
    before = ps.state_fingerprint(repo)
    assert before

    _git(repo, "switch", "-qc", "housekeeping-20261027")
    assert ps.state_fingerprint(repo) == before

    (repo / "f").write_text("2\n")
    edited = ps.state_fingerprint(repo)
    assert edited != before

    _git(repo, "commit", "-qam", "two")
    assert ps.state_fingerprint(repo) not in (before, edited)


@pytest.mark.integration
def test_state_fingerprint_sees_claude_housekeeping_branches(tmp_path):
    """Yawn check 8 reports claude/housekeeping-* branches as "tidying"; a
    reused report must not hide one created since."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "commit", "-qm", "one", "--allow-empty")
    before = ps.state_fingerprint(repo)
    _git(repo, "branch", "claude/housekeeping-foo")
    assert ps.state_fingerprint(repo) != before


def _hk_repo(tmp_path, days_old):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    when = f"{int(__import__('time').time()) - days_old * 86400} +0000"
    subprocess.run(
        ["git", "commit", "-qm", "chore: housekeeping fixes (sweep)", "--allow-empty",
         "--date", when],
        cwd=repo, check=True, capture_output=True,
        env={**__import__("os").environ, "GIT_COMMITTER_DATE": when},
    )
    return repo


@pytest.mark.integration
def test_housekeeping_state_commitless_molt_counts(tmp_path):
    """A molt that found nothing to commit leaves a marker in the git common
    dir; yawn check 8 must not report `needed` right after it."""
    repo = _hk_repo(tmp_path, 3)
    assert ps.housekeeping_state(repo)["state"] == "needed"
    (repo / ".git" / ps.HOUSEKEEPING_MARKER).touch()
    out = ps.housekeeping_state(repo)
    assert out["state"] == "clean"
    assert out["age_hours"] < 1


@pytest.mark.integration
def test_housekeeping_state_stale_marker_still_needed(tmp_path):
    """A marker older than the threshold does not mask an overdue sweep."""
    import os
    import time

    repo = _hk_repo(tmp_path, 3)
    marker = repo / ".git" / ps.HOUSEKEEPING_MARKER
    marker.touch()
    old = time.time() - 48 * 3600
    os.utime(marker, (old, old))
    assert ps.housekeeping_state(repo)["state"] == "needed"


@pytest.mark.integration
def test_dirty_tree_never_runs_deleting_target(tmp_path):
    subprocess.run([_GIT, "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "Makefile").write_text("test:\n\trm sentinel\n")
    (tmp_path / "sentinel").write_text("keep")
    out = ps.test_state(tmp_path)
    assert out["status"] == "skip"
    assert out["detail"] == "dirty tree"
    assert (tmp_path / "sentinel").read_text() == "keep"


@pytest.mark.parametrize("configuration", ["Makefile", "pyproject.toml", "package.json"])
def test_dirty_precondition_covers_every_runner(tmp_path, monkeypatch, configuration):
    (tmp_path / configuration).write_text("test:\n\ttrue\n")
    calls = []

    def respond(args):
        calls.append(args)
        return _cp("?? sentinel\n")

    _patch_run(monkeypatch, respond)
    out = ps.test_state(tmp_path)
    assert out["status"] == "skip"
    assert out["detail"] == "dirty tree"
    assert calls == [["git", "status", "--porcelain"]]


def test_unreadable_status_never_runs_tests(tmp_path, monkeypatch):
    (tmp_path / "Makefile").write_text("test:\n\ttrue\n")
    _patch_run(monkeypatch, lambda args: _cp(returncode=128, stderr="unreadable"))
    out = ps.test_state(tmp_path)
    assert out["status"] == "skip"
    assert "unreadable" in out["detail"]


@pytest.mark.parametrize("configuration, command", [
    ("Makefile", ["make", "test"]),
    ("pyproject.toml", ["pytest", "--tb=no", "-q"]),
    ("package.json", ["npm", "test"]),
])
def test_clean_precondition_allows_every_runner(tmp_path, monkeypatch, configuration, command):
    (tmp_path / configuration).write_text("test:\n\ttrue\n")
    calls = []

    def respond(args):
        calls.append(args)
        return _cp("")

    _patch_run(monkeypatch, respond)
    assert ps.test_state(tmp_path)["status"] == "pass"
    assert calls == [["git", "status", "--porcelain"], command]


# ── erg_state (ticket 1479: optional git-erg pin report) ─────────────────────

_GIT = __import__("shutil").which("git")  # PATH is emptied in these tests
_MANAGED = "# >>> erg managed >>>\nexit 0\n# <<< erg managed <<<\n"
_LEGACY = "# --- git-erg --- begin\nerg_bin=\"tickets/tools/go/erg\"\n# --- git-erg --- end\n"


def _erg_proj(tmp_path, monkeypatch, *, erg=b"pinned-bin", pin=b"pinned-bin", path_erg=None):
    import hashlib

    proj = tmp_path / "proj"
    proj.mkdir()
    subprocess.run([_GIT, "init", "-q", str(proj)], check=True)
    if erg is not None:
        (proj / "tickets").mkdir()
        (proj / "tickets" / "erg").write_bytes(erg)
    pinfile = tmp_path / "erg-pin"
    if pin is not None:
        pinfile.write_text(f"# c\nsha256={hashlib.sha256(pin).hexdigest()}\nrev=abc\n")
    monkeypatch.setattr(ps, "ERG_PIN_FILE", pinfile)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    if path_erg is not None:
        (bindir / "erg").write_bytes(path_erg)
        (bindir / "erg").chmod(0o755)
    monkeypatch.setenv("PATH", str(bindir))  # git is found by absolute path below
    monkeypatch.setattr(ps, "run", lambda a, cwd, timeout=30: subprocess.run(
        [_GIT] + a[1:], capture_output=True, text=True, cwd=cwd))
    return proj


def test_erg_pinned(tmp_path, monkeypatch):
    out = ps.erg_state(_erg_proj(tmp_path, monkeypatch, path_erg=b"pinned-bin"))
    assert (out["tickets_erg"], out["path_erg"]) == ("pinned", "pinned")
    assert out["findings"] == []


def test_erg_drifted(tmp_path, monkeypatch):
    out = ps.erg_state(_erg_proj(tmp_path, monkeypatch, erg=b"old", path_erg=b"old"))
    assert (out["tickets_erg"], out["path_erg"]) == ("drifted", "drifted")
    assert out["findings"] == ["tickets_erg drifted", "path_erg drifted"]


def test_erg_absent_is_na(tmp_path, monkeypatch):
    out = ps.erg_state(_erg_proj(tmp_path, monkeypatch, erg=None))
    assert (out["tickets_erg"], out["path_erg"], out["claims"]) == ("n/a", "n/a", False)
    assert out["findings"] == []


def test_erg_no_pin_file_is_na(tmp_path, monkeypatch):
    out = ps.erg_state(_erg_proj(tmp_path, monkeypatch, erg=b"x", pin=None))
    assert out["pin"] is None and out["tickets_erg"] == "n/a"
    assert out["findings"] == []


def test_erg_no_claims_is_not_a_finding(tmp_path, monkeypatch):
    proj = _erg_proj(tmp_path, monkeypatch)
    assert ps.erg_state(proj)["claims"] is False
    (proj / "tickets" / ".claims").mkdir()
    assert ps.erg_state(proj)["claims"] is True
    assert ps.erg_state(proj)["findings"] == []


def test_erg_dead_hookspath(tmp_path, monkeypatch):
    proj = _erg_proj(tmp_path, monkeypatch)
    _set_hooks_path(proj, "nowhere/hooks")
    assert ps.erg_state(proj)["findings"] == ["hooksPath dead"]
    (proj / "nowhere" / "hooks").mkdir(parents=True)
    out = ps.erg_state(proj)
    assert out["hooks_path_dead"] is False and out["findings"] == []


def _set_hooks_path(proj, value):
    subprocess.run([_GIT, "-C", str(proj), "config", "core.hooksPath", value], check=True)


def _hook(proj, text):
    hooks = proj / ".git" / "hooks"
    hooks.mkdir(exist_ok=True)
    (hooks / "pre-commit").write_text(text)


def test_erg_legacy_block_superseded(tmp_path, monkeypatch):
    proj = _erg_proj(tmp_path, monkeypatch)
    _hook(proj, _MANAGED + "\n# --- git-erg --- begin\nerg_bin=tickets/erg\n# --- git-erg --- end\n")
    lb = ps.erg_state(proj)["legacy_block"]
    assert lb["superseded"] is True and lb["dead_paths"] == []


def test_erg_legacy_block_dead_path(tmp_path, monkeypatch):
    proj = _erg_proj(tmp_path, monkeypatch)
    _hook(proj, _LEGACY)
    lb = ps.erg_state(proj)["legacy_block"]
    assert lb["superseded"] is False and lb["dead_paths"] == ["tickets/tools/go/erg"]


def test_erg_legacy_block_alone_is_silent(tmp_path, monkeypatch):
    proj = _erg_proj(tmp_path, monkeypatch)
    _hook(proj, "# --- git-erg --- begin\nerg_bin=tickets/erg\n# --- git-erg --- end\n")
    assert ps.erg_state(proj)["legacy_block"] is None
