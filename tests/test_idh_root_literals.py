"""Reject canonical repository paths spelled as Claude runtime paths.

This ratchet predates the portable checkout contract (0999). It covers
Claude-native literals; fixed ~/.idh defaults are additional portability
work tracked by 0999. Native paths and reviewed exceptions remain explicit.

Covered spellings: `~/`, `$HOME/` and `${HOME}/` (quoted or not), systemd
`%h/`, an absolute `/home/<user>/` prefix, and the pathlib/os.path forms
`Path.home() / ".claude"`, `.joinpath(".claude")`, `os.path.join(<home>,
".claude")`. A guard wired to one spelling is not a guard, but this list is not
every spelling either: `$HOMEDIR/.claude`, `Path(home) / ".claude"`,
`$HOME/./.claude` and f-strings still pass (residual coverage tracked by 0999).
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parent.parent

# Where live wiring lives: scripts, hooks, adapters, settings, units, skills.
SCOPES = ("scripts", "bin", "hooks", "adapters", "systemd", "skills", "settings.shared.json")

LITERAL = re.compile(
    r"""(?:~|"?\$HOME"?|"?\$\{HOME\}"?|%h|/home/[A-Za-z0-9_.-]+)/\.claude(?![\w.-])(\S*)"""
)
# The Python spellings: Path.home() / ".claude", Path.home().joinpath(".claude"),
# os.path.join(<home>, ".claude"), each with an optional next segment.
_HOME_EXPR = r"""(?:[\w.]*\.)?(?:home\(\)|expanduser\(\s*["']~["']\s*\)|environ\[\s*["']HOME["']\s*\]|\bhome\b|\bHOME\b)"""
PY_LITERAL = re.compile(
    r"(?:" + _HOME_EXPR + r"""\s*/\s*|home\(\)\.joinpath\(\s*|path\.join\(\s*""" + _HOME_EXPR
    + r"""\s*,\s*)["']\.claude["'](?:\s*(?:/|,)\s*["']([\w.-]+)["'])?"""
)

# Claude Code's native root: the runtime reads these at ~/.claude by design.
NATIVE = re.compile(
    r"^/(?:projects|settings\.json|settings\.local\.json|stats-cache\.json|telemetry"
    r"|history\.jsonl)(?![\w.-])"
)

# Reviewed lines that name ~/.claude on purpose: (path, line substring, reason).
ALLOWED = [
    ("adapters/claude-code/bin/idh-hook", "cannot name $HOME/.claude",
     "explains why the plugin cannot hard-code the native root"),
    ("adapters/README.md", "It scans `$HOME/.claude/skills`",
     "Claude Code's personal-skills scan root"),
    ("adapters/README.md", "| Claude Code | `$HOME/.claude/skills` |",
     "Claude Code's personal-skills scan root"),
    ("adapters/claude-code/README.md", "a plugin under `$HOME/.claude/skills/<name>/`",
     "measured Claude Code plugin discovery path"),
    ("adapters/perch.py", 'return _home() / ".claude" / "skills" / skill',
     "Claude Code's personal-skills scan root"),
    ("adapters/pilot-support.json", '"skills_root": "$HOME/.claude/skills"',
     "Claude Code's personal-skills scan root"),
    ("adapters/pilot-support.json", "the harness checkout is $HOME/.claude",
     "historical measured pilot layout, not an installation requirement"),
    ("adapters/pilot-support.json", '"native_expression": "$HOME/.claude/skills/perch',
     "Claude Code's native expression of the skill"),
    ("adapters/pilot-support.json", "personal skills live in ~/.claude/skills/",
     "quotes Claude Code's documentation"),
    ("adapters/projections.json", '"path": "~/.claude/', "Runtime-owned registration destinations"),
    ("scripts/adapter-claude-code-activate.sh", 'LINK="$HOME/.claude/skills/', "Native plugin discovery"),
    ("scripts/on-start.sh", "`~/.claude/rules/**.md` into the system prompt", "Native rules loader"),
    ("scripts/probe-plugin-hook-loading.sh", "a plugin at $HOME/.claude/skills/", "Native plugin discovery"),
    ("skills/roar/SKILL.md", "of a `~/.claude/projects/` slug",
     "native project store"),
]


def _scope_files(root: Path):
    for scope in SCOPES:
        path = root / scope
        if path.is_file():
            yield path
        elif path.is_dir():
            for f in sorted(path.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts and not f.is_symlink():
                    yield f


def offending_literals(root: Path, allowed=ALLOWED):
    """Return (relpath, lineno, line) for every non-native, non-allowed literal."""
    found = []
    for f in _scope_files(root):
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        rel = f.relative_to(root).as_posix()
        for lineno, line in enumerate(text.splitlines(), 1):
            rests = [m.group(1) for m in LITERAL.finditer(line)]
            rests += ["/" + (m.group(1) or "") for m in PY_LITERAL.finditer(line)]
            for rest in rests:
                if NATIVE.match(rest):
                    continue
                if any(rel == p and s in line for p, s, _ in allowed):
                    continue
                found.append((rel, lineno, line.strip()))
    return found


def test_live_wiring_names_the_harness_as_idh():
    found = offending_literals(REPO)
    assert not found, "\n".join(f"{r}:{n}: {text}" for r, n, text in found)


def test_every_allowlist_entry_still_matches_a_line():
    """A stale allowlist entry is a hole waiting for a new literal."""
    for rel, needle, reason in ALLOWED:
        assert reason
        assert needle in (REPO / rel).read_text(), (rel, needle)


@pytest.mark.parametrize(
    "planted",
    [
        'bash "$HOME/.claude/scripts/x.sh"',
        "cat ~/.claude/STATE.md",
        "cd ${HOME}/.claude",
        "WorkingDirectory=%h/.claude",
        '"BASH_ENV": "/home/someone/.claude/scripts/bash-env.sh"',
        "git -C ~/.claude status",
        'ROOT = Path.home() / ".claude"',
        "base = Path.home() / '.claude' / 'memory'",
        'cat "$HOME"/.claude/STATE.md',
        'root = Path.home().joinpath(".claude")',
        'root = os.path.join(os.path.expanduser("~"), ".claude")',
        'root = os.path.join(home, ".claude", "scripts")',
    ],
)
def test_positive_control_fires_on_a_planted_literal(tmp_path, planted):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "planted.sh").write_text(planted + "\n")
    assert offending_literals(tmp_path, allowed=[]) == [("scripts/planted.sh", 1, planted)]


@pytest.mark.parametrize(
    "native",
    [
        "ls ~/.claude/projects/",
        'jq . "$HOME/.claude/settings.json"',
        "find %h/.claude/telemetry -name x",
        "cat ~/.idh/STATE.md",
        "cd <project>/.claude/worktrees/x",
        'd = Path.home() / ".claude" / "projects"',
        'rules = project / ".claude" / "rules"',
        'root = os.path.join(home, ".claude", "projects")',
    ],
)
def test_native_root_and_idh_spellings_pass(tmp_path, native):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "ok.sh").write_text(native + "\n")
    assert offending_literals(tmp_path, allowed=[]) == []
