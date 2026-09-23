"""SessionStart asks for a coherence pass only when local directives exist."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]


def start(project: Path, home: Path) -> str:
    env = os.environ.copy()
    env.update(CLAUDE_PROJECT_DIR=str(project), HOME=str(home), BASH_ENV="")
    return subprocess.check_output(
        ["bash", str(ROOT / "scripts/on-start.sh")],
        env=env,
        text=True,
        stderr=subprocess.DEVNULL,
    )


def test_startup_prompt_tracks_local_directive_sources(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    assert "PROJECT DIRECTIVE COHERENCE" not in start(project, tmp_path)

    (project / "AGENTS.md").write_text("# Local instructions\n")
    skill = project / ".claude/skills/example/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Example\n")
    output = start(project, tmp_path)
    assert "PROJECT DIRECTIVE COHERENCE" in output
    assert "AGENTS.md, .claude/skills/" in output
    assert "conflicting instructions, repeated procedures, and stale references" in output
    assert "A startup coherence pass is due after worktree entry" in output


def test_empty_skill_directory_does_not_prompt(tmp_path):
    project = tmp_path / "project"
    (project / ".claude/skills").mkdir(parents=True)
    assert "PROJECT DIRECTIVE COHERENCE" not in start(project, tmp_path)


def test_harness_worktree_does_not_prompt(tmp_path):
    harness = tmp_path / "harness"
    scripts = harness / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/prompt-project-coherence.sh", scripts)
    (harness / "CLAUDE.md").write_text("# Harness instructions\n")
    subprocess.run(["git", "init", "-b", "main", str(harness)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(harness), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(harness), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(harness), "add", "."], check=True)
    subprocess.run(["git", "-C", str(harness), "commit", "-m", "fixture"], check=True, capture_output=True)
    linked = tmp_path / "linked"
    subprocess.run(["git", "-C", str(harness), "worktree", "add", "-b", "linked", str(linked)], check=True, capture_output=True)
    result = subprocess.run(["bash", str(scripts / "prompt-project-coherence.sh"), str(linked)],
                            check=True, capture_output=True, text=True)
    assert result.stdout == ""
