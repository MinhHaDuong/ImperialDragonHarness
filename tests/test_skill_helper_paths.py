"""Skill helpers resolve from the loaded skill, even through a projection."""

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
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
