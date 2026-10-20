"""STATE.md must respect the hard line cap stated in ``rules/state.md``.

The limit is parsed from the rule text ('Hard cap: **40 lines total**'), so the
rule and the test cannot drift: one number, one home. The simpler robust
direction is rule -> test, since the test already has to read the rule.

Positive controls: the parse fails loudly if the rule sentence moves, and the
STATE.md check fails if the file is missing or near-empty, so an all-clear is
never "the file was not found". ``test_check_fires_over_cap`` shows the check
can fail.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
MIN_LINES = 5


def line_cap() -> int:
    text = (REPO / "rules" / "state.md").read_text(encoding="utf-8")
    match = re.search(r"Hard cap: \*\*(\d+) lines total\*\*", text)
    assert match, "rules/state.md lost its 'Hard cap: **N lines total**' sentence"
    return int(match.group(1))


def over_cap(path: Path, cap: int) -> int | None:
    """Return the line count if ``path`` exceeds ``cap``, else None."""
    assert path.is_file(), f"{path} not found: cannot certify the cap"
    count = len(path.read_text(encoding="utf-8").splitlines())
    assert count >= MIN_LINES, f"{path} has {count} lines: census could not look"
    return count if count > cap else None


def test_state_within_cap():
    cap = line_cap()
    count = over_cap(REPO / "STATE.md", cap)
    assert count is None, f"STATE.md has {count} lines, cap is {cap} (rules/state.md)"


def test_check_fires_over_cap(tmp_path):
    cap = line_cap()
    fixture = tmp_path / "STATE.md"
    fixture.write_text("line\n" * (cap + 1), encoding="utf-8")
    assert over_cap(fixture, cap) == cap + 1
    fixture.write_text("line\n" * cap, encoding="utf-8")
    assert over_cap(fixture, cap) is None


def test_check_rejects_missing_or_tiny(tmp_path):
    with pytest.raises(AssertionError):
        over_cap(tmp_path / "absent.md", 40)
    tiny = tmp_path / "tiny.md"
    tiny.write_text("x\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        over_cap(tiny, 40)
