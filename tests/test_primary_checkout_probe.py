"""
Tests for scripts/check-primary-checkout.sh — the stranded-checkout probe
(ticket 0247). The probe is silent + exit 0 when a repo is on its default
branch and clean (settings.json changes tolerated); it flags + exits nonzero
when the checkout is stranded off main or dirty beyond settings.json.
"""

import subprocess
from pathlib import Path

import pytest

PROBE = Path(__file__).parent.parent / "scripts" / "check-primary-checkout.sh"


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "settings.json").write_text("{}\n")
    (r / "file.txt").write_text("x\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    return r


def _run(repo):
    return subprocess.run([str(PROBE), str(repo)], capture_output=True, text=True)


@pytest.mark.integration
def test_probe_silent_on_clean_main(repo):
    res = _run(repo)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == ""


@pytest.mark.integration
def test_probe_flags_off_main(repo):
    _git(repo, "switch", "-qc", "dream-consolidate-2026-07-10")
    res = _run(repo)
    assert res.returncode != 0
    assert "main" in (res.stdout + res.stderr).lower()


@pytest.mark.integration
def test_probe_tolerates_settings_json_change(repo):
    (repo / "settings.json").write_text('{"effortLevel": "medium"}\n')
    res = _run(repo)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == ""


@pytest.mark.integration
def test_probe_flags_dirty_beyond_settings(repo):
    (repo / "file.txt").write_text("changed\n")
    res = _run(repo)
    assert res.returncode != 0
    assert "dirty" in (res.stdout + res.stderr).lower()


@pytest.mark.integration
def test_probe_flags_untracked_new_file(repo):
    (repo / "new.txt").write_text("orphan\n")
    res = _run(repo)
    assert res.returncode != 0
