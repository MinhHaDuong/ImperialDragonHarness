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
    assert "/zotero check-staging" in run(tmp_path)


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


def test_midnight_exact_file_fires(tmp_path):
    from datetime import datetime

    (tmp_path / "docs").mkdir()
    f = tmp_path / "docs" / "mid.pdf"
    f.write_text("x")
    midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    os.utime(f, (midnight, midnight))
    assert "/zotero check-staging" in run(tmp_path)


def test_symlinked_staging_file_fires(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "new.pdf").write_text("x")
    (tmp_path / "docs" / "new.pdf").symlink_to("../target/new.pdf")
    assert "/zotero check-staging" in run(tmp_path)


def test_symlinked_docs_dir_fires(tmp_path):
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / "elsewhere" / "new.pdf").write_text("x")
    (tmp_path / "docs").symlink_to("elsewhere")
    assert "/zotero check-staging" in run(tmp_path)


def test_trigger_step_is_reachable():
    import re

    text = (ROOT / "skills" / "lair" / "SKILL.md").read_text()
    trigger = text.index("zotero-reconcile-trigger")
    assert trigger < text.index("Then\n    finish") if "Then\n    finish" in text else True
    assert trigger < text.index("Then finish") if "Then finish" in text else True
    step0 = re.search(r"^0\. .*$", text, re.M).group(0)
    num = re.search(r"^(\d+)\. \*\*Propose the staging reconcile", text, re.M).group(1)
    assert re.search(rf"\b{num}\b", step0) and "Always perform" in step0
