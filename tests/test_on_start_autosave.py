"""Session start reports VS Code autosave being off (author ruling, 2026-11-01).

Agents edit files the author may have open in the primary checkout; an unsaved
editor buffer is invisible to them. `scripts/on-start-context.sh` prints one
declarative line when VS Code's user settings exist and set no `files.autoSave`
mode other than `off`. It stays silent when VS Code is absent or autosave is on.
"""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "on-start-context.sh"
MARK = "VS Code autosave is off"


def run(tmp_path: Path, settings: str | None) -> str:
    home = tmp_path / "home"
    home.mkdir()
    if settings is not None:
        user = home / ".config" / "Code" / "User"
        user.mkdir(parents=True)
        (user / "settings.json").write_text(settings)
    env = child_env()
    env["HOME"] = str(home)
    env.pop("XDG_CONFIG_HOME", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run(
        ["bash", str(SCRIPT)], cwd=tmp_path, env=env,
        capture_output=True, text=True, input="{}",
    )
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.mark.parametrize("settings", [
    '{\n  "editor.fontSize": 14\n}\n',
    '{ "files.autoSave": "off" }',
])
def test_line_when_autosave_off(tmp_path, settings):
    out = run(tmp_path, settings)
    assert MARK in out
    assert '"files.autoSave": "afterDelay"' in out
    assert "offers once to set it" in out


@pytest.mark.parametrize("mode", ["afterDelay", "onFocusChange", "onWindowChange"])
def test_silent_when_autosave_on(tmp_path, mode):
    assert MARK not in run(tmp_path, '{\n  "files.autoSave" : "%s"\n}\n' % mode)


def test_silent_without_vscode(tmp_path):
    assert MARK not in run(tmp_path, None)
