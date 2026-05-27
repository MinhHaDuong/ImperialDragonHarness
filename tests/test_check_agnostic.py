"""
Tests for scripts/check-agnostic.sh as applied to ticket bodies.

Guards ticket 0172: agents must not commit real home paths (`/home/<user>/...`)
in ticket bodies. The check already exists; these tests pin its behavior so the
`make check` / CI guard keeps catching the regression class.
"""

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "check-agnostic.sh"

# A synthetic ticket body carrying a hardcoded home path (the forbidden pattern).
BAD_TICKET = (
    "%erg 0.1\n"
    "Title: example\n"
    "\n--- body ---\n"
    "Ran the thing from /home/someone/myrepo/file.py during the session.\n"
)
CLEAN_TICKET = (
    "%erg 0.1\n"
    "Title: example\n"
    "\n--- body ---\n"
    "Ran the thing from $HOME/myrepo/file.py during the session.\n"
)


def _run(target):
    return subprocess.run(
        ["bash", str(SCRIPT), str(target)],
        capture_output=True,
        text=True,
    )


def test_fails_on_hardcoded_home_path(tmp_path):
    (tmp_path / "0001-bad.erg").write_text(BAD_TICKET)
    result = _run(tmp_path)
    assert result.returncode != 0, result.stdout
    assert "VIOLATION" in result.stdout
    assert "/home/someone" in result.stdout


def test_passes_on_agnostic_path(tmp_path):
    (tmp_path / "0001-clean.erg").write_text(CLEAN_TICKET)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout


def test_closed_subdir_is_exempt(tmp_path):
    """Closed tickets are frozen archives — a home path there must not fail."""
    closed = tmp_path / "closed"
    closed.mkdir()
    (closed / "0001-old.erg").write_text(BAD_TICKET)
    (tmp_path / "0002-open.erg").write_text(CLEAN_TICKET)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout


def test_escape_hatch_suppresses_violation(tmp_path):
    (tmp_path / "0001-doc.erg").write_text(
        "%erg 0.1\nTitle: doc\n\n--- body ---\n"
        "<!-- harness-extension-point --> example /home/someone/repo/file.py\n"
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout
