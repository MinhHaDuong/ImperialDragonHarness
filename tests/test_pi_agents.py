"""Pi renderings of the harness agents and their install projection (ticket 1426).

Pi's subagent extension discovers user agents in ``~/.pi/agent/agents`` and
passes the frontmatter ``tools:`` to the child as ``--tools a,b``. Pi matches
tool names case-sensitively against its registry and drops unknown ones
without a word, so a Claude grant (``Read, Grep``) launches a child with no
tools at all. The renderings under adapters/pi/agents/ are generated from
agents/*.md by scripts/render-pi-agents.py; these tests pin the generated
files to the generator, the ``--tools`` value to Pi tool names, and the
install to a Pi agent directory where ``gate-seat`` resolves.
"""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("render_pi_agents", REPO / "scripts" / "render-pi-agents.py")
render = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render)

PI_DIR = REPO / "adapters" / "pi" / "agents"
SOURCES = sorted((REPO / "agents").glob("*.md"))

# Pi 1.4.0 built-in tools (dist/core/tools/index.js allToolNames, minus
# powershell) plus the subagent extension's own tool.
PI_TOOLS = {"read", "bash", "edit", "write", "grep", "find", "ls", "subagent"}


def _frontmatter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def _pi_tools_flag(path: Path) -> str:
    """The --tools value the subagent extension builds (agents.ts parseToolList, index.ts join)."""
    value = _frontmatter(path).get("tools")
    raw = value if isinstance(value, list) else value.split(",") if isinstance(value, str) else []
    return ",".join(t.strip() for t in raw if isinstance(t, str) and t.strip())


def test_every_agent_has_a_pi_rendering_and_nothing_else_lives_there():
    assert sorted(p.name for p in PI_DIR.glob("*.md")) == [p.name for p in SOURCES]


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.stem)
def test_committed_rendering_is_the_generator_output(source):
    assert (PI_DIR / source.name).read_text(encoding="utf-8") == render.render(source), (
        f"adapters/pi/agents/{source.name} drifted: run scripts/render-pi-agents.py"
    )


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.stem)
def test_pi_child_gets_the_intended_tools(source):
    flag = _pi_tools_flag(PI_DIR / source.name)
    assert flag, f"{source.name}: Pi child would launch with Pi's default tools, not the grant"
    tools = flag.split(",")
    assert set(tools) <= PI_TOOLS, f"{source.name}: --tools {flag} names tools Pi drops silently"
    claude = _frontmatter(source).get("tools")
    expected = render.pi_tools(claude)
    assert tools == expected


def test_tool_map_examples():
    assert render.pi_tools("Read, Grep, Glob, Bash, Write") == ["read", "grep", "find", "ls", "bash", "write"]
    # Skill has no Pi tool: Pi lists skills in the system prompt and the child reads SKILL.md.
    assert render.pi_tools("Read, Grep, Glob, Bash, Write, Edit, Skill, Agent") == [
        "read", "grep", "find", "ls", "bash", "write", "edit", "subagent"]
    # No tools: line on Claude means every tool; on Pi it would mean Pi's default set.
    assert render.pi_tools(None) == ["read", "grep", "find", "ls", "bash", "edit", "write", "subagent"]
    with pytest.raises(ValueError):
        render.pi_tools("Read, WebFetch")


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.stem)
def test_rendering_carries_name_description_body_and_no_model(source):
    fm, src = _frontmatter(PI_DIR / source.name), _frontmatter(source)
    assert fm["name"] == src["name"] and fm["description"] == src["description"]
    # No model pin: a projected pin names a provider the host may lack (the
    # arena's sealed HOME); unpinned, the child inherits the dispatcher's model.
    assert "model" not in fm
    assert (PI_DIR / source.name).read_text(encoding="utf-8").endswith(source.read_text(encoding="utf-8").split("---", 2)[2].lstrip("\n"))


def test_manifest_projects_the_pi_renderings():
    entries = json.loads((REPO / "adapters" / "projections.json").read_text())["entries"]
    entry = next(e for e in entries if e["path"] == "~/.pi/agent/agents")
    assert entry["target"] == "$IDH_ROOT/adapters/pi/agents"
    assert entry["runtimes"] == ["pi"] and entry["children"] == "markdown" and entry["required"] is True


@pytest.mark.integration
def test_install_in_a_temp_home_lets_pi_resolve_gate_seat(tmp_path):
    home = tmp_path / "home"
    (home / ".pi" / "agent" / "agents").mkdir(parents=True)
    user_agent = home / ".pi" / "agent" / "agents" / "scout.md"
    user_agent.write_text("---\nname: scout\ndescription: user agent\n---\n")
    env = {**os.environ, "HOME": str(home), "XDG_STATE_HOME": str(tmp_path / "state")}
    env.pop("IDH_ROOT", None)
    subprocess.run([str(REPO / "bin" / "idh"), "install"], env=env, capture_output=True, text=True, timeout=120)
    agents_dir = home / ".pi" / "agent" / "agents"
    names = {}
    for entry in os.scandir(agents_dir):  # agents.ts loadAgentsFromDir: *.md, file or symlink
        if entry.name.endswith(".md") and (entry.is_file() or entry.is_symlink()):
            fm = _frontmatter(Path(entry.path))
            names[fm["name"]] = Path(entry.path)
    assert {p.stem for p in SOURCES} | {"scout"} <= set(names), sorted(names)
    assert user_agent.read_text().startswith("---\nname: scout"), "a user agent must survive install"
    assert names["gate-seat"].resolve() == (PI_DIR / "gate-seat.md").resolve()
    assert _pi_tools_flag(names["gate-seat"]) == "read,grep,find,ls,bash,write"
