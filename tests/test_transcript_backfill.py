"""Ticket 1391: the one-off cadens backfill adds absent files, keeps the larger copy, skips broken links."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transcript_backfill.py"
pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(shutil.which("zstd") is None, reason="zstd not installed")]


def zst(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["zstd", "-q", "-o", str(path)], input=text.encode(), check=True)


def unzst(path: Path) -> str:
    return subprocess.run(["zstd", "-dc", str(path)], capture_output=True, check=True).stdout.decode()


def test_backfill_adds_absent_keeps_larger_and_counts(tmp_path):
    src, dest = tmp_path / "cadens/padme", tmp_path / "raw/padme/claude"
    (src / "-p").mkdir(parents=True)
    (src / "-p/old.jsonl").write_text("pruned from live\n")
    os.utime(src / "-p/old.jsonl", (1_700_000_000, 1_700_000_000))
    (src / "-p/grown.jsonl").write_text("the longer copy\n")
    (src / "-p/trunc.jsonl").write_text("short\n")
    (src / "-p/broken.jsonl").symlink_to(tmp_path / "nowhere")
    zst(dest / "-p/grown.jsonl.zst", "short\n")
    zst(dest / "-p/trunc.jsonl.zst", "short, then appended\n")

    out = subprocess.run([sys.executable, "-I", str(SCRIPT), str(src), str(dest)],
                         capture_output=True, text=True, check=True).stdout
    assert "unreadable: 1 files" in out
    assert "added: 1 files" in out and "replaced: 1 files" in out and "kept: 1 files" in out
    assert unzst(dest / "-p/old.jsonl.zst") == "pruned from live\n"
    assert unzst(dest / "-p/grown.jsonl.zst") == "the longer copy\n"
    assert unzst(dest / "-p/trunc.jsonl.zst") == "short, then appended\n"
    added = dest / "-p/old.jsonl.zst"
    assert added.stat().st_mtime == 1_700_000_000 and added.stat().st_mode & 0o777 == 0o600
    assert (src / "-p/trunc.jsonl").read_text() == "short\n"  # the source is only read

    again = subprocess.run([sys.executable, "-I", str(SCRIPT), str(src), str(dest)],
                           capture_output=True, text=True, check=True).stdout
    assert "added: 0 files" in again and "replaced: 0 files" in again
