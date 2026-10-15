"""Lair proposes the staging reconcile, never runs it (ticket 1112)."""
import os
import subprocess
import time

from child_env import child_env
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIGGER = ROOT / "skills" / "lair" / "zotero-reconcile-trigger"


def run(project: Path) -> str:
    out = subprocess.run([str(TRIGGER), str(project)], capture_output=True, text=True, check=True, env=child_env())
    return out.stdout


def test_fresh_docs_file_fires(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "new.pdf").write_text("x")
    assert "/zotero reconcile" in run(tmp_path)


def test_old_docs_file_is_silent(tmp_path):
    (tmp_path / "docs").mkdir()
    f = tmp_path / "docs" / "old.pdf"
    f.write_text("x")
    old = time.time() - 3 * 86400
    os.utime(f, (old, old))
    assert run(tmp_path) == ""


def test_no_docs_dir_is_silent(tmp_path):
    assert run(tmp_path) == ""


def test_skill_proposes_never_runs():
    text = (ROOT / "skills" / "lair" / "SKILL.md").read_text()
    assert "zotero-reconcile-trigger" in text
    assert "never run automatically" in text
