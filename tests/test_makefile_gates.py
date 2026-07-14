"""Hygiene: Makefile gate targets match the coding-python.md definitions.

`check` is the pre-PR gate: full pytest suite (integration + slow included)
plus the static checks. `check-fast` is the development gate: unit tests only,
excluding the integration, slow, and adherence tiers. `lint` is the adherence
gate: the mechanical `-m adherence` tier run apart from the logic loop.
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
    if "check-tests" in rule.splitlines()[0]:
        rule = target_recipe("check-tests")
    assert re.search(r"pytest tests/\s*$", rule, re.MULTILINE), (
        "coding-python.md defines 'make check' as the full test suite — "
        "pytest over tests/ with no marker filter or other trailing args; "
        f"current rule:\n{rule}"
    )


def test_check_keeps_static_checks():
    deps = target_recipe("check").splitlines()[0]
    for dep in (
        "check-skills-drift",
        "check-agnostic-tickets",
        "check-agnostic-skills",
        "check-agnostic-scripts",
    ):
        assert dep in deps, f"'check' lost its static prerequisite {dep}"


def test_check_fast_excludes_non_fast_tiers():
    rule = target_recipe("check-fast")
    for marker in ("not integration", "not slow", "not adherence"):
        assert marker in rule, (
            "coding-python.md keeps the integration, slow, and adherence tiers "
            f"out of the fast loop — 'check-fast' must filter '{marker}'; "
            f"current rule:\n{rule}"
        )


def test_lint_runs_adherence_tier_only():
    rule = target_recipe("lint")
    assert re.search(r"pytest tests/ -m adherence\s*$", rule, re.MULTILINE), (
        "coding-python.md defines 'make lint' as the adherence tier only — "
        "pytest over tests/ filtered to -m adherence; "
        f"current rule:\n{rule}"
    )
