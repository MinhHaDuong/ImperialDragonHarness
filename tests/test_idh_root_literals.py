"""Live wiring names the harness as ~/.idh, never as ~/.claude (ticket 0982).

Step A of the 0978 relocation: `~/.idh` is a pointer to the checkout, and every
consumer that means "the harness repository" spells it `~/.idh` (or `$IDH_ROOT`),
so the later cutover (0986) moves bytes without chasing callers. Paths that are
Claude Code's own native root stay spelled `~/.claude` on purpose; each such
spelling is either a native-root path (NATIVE) or a reviewed line (ALLOWED).

Every home-rooted spelling counts: `~/`, `$HOME/`, `${HOME}/`, systemd `%h/`
and an absolute `/home/<user>/` prefix. A guard wired to one spelling is not a
guard.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parent.parent

# Where live wiring lives: scripts, hooks, adapters, settings, units, skills.
SCOPES = ("scripts", "bin", "hooks", "adapters", "systemd", "skills", "settings.shared.json")

LITERAL = re.compile(r"(?:~|\$HOME|\$\{HOME\}|%h|/home/[A-Za-z0-9_.-]+)/\.claude(?![\w.-])(\S*)")
# The pathlib spelling: Path.home() / ".claude" [/ "segment"].
PY_LITERAL = re.compile(r"""home\(\)\s*/\s*["']\.claude["'](?:\s*/\s*["']([\w.-]+)["'])?""")

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
    ("adapters/README.md", "the harness repository *is* `$HOME/.claude`",
     "describes where the checkout sits until 0986"),
    ("adapters/README.md", "| Claude Code | `$HOME/.claude/skills` |",
     "Claude Code's personal-skills scan root"),
    ("adapters/README.md", "For the planned `~/.claude` → `~/.idh` move",
     "names the move itself"),
    ("adapters/claude-code/README.md", "the harness repository *is* `~/.claude`",
     "plugin discovery happens under Claude Code's native skills root"),
    ("adapters/claude-code/README.md", "a plugin under `$HOME/.claude/skills/<name>/`",
     "measured Claude Code plugin discovery path"),
    ("adapters/perch.py", "installation the harness repository *is* ``$HOME/.claude``",
     "Claude Code's personal-skills scan root; the checkout still sits there until 0986"),
    ("adapters/perch.py", "``$HOME/.claude/skills/perch`` and the canonical source",
     "Claude Code's personal-skills scan root"),
    ("adapters/perch.py", "``$HOME/.claude`` is that harness's",
     "Claude Code's personal-skills scan root"),
    ("adapters/perch.py", 'return _home() / ".claude" / "skills" / skill',
     "Claude Code's personal-skills scan root"),
    ("adapters/pilot-support.json", '"skills_root": "$HOME/.claude/skills"',
     "Claude Code's personal-skills scan root"),
    ("adapters/pilot-support.json", "the harness checkout is $HOME/.claude",
     "states where Claude Code scans skills; true until 0986"),
    ("adapters/pilot-support.json", '"native_expression": "$HOME/.claude/skills/perch',
     "Claude Code's native expression of the skill"),
    ("adapters/pilot-support.json", "personal skills live in ~/.claude/skills/",
     "quotes Claude Code's documentation"),
    ("scripts/adapter-claude-code-activate.sh", "repository *is* ~/.claude",
     "plugin discovery happens under Claude Code's native skills root"),
    ("scripts/probe-plugin-hook-loading.sh", "a plugin at $HOME/.claude/skills/",
     "probes Claude Code's native plugin discovery"),
    ("scripts/on-start.sh", "`~/.claude/rules/**.md` into the system prompt",
     "the runtime loads rules from its native root"),
    ("settings.shared.json", '"Edit(~/.claude/skills/hunt/**)"',
     "transition alias: sessions still reach the checkout as ~/.claude until 0986"),
    ("settings.shared.json", '"Edit(~/.claude/tickets/*.erg)"',
     "transition alias until 0986"),
    ("settings.shared.json", '"Write(~/.claude/tickets/*.erg)"',
     "transition alias until 0986"),
    ("settings.shared.json", '"Bash(~/.claude/skills/merge/erg-pr-merge:*)"',
     "transition alias until 0986"),
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
    ],
)
def test_native_root_and_idh_spellings_pass(tmp_path, native):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "ok.sh").write_text(native + "\n")
    assert offending_literals(tmp_path, allowed=[]) == []
