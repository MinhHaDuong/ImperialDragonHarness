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


def _run_no_args(cwd):
    """Invoke the gate with no dir args (as CI does), from the given cwd."""
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(cwd),
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


# --- scripts/ dir coverage (ticket 0322) ---
#
# The default scan (no args, as CI runs it) must include scripts/, so a
# hardcoded home path in a shell/python helper is caught mechanically instead
# of only in human review. SKILL_PATTERNS must NOT fire in scripts/, which
# legitimately use gh/uv/repo-relative script paths.


def test_real_scripts_dir_is_agnostic():
    """The actual scripts/ tree passes the agnostic gate (ticket 0322)."""
    result = _run(SCRIPT.parent)
    assert result.returncode == 0, result.stdout


def test_default_no_arg_scan_includes_scripts_dir(tmp_path):
    """No-arg invocation (as CI runs it) must scan a scripts/ subdir."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "helper.sh").write_text("HOMEDIR=/home/someone/.claude\n")
    result = _run_no_args(tmp_path)
    assert result.returncode != 0, result.stdout
    assert "VIOLATION" in result.stdout


def test_skill_patterns_do_not_fire_in_scripts_dir(tmp_path):
    """gh/uv/repo-relative script tokens are legal in scripts/ — no false fire."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "helper.sh").write_text(
        "gh pr view 5\nuv run pytest\n./scripts/other.sh\n"
    )
    result = _run(scripts)
    assert result.returncode == 0, result.stdout


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


# --- PROSE_PATTERNS: vendor-namespaced runtime knobs in doctrine prose --------
# Regression guard for the 2026-07-27 gap: rules/ was outside the scanned dirs
# AND no pattern covered vendor env names, so a rule written around
# CLAUDE_CODE_* passed every gate. Both halves are pinned below — dropping
# either one alone would let the same text through again.


def _rules_dir(tmp_path):
    """A directory whose name makes check-agnostic.sh apply PROSE_PATTERNS."""
    d = tmp_path / "rules"
    d.mkdir()
    return d


VENDOR_LINE = "Set `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` to bound the fan-out.\n"


def test_fails_on_vendor_env_var_in_rules(tmp_path):
    """Doctrine naming a vendor runtime knob rots with the tool — name the
    capability instead (workflow.md § Writing Skills and Hooks)."""
    d = _rules_dir(tmp_path)
    (d / "workflow.md").write_text(f"# Rules\n\n{VENDOR_LINE}")
    result = _run(d)
    assert result.returncode == 1, result.stdout
    assert "CLAUDE_CODE_" in result.stdout


def test_vendor_env_var_escape_hatch_in_rules(tmp_path):
    """The concrete knob may be recorded behind a harness-extension-point."""
    d = _rules_dir(tmp_path)
    (d / "workflow.md").write_text(
        f"# Rules\n\n<!-- harness-extension-point -->\n{VENDOR_LINE}"
    )
    result = _run(d)
    assert result.returncode == 0, result.stdout


def test_rules_dir_is_scanned_by_default(tmp_path):
    """rules/ must be in the default dir list, not just reachable by argument:
    CI invokes the gate per-dir, and a rules/ target that nothing calls is the
    gap this test exists for."""
    d = _rules_dir(tmp_path)
    (d / "workflow.md").write_text(f"# Rules\n\n{VENDOR_LINE}")
    result = _run_no_args(tmp_path)
    assert result.returncode == 1, (
        "rules/ not scanned when the gate runs with no dir args:\n" + result.stdout
    )


def test_forge_patterns_not_applied_to_rules(tmp_path):
    """Deliberate boundary: rules/git.md documents forge mechanics concretely
    by design. Retrofitting SKILL_PATTERNS onto rules/ is a separate cleanup —
    pin the current scope so widening it is a conscious edit, not a drift."""
    d = _rules_dir(tmp_path)
    (d / "git.md").write_text("# Git\n\nRun `gh pr merge` from the branch.\n")
    result = _run(d)
    assert result.returncode == 0, (
        "forge patterns leaked onto rules/ — intended scope is skills/ only:\n"
        + result.stdout
    )
