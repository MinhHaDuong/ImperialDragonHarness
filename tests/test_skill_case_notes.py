"""Skill case notes hook (ticket 1394, stage 1).

PostToolUse on Skill pushes `memory/skills/<skill>.md` of the project into the
model's context once per session and agent. Every outcome is logged, so "no
note" and "hook never fired" stay distinguishable.
"""

import json
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "skill-case-notes.sh"
TOKEN = "PLANTED-TOKEN-7731"


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    (root / "memory" / "skills").mkdir(parents=True)
    (root / "memory" / "skills" / "merge.md").write_text(f"# merge cases\n{TOKEN}\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=child_env())
    return root


@pytest.fixture
def state(tmp_path):
    return tmp_path / "state"


def run(state, cwd, skill="merge", session="s1", agent=None, raw=None):
    payload = raw
    if payload is None:
        payload = {"session_id": session, "cwd": str(cwd), "tool_name": "Skill",
                   "tool_input": {} if skill is None else {"skill": skill}}
        if agent:
            payload["agent_id"] = agent
        payload = json.dumps(payload)
    env = {**child_env(), "XDG_STATE_HOME": str(state)}
    r = subprocess.run([str(SCRIPT)], input=payload, capture_output=True, text=True, env=env)
    log = state / "idh" / "skill-notes" / "log"
    return r, (log.read_text() if log.exists() else "")


def typed(state, cwd, prompt, session="s1", agent=None):
    payload = {"session_id": session, "cwd": str(cwd), "hook_event_name": "UserPromptSubmit",
               "prompt": prompt}
    if agent:
        payload["agent_id"] = agent
    return run(state, cwd, raw=json.dumps(payload))


def context(r):
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def test_delivers_note_as_additional_context(project, state):
    r, log = run(state, project)
    assert r.returncode == 0
    out = json.loads(r.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PostToolUse"
    assert out["additionalContext"].startswith("Case notes for skill merge")
    assert TOKEN in out["additionalContext"]
    assert "delivered" in log


def test_second_load_in_same_context_is_silent(project, state):
    run(state, project)
    r, log = run(state, project)
    assert r.returncode == 0 and r.stdout == ""
    assert "already-delivered" in log


def test_subagent_gets_its_own_delivery(project, state):
    run(state, project)
    r, _ = run(state, project, agent="a1")
    assert TOKEN in context(r)
    r, _ = run(state, project, agent="a1")
    assert r.stdout == ""


def test_other_session_gets_delivery(project, state):
    run(state, project)
    r, _ = run(state, project, session="s2")
    assert TOKEN in context(r)


def test_no_note_is_logged_and_silent(project, state):
    r, log = run(state, project, skill="gaze")
    assert r.returncode == 0 and r.stdout == ""
    assert "no-note" in log


def test_bad_name_is_refused(project, state):
    (project / "memory" / "x.md").write_text(TOKEN)
    r, log = run(state, project, skill="../x")
    assert r.returncode == 0 and r.stdout == ""
    assert "bad-name" in log


def test_plugin_prefix_is_stripped(project, state):
    r, _ = run(state, project, skill="idh:merge")
    assert TOKEN in context(r)


def test_missing_skill_name_is_logged(project, state):
    r, log = run(state, project, skill=None)
    assert r.returncode == 0 and r.stdout == ""
    assert "no-skill-name" in log


def test_garbage_stdin_fails_open(state):
    r, log = run(state, Path("/"), raw="not json{")
    assert r.returncode == 0 and r.stdout == ""
    assert "parse-error" in log


def test_subdirectory_cwd_finds_project_root(project, state):
    sub = project / "a" / "b"
    sub.mkdir(parents=True)
    r, _ = run(state, sub)
    assert TOKEN in context(r)


def test_cwd_outside_a_repository_is_a_no_note(tmp_path, state):
    r, log = run(state, tmp_path)
    assert r.returncode == 0 and r.stdout == ""
    assert "no-note" in log


def test_note_is_capped(project, state):
    (project / "memory" / "skills" / "merge.md").write_text("word " * 1000)
    r, _ = run(state, project)
    assert len(context(r).split()) <= 450


def test_typed_slash_command_delivers(project, state):
    r, log = typed(state, project, "/merge 2114 now")
    out = json.loads(r.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "UserPromptSubmit"
    assert TOKEN in out["additionalContext"]
    assert "delivered skill=merge" in log


def test_typed_then_skill_tool_delivers_once(project, state):
    r1, _ = typed(state, project, "/merge")
    r2, log = run(state, project)
    assert TOKEN in context(r1) and r2.stdout == ""
    assert "already-delivered" in log


def test_skill_tool_then_typed_delivers_once(project, state):
    run(state, project)
    r, _ = typed(state, project, "/idh:merge")
    assert r.stdout == ""


def test_typed_unknown_command_is_no_note(project, state):
    r, log = typed(state, project, "/help")
    assert r.stdout == "" and "no-note skill=help" in log


def test_non_slash_prompt_is_silent_and_unlogged(project, state):
    r, log = typed(state, project, "please /merge this")
    assert r.returncode == 0 and r.stdout == "" and log == ""


def test_hooks_json_wires_prompt_submit():
    hooks = json.loads((REPO / "adapters" / "claude-code" / "hooks" / "hooks.json").read_text())["hooks"]
    cmd = hooks["UserPromptSubmit"][0]["hooks"][0]
    assert "idh-hook\" skill-case-notes.sh" in cmd["command"]
    assert cmd["timeout"] == 5


def test_hooks_json_wires_skill_matcher():
    hooks = json.loads((REPO / "adapters" / "claude-code" / "hooks" / "hooks.json").read_text())["hooks"]
    blocks = hooks["PostToolUse"]
    assert [b["matcher"] for b in blocks] == ["Skill"]
    cmd = blocks[0]["hooks"][0]
    assert "idh-hook\" skill-case-notes.sh" in cmd["command"]
    assert cmd["timeout"] == 5


# Codex shapes (ticket 1404): no Skill tool, so a skill load is a shell read of
# skills/<name>/SKILL.md (PostToolUse, tool_name Bash) or a typed `$name`.
def codex_bash(state, cwd, command, session="c1"):
    payload = {"session_id": session, "turn_id": "t1", "cwd": str(cwd),
               "hook_event_name": "PostToolUse", "tool_name": "Bash",
               "tool_input": {"command": command}, "tool_response": "x"}
    return run(state, cwd, raw=json.dumps(payload, separators=(",", ":")))


def codex_prompt(state, cwd, prompt, session="c1", turn=True):
    payload = {"session_id": session, "cwd": str(cwd), "hook_event_name": "UserPromptSubmit",
               "prompt": prompt}
    if turn:
        payload["turn_id"] = "t1"
    return run(state, cwd, raw=json.dumps(payload, separators=(",", ":")))


def test_codex_shell_read_of_skill_file_delivers(project, state):
    r, log = codex_bash(state, project, "cat /home/u/.codex/skills/merge/SKILL.md")
    out = json.loads(r.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PostToolUse" and TOKEN in out["additionalContext"]
    assert "delivered skill=merge" in log


def test_codex_sed_read_and_relative_path_deliver(project, state):
    r, _ = codex_bash(state, project, "sed -n '1,200p' skills/merge/SKILL.md")
    assert TOKEN in context(r)


def test_codex_unrelated_shell_command_is_silent_and_unlogged(project, state):
    r, log = codex_bash(state, project, "git status --short")
    assert r.returncode == 0 and r.stdout == "" and log == ""


def test_codex_non_read_mention_of_skill_file_is_silent(project, state):
    r, log = codex_bash(state, project, "git add skills/merge/SKILL.md")
    assert r.stdout == "" and log == ""


def test_codex_dollar_prompt_delivers_once_with_shell_read(project, state):
    r1, _ = codex_prompt(state, project, "$merge 2114")
    assert json.loads(r1.stdout)["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert TOKEN in context(r1)
    r2, log = codex_bash(state, project, "cat skills/merge/SKILL.md")
    assert r2.stdout == "" and "already-delivered" in log


def test_dollar_prompt_without_codex_turn_is_ignored(project, state):
    r, log = codex_prompt(state, project, "$merge", turn=False)
    assert r.stdout == "" and log == ""


def test_codex_hooks_json_wires_prompt_and_shell_read():
    hooks = json.loads((REPO / "adapters" / "codex" / "hooks.json").read_text())["hooks"]
    for event in ("UserPromptSubmit", "PostToolUse"):
        cmds = [h["command"] for b in hooks[event] for h in b["hooks"]]
        assert any("skill-case-notes.sh" in c for c in cmds), event
    assert {b["matcher"] for b in hooks["PostToolUse"]} == {"^Bash$"}


def test_pi_extension_wires_case_notes_on_skill_read():
    """Ticket 1405: Pi has no Skill tool; the idh-guard extension feeds the same
    script on a read of skills/<name>/SKILL.md and appends the note to the result."""
    src = (REPO / "adapters" / "pi" / "extensions" / "idh-guard.ts").read_text()
    assert 'pi.on("tool_result"' in src
    assert 'event.toolName === "read"' in src
    assert "skill-case-notes.sh" in src
    assert "tool_input: { skill:" in src
    assert "SKILL" in src and "additionalContext" in src
