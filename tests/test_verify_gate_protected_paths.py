"""verify-gate scope containment: protected paths bind comment-only hunks too (ticket 1408)."""

import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "verify-gate" / "SKILL.md"


def _scope_section() -> str:
    text = SKILL.read_text()
    m = re.search(r"^## Scope containment\n(.*?)(?=^## )", text, re.S | re.M)
    assert m, "Scope containment section missing"
    return re.sub(r"\s+", " ", m.group(1))


def test_comment_leniency_has_no_protected_path_carve_out():
    body = _scope_section()
    assert "even under a path the brief marked protected" not in body


def test_protected_path_hunk_is_scope_overflow_whatever_its_kind():
    body = _scope_section()
    assert "path the brief marked protected" in body
    assert "`scope_overflow` entry whatever its kind, comments included" in body


def test_comment_leniency_applies_only_inside_authorised_scope():
    body = _scope_section()
    assert "inside authorised scope" in body
    assert "inside authorised scope is never" in body


def test_protected_path_disposition_is_escalate_and_author_exception_authorises():
    body = _scope_section()
    assert "suggested disposition is ESCALATE" in body
    assert "makes that path authorised scope" in body


def test_exception_comes_from_brief_or_author_forge_comment_never_the_pr_body():
    body = _scope_section()
    assert "PR body" not in body
    assert "commit message" in body
    assert "author's own login" in body


def test_comment_leniency_wording_is_authorised_scope_only():
    body = _scope_section()
    assert "did not protect" not in body
