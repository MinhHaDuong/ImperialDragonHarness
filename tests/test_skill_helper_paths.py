"""Skill helpers resolve from the loaded skill, even through a projection."""

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
OLD_HELPER = re.compile(
    r"~/.claude/(?:skills|scripts)/|\$\{IDH_HOME:-\$HOME/\.claude\}/(?:skills|scripts)/"
    r"|\$\{?HOME\}?/\.claude/(?:skills|scripts)/"
)


def test_skill_bodies_use_the_loaded_skill_for_helper_paths():
    exceptions = {
        "merge": "~/.claude/skills/merge/erg-pr-merge",
        "raid": "~/.claude/skills/merge/erg-pr-merge",
    }
    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        body = skill.read_text()
        old = OLD_HELPER.findall(body)
        if skill.parent.name in exceptions:
            assert len(old) == 1, skill
            assert exceptions[skill.parent.name] in body
            assert "harness-extension-point" in body
        else:
            assert not old, skill
        if "$IDH_ROOT/" in body and skill.parent.name != "roar":
            assert 'IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"' in body, skill


@pytest.mark.integration
def test_loaded_skill_root_survives_a_symlink_and_spaces(tmp_path):
    projected = tmp_path / "profile with spaces" / ".agents" / "skills" / "roar"
    projected.parent.mkdir(parents=True)
    projected.symlink_to(SKILLS / "roar", target_is_directory=True)
    script = 'IDH_ROOT="$(cd -P "$(dirname "$1")/../.." && pwd -P)"; printf "%s\\n%s\\n" "$IDH_ROOT" "$PWD"'
    result = subprocess.run(
        ["bash", "-c", script, "bash", str(projected / "SKILL.md")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines() == [str(REPO), str(tmp_path)]
