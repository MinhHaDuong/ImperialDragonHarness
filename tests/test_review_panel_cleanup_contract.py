"""Ticket 0948: review scratch has one owner and a bounded lifetime.

Ticket 1227 moved the cleanup recipe from cleanup.md into scripts/gaze_close.py;
the pins moved with it (behaviour is exercised by tests/test_gaze_close.py).
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gaze_close_script_keeps_the_cleanup_order():
    src = (ROOT / "scripts/gaze_close.py").read_text()
    assert src.index('"worktree-tmp-guard.py"') < src.index('tree / ".panel" / key')
    assert '"build" / "panel-head"' in src
    assert '"worktree-exit-preflight.sh"' in src and '"--removal"' in src
    assert src.index("worktree-exit-preflight.sh") < src.index('"worktree", "remove"')
    assert '"--force"' not in src
