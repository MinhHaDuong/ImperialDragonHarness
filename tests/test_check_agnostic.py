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


# --- Repo-relative script path pattern (ticket 0204, pinned by ticket 0213) ---
#
# The SKILL_PATTERNS entry catching repo-relative `scripts/<name>.(sh|py)`
# references only runs against directories matching the skills case (`skills*`
# or `*/skills*`), so these fixtures live under a `skills` subdir. Skills must
# reference scripts via `~/.claude/scripts/` or `$HARNESS_DIR`, never as a bare
# repo-relative `scripts/foo.sh` that assumes the harness IS the cwd.


def _skill_dir(tmp_path):
    """A directory whose name makes check-agnostic.sh apply SKILL_PATTERNS."""
    d = tmp_path / "skills"
    d.mkdir()
    return d


def _skill_doc(tmp_path, body):
    d = _skill_dir(tmp_path)
    (d / "SKILL.md").write_text(f"# Example skill\n\n{body}\n")
    return d


def test_fails_on_repo_relative_script_path(tmp_path):
    """A bare `scripts/foo.sh` reference in a skill must fail the check."""
    d = _skill_doc(tmp_path, "Run `scripts/foo.sh` to do the thing.")
    result = _run(d)
    assert result.returncode != 0, result.stdout
    assert "VIOLATION" in result.stdout
    assert "scripts/foo.sh" in result.stdout


def test_passes_on_agnostic_script_path_forms(tmp_path):
    """Home-anchored, HARNESS_DIR, and ./-prefixed forms are all agnostic."""
    for body in (
        "Run `~/.claude/scripts/foo.sh` to do the thing.",
        "Run `$HARNESS_DIR/scripts/foo.py` to do the thing.",
        "Run `./scripts/foo.sh` to do the thing.",
    ):
        sub = tmp_path / f"case_{abs(hash(body))}"
        sub.mkdir()
        d = _skill_doc(sub, body)
        result = _run(d)
        assert result.returncode == 0, f"{body!r} -> {result.stdout}"


def test_catches_mixed_case_and_underscore_script_names(tmp_path):
    """Stem must cover uppercase/digit/underscore names, not just [a-z-].

    Red against the original `[a-z-]\\+` stem; green once broadened to
    `[A-Za-z0-9_-]`. This is the deliberately-broken-pattern pin.
    """
    d = _skill_doc(tmp_path, "Run `scripts/Build_Step2.py` to do the thing.")
    result = _run(d)
    assert result.returncode != 0, result.stdout
    assert "VIOLATION" in result.stdout
    assert "scripts/Build_Step2.py" in result.stdout


# --- Multi-line command continuation markers (ticket 0273) ---
#
# The marker's natural home on a multi-line command is the closing continuation
# line, not the line carrying the flagged token. A marker anywhere in the same
# logical command (across `\`-continued lines) must exempt the whole command.

MARKED_MULTILINE = (
    "# Example skill\n\n"
    "```bash\n"
    's=$(gh pr view "$PR" --json state \\\n'
    "    --jq '.state' \\\n"
    "    2>/dev/null) || return 1  # harness-extension-point\n"
    "```\n"
)
UNMARKED_MULTILINE = (
    "# Example skill\n\n"
    "```bash\n"
    's=$(gh pr view "$PR" --json state \\\n'
    "    --jq '.state' \\\n"
    "    2>/dev/null) || return 1\n"
    "```\n"
)


def test_marker_on_continuation_line_exempts_command(tmp_path):
    """A marker on the command's closing continuation line exempts the whole command."""
    d = _skill_dir(tmp_path)
    (d / "SKILL.md").write_text(MARKED_MULTILINE)
    result = _run(d)
    assert result.returncode == 0, result.stdout


def test_unmarked_multiline_command_still_flagged(tmp_path):
    """No marker anywhere in the command → still a violation (no over-exemption)."""
    d = _skill_dir(tmp_path)
    (d / "SKILL.md").write_text(UNMARKED_MULTILINE)
    result = _run(d)
    assert result.returncode != 0, result.stdout
    assert "VIOLATION" in result.stdout
