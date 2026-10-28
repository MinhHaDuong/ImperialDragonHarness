"""Ticket 1319: status and hygiene scripts read merge requests through forge.py.

On a repository with no forge (no origin remote) each answers "not inspected" or a typed
refusal, never an empty list read as "nothing open". No gh is on PATH in these tests.
"""

import importlib.util
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


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          env=child_env()).stdout


def no_gh_path(tmp_path):
    """A PATH holding git, python3 and coreutils but no gh."""
    bin_dir = tmp_path / "nogh"
    bin_dir.mkdir()
    for tool in ("git", "python3", "bash", "sed", "grep", "paste", "tr", "head", "dirname", "env", "cat", "sh"):
        found = shutil.which(tool)
        if found:
            (bin_dir / tool).symlink_to(found)
    return str(bin_dir)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "T")
    (root / "tickets").mkdir()
    (root / "tickets" / "0001-x.erg").write_text("%erg 0.1\nTitle: x\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "seed")
    return root


def test_dashboard_without_gh_says_not_inspected(repo, tmp_path):
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(repo), str(origin)], check=True, env=child_env())
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "fetch", "-q", "origin")
    env = dict(child_env(), PATH=no_gh_path(tmp_path))
    done = subprocess.run([shutil.which("bash"), str(ROOT / "skills" / "dashboard" / "dashboard.sh")],
                          cwd=repo, env=env, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert "NOT inspected" in done.stdout
    assert "== open merge requests" not in done.stdout


def test_tmp_report_references_unknown_without_forge(repo):
    report = load("tmp_report_t1319", "tmp_report.py")
    ref = report._references([{"path": "/x/.tmp/a"}], repo)
    assert ref["/x/.tmp/a"]["pull_requests"] == "unknown"


def test_tmp_guard_without_forge_reads_commits_only_and_refuses_unreadable_forge(repo, tmp_path):
    guard = load("guard_t1319", "worktree-tmp-guard.py")
    git(repo, "switch", "-q", "-c", "feat")
    sources = guard.citation_sources(repo, repo, "feat")
    assert not any(label.startswith("PR #") for label, _ in sources)
    git(repo, "remote", "add", "origin", "https://example.invalid/r.git")  # a forge, but no gh on PATH
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PATH", no_gh_path(tmp_path))
        with pytest.raises(guard.Blocked, match="could not inspect"):
            guard.citation_sources(repo, repo, "feat")


def test_project_state_no_forge_is_not_zero(repo):
    ps = load("ps_t1319", "project-state.py")
    out = ps.pr_state(repo)
    assert out["open"] is None and "no forge" in out["error"]


def test_sitrep_no_forge_is_none_not_an_empty_list(repo, monkeypatch):
    sitrep = load("sitrep_t1319", "raid-sitrep.py")
    monkeypatch.chdir(repo)
    assert sitrep.open_prs() is None
