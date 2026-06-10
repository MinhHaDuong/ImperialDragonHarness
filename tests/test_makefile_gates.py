"""Hygiene: Makefile gate targets match the coding-python.md definitions.

`check` is the pre-PR gate: full pytest suite (integration + slow included)
plus the static checks. `check-fast` is the development gate: unit tests only.
Source inspection, not subprocess (ticket 0238).
"""

import re
from pathlib import Path

MAKEFILE = Path(__file__).parent.parent / "Makefile"


def target_recipe(name: str) -> str:
    """Return the full rule (deps line + recipe) for a Makefile target."""
    text = MAKEFILE.read_text()
    match = re.search(rf"^{re.escape(name)}:.*(?:\n\t.*)*", text, re.MULTILINE)
    assert match, f"target '{name}' not found in {MAKEFILE}"
    return match.group(0)


def test_check_runs_full_pytest_suite():
    rule = target_recipe("check")
    runs_pytest_directly = "pytest tests/" in rule and "-m" not in rule
    deps = rule.splitlines()[0]
    delegates = any(
        dep in deps for dep in ("check-tests", "test")
    ) and "pytest tests/" in target_recipe("check-tests" if "check-tests" in deps else "test")
    assert runs_pytest_directly or delegates, (
        "coding-python.md defines 'make check' as the full test suite "
        f"(integration + slow included); current rule:\n{rule}"
    )


def test_check_keeps_static_checks():
    deps = target_recipe("check").splitlines()[0]
    for dep in ("check-skills-drift", "check-agnostic-tickets", "check-agnostic-skills"):
        assert dep in deps, f"'check' lost its static prerequisite {dep}"


def test_check_fast_excludes_integration_and_slow():
    rule = target_recipe("check-fast")
    assert "not integration" in rule and "not slow" in rule, (
        f"'check-fast' must exclude integration and slow tiers; current rule:\n{rule}"
    )
