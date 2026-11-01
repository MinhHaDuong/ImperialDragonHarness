"""Conditional rules on Codex and Pi (ticket 1424).

Claude Code loads a rule whose frontmatter declares `paths:` when the session
touches a matching file. Codex and Pi do not: `scripts/conditional_rules.py`
does it for them, from the payload the Codex PostToolUse hook or the Pi
extension hands it, once per session and rule, comments stripped.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "conditional_rules.py"
sys.path.insert(0, str(REPO / "scripts"))

PY_TOKEN = "PY-RULE-TOKEN-4410"
STATE_TOKEN = "STATE-RULE-TOKEN-9921"
COMMENT_TOKEN = "COMMENT-TOKEN-5150"


def _module():
    import conditional_rules  # noqa: PLC0415  (absent until implemented)

    return conditional_rules


@pytest.mark.parametrize(
    "glob,path,expected",
    [
        ("**/*.py", "a.py", True),
        ("**/*.py", "src/pkg/a.py", True),
        ("**/*.py", "a.pyc", False),
        ("**/*.py", "a.py/readme.txt", False),
        ("STATE.md", "STATE.md", True),
        ("STATE.md", "sub/STATE.md", False),
        ("rules/**", "rules/lang/fr.md", True),
        ("rules/**", "myrules/a.md", False),
        ("**/rules/**", "x/rules/a.md", True),
        ("**/docs/**", "docs/a.txt", True),
        ("**/docs/**", "a/docs/b/c.pdf", True),
        ("**/docs/**", "a/docsx/c.pdf", False),
        ("**/tests/**/*.py", "tests/test_a.py", True),
        ("**/test_*.py", "pkg/test_a.py", True),
        ("**/test_*.py", "pkg/atest_a.py", False),
        ("**/_quarto.y{a,}ml", "_quarto.yml", True),
        ("**/*.latexmkrc", "paper/.latexmkrc", True),
    ],
)
def test_glob_semantics_follow_claude_paths(glob, path, expected):
    assert _module().glob_matches(glob, path) is expected


def test_real_index_holds_conditional_rules_only():
    index = dict(_module().rule_index(REPO / "rules"))
    assert index.get("coding-python.md") == ["**/*.py"]
    assert "lang/fr.md" in index and "state.md" in index
    for resident in ("git.md", "guards.md", "workflow.md", "claude-code.md"):
        assert resident not in index


# --- the hook, end to end --------------------------------------------------


@pytest.fixture
def rules(tmp_path):
    d = tmp_path / "rules"
    (d / "lang").mkdir(parents=True)
    (d / "coding-python.md").write_text(
        '---\npaths:\n  - "**/*.py"\nlast-reviewed: 2026-11-01\n---\n'
        f"# Python\n<!-- {COMMENT_TOKEN} -->\n{PY_TOKEN}\n"
    )
    (d / "state.md").write_text(f'---\npaths:\n  - "STATE.md"\n---\n# State\n{STATE_TOKEN}\n')
    (d / "git.md").write_text("# Git, resident: no paths\nRESIDENT-TOKEN\n")
    return d


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text("x = 1\n")
    (root / "STATE.md").write_text("# state\n")
    (root / "notes.txt").write_text("hello\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=child_env())
    return root


def hook(tmp_path, rules, payload):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    env = {**child_env(), "XDG_STATE_HOME": str(tmp_path / "state"), "IDH_RULES_DIR": str(rules)}
    return subprocess.run([sys.executable, str(SCRIPT)], input=raw, capture_output=True,
                          text=True, env=env, timeout=30)


def bash(cwd, command, session="s1"):
    return {"hook_event_name": "PostToolUse", "session_id": session, "cwd": str(cwd),
            "tool_name": "Bash", "tool_input": {"command": command}, "turn_id": "t1"}


def context(r):
    assert r.returncode == 0, r.stderr
    assert r.stdout, "expected a rule to be injected"
    out = json.loads(r.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PostToolUse"
    return out["additionalContext"]


@pytest.mark.integration
def test_shell_read_of_matching_file_injects_rule(tmp_path, rules, project):
    ctx = context(hook(tmp_path, rules, bash(project, "cat src/a.py")))
    assert PY_TOKEN in ctx
    assert "coding-python.md" in ctx and "src/a.py" in ctx
    assert STATE_TOKEN not in ctx and "RESIDENT-TOKEN" not in ctx


@pytest.mark.integration
def test_comments_and_frontmatter_are_stripped(tmp_path, rules, project):
    ctx = context(hook(tmp_path, rules, bash(project, "sed -n 1,5p src/a.py")))
    assert COMMENT_TOKEN not in ctx and "<!--" not in ctx
    assert "last-reviewed" not in ctx


@pytest.mark.integration
def test_once_per_session_per_rule(tmp_path, rules, project):
    context(hook(tmp_path, rules, bash(project, "cat src/a.py")))
    again = hook(tmp_path, rules, bash(project, "head src/a.py"))
    assert again.returncode == 0 and again.stdout == ""
    # another rule in the same session still arrives, and only that one
    ctx = context(hook(tmp_path, rules, bash(project, "cat src/a.py STATE.md")))
    assert STATE_TOKEN in ctx and PY_TOKEN not in ctx
    # a new session gets the first rule again
    assert PY_TOKEN in context(hook(tmp_path, rules, bash(project, "cat src/a.py", session="s2")))


@pytest.mark.integration
def test_each_agent_of_a_session_gets_its_own_delivery(tmp_path, rules, project):
    context(hook(tmp_path, rules, bash(project, "cat src/a.py")))
    sub = {**bash(project, "cat src/a.py"), "agent_id": "sub1"}
    assert PY_TOKEN in context(hook(tmp_path, rules, sub))


@pytest.mark.integration
def test_no_match_gives_no_output(tmp_path, rules, project):
    r = hook(tmp_path, rules, bash(project, "cat notes.txt"))
    assert r.returncode == 0 and r.stdout == ""


@pytest.mark.integration
def test_a_glob_that_names_no_file_does_not_match(tmp_path, rules, project):
    r = hook(tmp_path, rules, bash(project, "rg -g '*.py' needle missing.py"))
    assert r.returncode == 0 and r.stdout == ""


@pytest.mark.integration
def test_pi_tool_path_shape_matches(tmp_path, rules, project):
    payload = {"hook_event_name": "PostToolUse", "session_id": "pi1", "cwd": str(project),
               "tool_name": "edit", "tool_input": {"path": "src/a.py"}}
    assert PY_TOKEN in context(hook(tmp_path, rules, payload))


@pytest.mark.integration
def test_patch_headers_in_a_shell_command_match(tmp_path, rules, project):
    cmd = "apply_patch <<'EOF'\n*** Begin Patch\n*** Update File: src/a.py\n@@\n-x = 1\n+x = 2\n*** End Patch\nEOF"
    assert PY_TOKEN in context(hook(tmp_path, rules, bash(project, cmd)))


@pytest.mark.integration
@pytest.mark.parametrize(
    "raw",
    ["", "not json", "[1, 2]", '{"session_id": "s1"}',
     '{"session_id": "../evil", "cwd": "/", "tool_input": {"command": "cat /etc/hostname"}}',
     '{"tool_input": {"command": 7}, "session_id": "s1"}'],
)
def test_fails_open_on_bad_input(tmp_path, rules, raw):
    r = hook(tmp_path, rules, raw)
    assert r.returncode == 0 and r.stdout == ""


@pytest.mark.integration
def test_fails_open_on_missing_rules_dir(tmp_path, project):
    r = hook(tmp_path, tmp_path / "no-such-rules", bash(project, "cat src/a.py"))
    assert r.returncode == 0 and r.stdout == ""


# --- wiring ------------------------------------------------------------------

SOFT = '[ -x "$HOME/.local/bin/idh-hook" ] || exit 0; exec "$HOME/.local/bin/idh-hook" conditional_rules.py'


def test_codex_wires_post_tool_use_on_shell_calls():
    doc = json.loads((REPO / "adapters" / "codex" / "hooks.json").read_text())
    blocks = doc["hooks"]["PostToolUse"]
    wired = [b["matcher"] for b in blocks for h in b["hooks"] if h["command"] == SOFT]
    assert wired == ["^Bash$"]
    # the case-notes entry keeps index 0, so its recorded trust hash survives
    assert "skill-case-notes.sh" in blocks[0]["hooks"][0]["command"]


def test_pi_extension_feeds_read_write_edit_and_bash():
    src = (REPO / "adapters" / "pi" / "extensions" / "idh-guard.ts").read_text()
    assert "conditional_rules.py" in src
    for tool in ("read", "write", "edit", "bash"):
        assert f'"{tool}"' in src
