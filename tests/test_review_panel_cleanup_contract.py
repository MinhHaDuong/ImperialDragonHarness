"""Ticket 0948: review scratch has one owner and a bounded lifetime.

Ticket 1227 moved the cleanup recipe from cleanup.md into scripts/gaze_close.py;
the pins moved with it (behaviour is exercised by tests/test_gaze_close.py).
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gaze_owns_delegated_panel_cleanup_on_every_exit():
    text = (ROOT / "skills/gaze/SKILL.md").read_text()
    cleanup = text.split("## Review scratch cleanup", 1)[1].split("\n## ", 1)[0]
    assert "every exit path" in cleanup.lower()
    assert "after" in cleanup.lower() and "consumed" in cleanup.lower()
    assert "circuit-breaker" in cleanup.lower()
    assert "gaze_close.py" in cleanup
    assert "leave the review worktree" in " ".join(cleanup.lower().split())
    assert "--force" not in cleanup.replace("never `--force`", "")


def test_gaze_close_script_keeps_the_cleanup_order():
    src = (ROOT / "scripts/gaze_close.py").read_text()
    assert src.index('"worktree-tmp-guard.py"') < src.index('tree / ".panel" / str(pr)')
    assert '"build" / "panel-head"' in src
    assert '"worktree-exit-preflight.sh"' in src and '"--removal"' in src
    assert src.index("worktree-exit-preflight.sh") < src.index('"worktree", "remove"')
    assert '"--force"' not in src
