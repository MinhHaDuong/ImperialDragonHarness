"""Pin: verify-gate never blocks a comment-only edit on scope or authorisation (ticket 1126).

Worked example: a `%`-comment edit under a protected path (rapport/) yields no
blocker, recorded as `nofollow:`; a typeset-sentence edit stays guarded.
"""

import re
from pathlib import Path

import pytest

GATE = (Path(__file__).resolve().parent.parent / "skills" / "verify-gate" / "SKILL.md").read_text()


def _section() -> str:
    m = re.search(r"\*\*Comment-only hunks never block\.\*\*.*?(?:\n\n|\Z)", GATE, re.S)
    assert m, "verify-gate lacks the comment-only exemption in Scope containment"
    return " ".join(m.group(0).split())


@pytest.mark.adherence
def test_comment_only_hunk_is_nonblocking_nofollow():
    t = _section()
    assert "LaTeX `%`" in t and "never a scope or authorisation blocker" in t
    assert "protected" in t and "`nofollow:`" in t
    assert "no `scope_overflow` entry" in t


@pytest.mark.adherence
def test_no_self_granted_pr_body_exception():
    assert "caller states in the PR body" not in GATE


@pytest.mark.adherence
def test_typeset_text_stays_guarded():
    t = _section()
    assert "Typeset text and argument changes keep the guard" in t


@pytest.mark.adherence
def test_exemption_sits_in_scope_containment():
    i = GATE.index("## Scope containment")
    assert i < GATE.index("Comment-only hunks never block") < GATE.index("## Verdict shape")
