"""The un-reviewable breaker counts CONTENT-BEARING files, not raw paths.

Pure renames (R100, zero line change) add no review load; counting them
(via --no-renames, where every git mv registers as delete+add) inflates
consolidation diffs past the 15-file breaker on arithmetic, not
substance — observed on PRs #1178 and #1179 (ticket 1026). The threshold
itself is untouched; only the counting rule is refined.
"""

import re
import subprocess
from pathlib import Path

from child_env import child_env

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
GAZE = REPO / "skills" / "gaze" / "SKILL.md"


def _phase1() -> str:
    text = GAZE.read_text(encoding="utf-8")
    return text.split("Compute PR size", 1)[1].split("Classify the battery", 1)[0]


def test_phase1_counts_content_bearing_files():
    """The size computation names the content-bearing rule: pure renames
    (R100) count 0; added/modified/deleted and renamed-with-edit count 1."""
    phase1 = _phase1()
    assert "content-bearing" in phase1.lower(), (
        "the Phase 1 size computation must count content-bearing files "
        "(pure renames excluded) — rename-inflated counts fire the breaker "
        "on arithmetic (ticket 1026)"
    )
    assert "R100" in phase1 or "pure rename" in phase1, (
        "the rule must name the excluded class: pure renames"
    )
    assert "--name-status -M" in phase1, (
        "the counting command must be rename-aware (`--name-status -M`), "
        "not `--no-renames`"
    )


def test_breaker_bullet_names_content_bearing():
    text = GAZE.read_text(encoding="utf-8")
    breaker = text.split("If `pr_files >= 15`", 1)[1].split(
        "When `multi_ticket` is present", 1
    )[0]
    assert "content-bearing" in breaker, (
        "the un-reviewable breaker bullet must name the content-bearing "
        "count (the threshold is unchanged; the counting is refined)"
    )
    assert "split before review" in breaker


def test_verdict_time_recheck_uses_the_phase1_rule():
    text = GAZE.read_text(encoding="utf-8")
    recheck = text.split("At verdict time, re-check", 1)[1].split(
        "if the diff against", 1
    )[0]
    assert "content-bearing" in recheck, (
        "the verdict-time re-check (0990) must count content-bearing files "
        "per the phase-1 rule — a round-2 fix of pure renames must not "
        "re-fire the breaker"
    )
    m = re.search(r"pr_files\s*>=\s*(\d+)", text)
    assert m and m.group(1) == "15", "the 15 threshold itself is untouched"


def _run(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
        env=child_env(),
    ).stdout


def _content_bearing(cwd: Path, base: str) -> int:
    """The phase-1 recipe: A/M/D count 1; R100 counts 0; R with edits
    (similarity < 100) counts 1."""
    out = _run(cwd, "diff", "--name-status", "-M", f"{base}..HEAD")
    count = 0
    for line in out.splitlines():
        if not line.strip():
            continue
        status = line.split("\t", 1)[0]
        if status.startswith("R"):
            score = re.match(r"R(\d+)", status)
            if score and int(score.group(1)) < 100:
                count += 1
        else:
            count += 1
    return count


@pytest.fixture()
def scratch(tmp_path: Path) -> Path:
    cwd = tmp_path / "repo"
    cwd.mkdir()
    _run(cwd, "init", "-q")
    _run(cwd, "config", "user.email", "t@example.org")
    _run(cwd, "config", "user.name", "t")
    for i in range(16):
        (cwd / f"f{i}.txt").write_text(
            "\n".join(f"line {j} of file {i}" for j in range(10)) + "\n"
        )
    _run(cwd, "add", "-A")
    _run(cwd, "commit", "-qm", "base")
    return cwd


def test_rename_inflated_diff_stays_under_the_breaker(scratch: Path):
    """16 paths touched, 10 of them pure renames: 6 content-bearing —
    the breaker (>= 15) must NOT fire on rename arithmetic."""
    for i in range(6):
        (scratch / f"f{i}.txt").write_text(
            "\n".join(f"line {j} of file {i}" for j in range(9))
            + "\nline 9 edited\n"
        )
    for i in range(6, 16):
        (scratch / f"f{i}.txt").rename(scratch / f"moved{i}.txt")
    _run(scratch, "add", "-A")
    _run(scratch, "commit", "-qm", "wave")
    assert _content_bearing(scratch, "HEAD~1") == 6


def test_renamed_with_edit_counts_once(scratch: Path):
    """A rename that also edits its content is content-bearing: counts 1
    (rename detection engaged: similarity above the threshold)."""
    (scratch / "f0.txt").rename(scratch / "moved0.txt")
    (scratch / "moved0.txt").write_text(
        "\n".join(f"line {j} of file 0" for j in range(9))
        + "\nline 9 edited\n"
    )
    _run(scratch, "add", "-A")
    _run(scratch, "commit", "-qm", "rename+edit")
    assert _content_bearing(scratch, "HEAD~1") == 1


def test_genuinely_large_diff_fires(scratch: Path):
    """16 content-bearing files: the breaker fires as before."""
    for i in range(16):
        (scratch / f"f{i}.txt").write_text(
            "\n".join(f"line {j} of file {i}" for j in range(9))
            + "\nline 9 edited\n"
        )
    _run(scratch, "add", "-A")
    _run(scratch, "commit", "-qm", "big")
    assert _content_bearing(scratch, "HEAD~1") == 16
