"""Isolated diagnostic controls; subprocess fixtures never touch a live project."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
pytestmark = pytest.mark.integration


def load_probe():
    path = SCRIPTS / "test_target_probe.py"
    assert path.exists(), "the isolated diagnostic is not implemented"
    spec = importlib.util.spec_from_file_location("test_target_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(project, *args):
    return subprocess.run(["git", "-C", str(project), *args], check=True,
                          capture_output=True, text=True).stdout


def repo(tmp_path, recipe):
    project = tmp_path / "primary"
    project.mkdir()
    git(project, "init", "-q")
    git(project, "config", "user.name", "Fixture")
    git(project, "config", "user.email", "fixture@example.invalid")
    (project / "tracked").write_text("original\n")
    (project / "Makefile").write_text("test:\n\t" + recipe + "\n")
    git(project, "add", "Makefile", "tracked")
    git(project, "commit", "-qm", "fixture")
    return project


@pytest.mark.parametrize("recipe, expected", [
    ("true", "unchanged"),
    ("printf changed > tracked", "finding"),
    ("touch generated", "finding"),
    ("rm tracked", "finding"),
    ("false", "unavailable"),
])
def test_probe_preserves_primary_and_classifies(tmp_path, recipe, expected):
    module = load_probe()
    project = repo(tmp_path, recipe)
    # Primary dirt never enters the detached probe.
    (project / "author-output").write_text("keep")
    before = git(project, "status", "--porcelain")
    out = module.probe(project, "test", tmp_path / "scratch", timeout=10)
    assert out["status"] == expected
    assert out["head"] == git(project, "rev-parse", "HEAD").strip()
    assert git(project, "status", "--porcelain") == before
    assert (project / "tracked").read_text() == "original\n"
    assert (project / "author-output").read_text() == "keep"
    if expected != "unchanged":
        assert Path(out["worktree"]).exists()
        assert Path(out["log"]).exists()
    else:
        assert not Path(out["worktree"]).exists()


def test_timeout_retains_evidence(tmp_path):
    module = load_probe()
    project = repo(tmp_path, "sleep 10")
    out = module.probe(project, "test", tmp_path / "scratch", timeout=0.1)
    assert out["status"] == "unavailable"
    assert out["execution"] == "timeout"
    assert Path(out["worktree"]).exists()
    assert (project / "tracked").read_text() == "original\n"


def test_missing_makefile_is_unavailable(tmp_path):
    module = load_probe()
    project = repo(tmp_path, "true")
    git(project, "rm", "Makefile")
    git(project, "commit", "-qm", "no target configuration")
    out = module.probe(project, "test", tmp_path / "scratch", timeout=10)
    assert out["status"] == "unavailable"
    assert out["execution"] == "not-run"


def test_seeded_untracked_deletion_control(tmp_path):
    """A seeded dirty baseline exercises deletion; production begins clean."""
    module = load_probe()
    project = repo(tmp_path, "true")
    (project / "sentinel").write_text("seeded control")
    before = module.snapshot(project)
    (project / "sentinel").unlink()
    after = module.snapshot(project)
    assert module.changes(before, after)["status_changed"] is True


def test_missing_make_executable_is_unavailable(tmp_path, monkeypatch):
    module = load_probe()
    project = repo(tmp_path, "true")
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    out = module.probe(project, "test", tmp_path / "scratch", timeout=10)
    assert out["status"] == "unavailable"
    assert out["execution"] == "not-run"
    assert Path(out["worktree"]).exists()


def test_endpoint_limit_does_not_claim_to_detect_restored_write(tmp_path):
    module = load_probe()
    project = repo(tmp_path, "cp tracked saved; printf changed > tracked; mv saved tracked")
    out = module.probe(project, "test", tmp_path / "scratch", timeout=10)
    assert out["status"] == "unchanged"


def test_tracked_fifo_mutation_does_not_hang_snapshot(tmp_path):
    """A selected target's timeout must not be defeated by reading its FIFO."""
    project = repo(tmp_path, "rm tracked; mkfifo tracked")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "test_target_probe.py"), str(project),
             "--target", "test", "--scratch-dir", str(tmp_path / "scratch"), "--timeout", "0.2"],
            capture_output=True, text=True, timeout=3, check=True,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("after-snapshot blocked on tracked FIFO beyond target timeout")
    import json

    report = json.loads(result.stdout)
    assert report["status"] == "finding"
    assert report["changes"]["tracked_changed"] == ["tracked"]
    assert (project / "tracked").read_text() == "original\n"
