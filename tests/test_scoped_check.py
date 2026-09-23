"""A scoped gate must cover every changed path or fall back to the full gate."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scoped-check.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.mark.integration
def test_doc_code_unmapped_and_mixed_diffs(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    config = {
        "default_branch": "main",
        "full_target": "check",
        "targets": ["lint", "figures", "names", "progress", "tickets", "ticket-logs", "sitter-version", "sitter-mutants", "check-fast"],
        "rules": [
            {"paths": ["*.md", "tickets/**"], "targets": ["lint", "figures", "names", "progress", "tickets", "ticket-logs"]},
            {"paths": ["plugins/**/*.md", "plugins/**/manifest.json"], "targets": ["lint", "figures", "names", "progress", "tickets", "ticket-logs", "sitter-version", "sitter-mutants"]},
        ],
    }
    (repo / ".idh-checks.json").write_text(json.dumps(config))
    (repo / "DECISIONS.md").write_text("baseline\n")
    (repo / "module.py").write_text("print('baseline')\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "baseline")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--dry-run"], cwd=repo,
            capture_output=True, text=True, check=True, env={**os.environ, "RTK_DISABLED": "1"},
        )

    (repo / "DECISIONS.md").write_text("changed\n")
    (repo / ".panel" / "17").mkdir(parents=True)
    (repo / ".panel" / "17" / "review.md").write_text("scratch\n")
    doc = run().stdout
    assert "selected: lint figures names progress tickets ticket-logs" in doc
    assert "skipped: sitter-version sitter-mutants check-fast" in doc

    (repo / "plugins").mkdir()
    (repo / "plugins" / "sitter").mkdir()
    (repo / "plugins" / "sitter" / "manifest.json").write_text("{}\n")
    plugin = run().stdout
    assert "selected: lint figures names progress tickets ticket-logs sitter-version sitter-mutants" in plugin
    assert "skipped: check-fast" in plugin
    (repo / "plugins" / "sitter" / "manifest.json").unlink()
    (repo / "plugins" / "sitter" / "README.md").write_text("plugin notes\n")
    plugin_doc = run().stdout
    assert "selected: lint figures names progress tickets ticket-logs sitter-version sitter-mutants" in plugin_doc
    assert "skipped: check-fast" in plugin_doc
    (repo / "plugins" / "sitter" / "README.md").unlink()
    (repo / "plugins" / "sitter" / "bootstrap.js").write_text("// plugin code\n")
    assert "selected: check" in run().stdout
    (repo / "plugins" / "sitter" / "bootstrap.js").unlink()

    (repo / "module.py").write_text("print('code')\n")
    code = run().stdout
    assert "selected: check" in code
    assert "skipped: none" in code

    (repo / "module.py").unlink()
    assert "selected: check" in run().stdout  # deleting code still requires full gate
    (repo / "module.py").write_text("print('baseline')\n")
    (repo / "module.py").rename(repo / "ARCHIVE.md")
    assert "selected: check" in run().stdout  # both sides of a rename count
    (repo / "ARCHIVE.md").rename(repo / "module.py")
    (repo / "new.bin").write_bytes(b"x")
    unmapped = run().stdout
    assert "selected: check" in unmapped
    assert "skipped: none" in unmapped

    (repo / "new.bin").unlink()
    (repo / "tickets").mkdir()
    (repo / "tickets" / "0001-note.erg").write_text("note\n")
    ticket = run().stdout
    assert "selected: lint figures names progress tickets ticket-logs" in ticket
    assert "skipped: sitter-version sitter-mutants check-fast" in ticket


@pytest.mark.integration
def test_failed_selected_target_still_prints_skipped_targets(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / ".idh-checks.json").write_text(json.dumps({
        "default_branch": "main", "full_target": "check", "targets": ["lint", "check-fast"],
        "rules": [{"paths": ["*.md"], "targets": ["lint"]}],
    }))
    (repo / "README.md").write_text("baseline\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "baseline")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    (repo / "README.md").write_text("changed\n")
    fake_make = tmp_path / "make"
    fake_make.write_text("#!/bin/sh\nexit 7\n")
    fake_make.chmod(0o755)
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=repo, capture_output=True, text=True,
        env={**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}", "RTK_DISABLED": "1"},
    )
    assert result.returncode == 7
    assert "skipped: check-fast" in result.stdout
