"""Tests for the beat-skip expiry logic in scripts/housekeeping-git.sh."""

import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "housekeeping-git.sh"


def _fake_repo(tmp_path):
    """Minimal fake git repo layout the script expects."""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    (tmp_path / "tickets").mkdir()
    return tmp_path


def _run(cwd):
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_object_array_prunes_expired(tmp_path):
    """Expired object entries are removed; active and indefinite survive."""
    repo = _fake_repo(tmp_path)
    skip = [
        {"id": "0001", "until": "2020-01-01T00:00:00Z", "reason": "expired"},
        {"id": "0002", "until": "2099-01-01T00:00:00Z", "reason": "active"},
        {"id": "0003", "reason": "indefinite"},
    ]
    skip_file = repo / ".git" / "beat-skip.json"
    skip_file.write_text(json.dumps(skip))

    result = _run(repo)

    assert result.returncode == 0
    assert result.stderr == ""
    remaining = json.loads(skip_file.read_text())
    ids = [e["id"] for e in remaining]
    assert "0001" not in ids
    assert "0002" in ids
    assert "0003" in ids


def test_legacy_string_array_no_error(tmp_path):
    """Legacy plain-string arrays produce no stderr and result in empty list."""
    repo = _fake_repo(tmp_path)
    skip_file = repo / ".git" / "beat-skip.json"
    skip_file.write_text(json.dumps(["0001", "0012"]))

    result = _run(repo)

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(skip_file.read_text()) == []


def test_empty_array_no_error(tmp_path):
    """Empty beat-skip list is written back as empty without error."""
    repo = _fake_repo(tmp_path)
    skip_file = repo / ".git" / "beat-skip.json"
    skip_file.write_text("[]")

    result = _run(repo)

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(skip_file.read_text()) == []


def test_no_skip_file_is_noop(tmp_path):
    """Script runs cleanly when beat-skip.json is absent."""
    repo = _fake_repo(tmp_path)
    result = _run(repo)
    assert result.returncode == 0
    assert not (repo / ".git" / "beat-skip.json").exists()
