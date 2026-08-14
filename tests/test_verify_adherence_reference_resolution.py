"""Guard: verify-adherence phase 1.0 must gate prose reference resolution (ticket 0440).

The harness already treats an unresolved symbol as blocking — phase 1.0 (a),
"Any unresolved symbol → fail". Its scope stops at scripts/*.py, so a change
that drops an `import` fails the gate while one that drops a `.bib` entry
passes. Sub-check (c) closes that asymmetry.

Two clauses are load-bearing and are the ones a paraphrase would quietly lose:

1. The check is **textual** — it must not require a build. A manuscript whose
   `.bib` entry was purged from a sibling manuscript's change is not rebuilt in
   that change, so a log-reading check cannot see it. That case is the reason
   the sub-check exists.
2. The scope is the **blast radius of the .bib**, not the touched files.
   Restricting to touched files reproduces exactly the blind spot.

Two more clauses were added after the MR #726 review round, each closing a way
the sub-check could exist on paper and never fire:

3. The "no scripts/ directory" circuit breaker must skip (a) and (b) only.
   A manuscript-only repo has no scripts/ and is exactly the layout (c) exists
   for; skipping the whole phase there makes its all-clear indistinguishable
   from "I could not look".
4. The enumerated syntax must cover Quarto/pandoc (`@key`), not LaTeX alone.
   The skip trigger admits `.qmd` and the rule carries a Quarto recipe, so a
   LaTeX-only enumeration leaves the check textually inert on half its scope.

Text-grep only → fast tier, no marker.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "verify-adherence" / "SKILL.md"
RULE = REPO / "rules" / "manuscript-build.md"
RULES_INDEX = REPO / "rules" / "README.md"


@pytest.mark.parametrize(
    "needle,reason",
    [
        (
            "**(c) Reference resolution (prose).**",
            "phase 1.0 must carry the prose sub-check as (c), alongside (a) and (b)",
        ),
        (
            "Three sub-checks, all **blocking**",
            "the phase header must count three blocking sub-checks, not two",
        ),
        (
            "verify-adherence#reference-resolution",
            "the sub-check must emit its own rule ref, like (a) does",
        ),
        (
            "check **every manuscript in the repo that cites it**",
            "scope must be the blast radius of the .bib, not the touched files — "
            "restricting to touched files reproduces the cross-manuscript blind spot",
        ),
        (
            "Textual, no build",
            "the check must be textual: a build-dependent check cannot see a "
            "manuscript this change never rendered, which is the case it exists for",
        ),
        (
            "rules/manuscript-build.md",
            "the sub-check must point at the rule holding the doctrine and recipes",
        ),
        (
            "**(c) still runs**",
            "the 'no scripts/ directory' circuit breaker must skip (a) and (b) only "
            "— a manuscript-only repo has no scripts/ and is precisely the layout "
            "(c) exists for, so skipping the whole phase there silences the check "
            "in its own target class",
        ),
        (
            "Two exemptions, or the check cries wolf on valid sources.",
            "the sub-check must exempt the `\\nocite{*}` wildcard and `@` inside "
            "code/verbatim contexts — without them a valid manuscript fails the "
            "gate, and a gate that cries wolf gets routed around",
        ),
        (
            "Quarto/pandoc: same two checks, different syntax",
            "the enumerated reference forms must cover Quarto/pandoc `@key`, not "
            "LaTeX alone: the skip trigger admits .qmd and the rule ships a Quarto "
            "recipe, so a LaTeX-only enumeration is inert on half the declared scope",
        ),
    ],
)
def test_skill_wires_reference_resolution(needle, reason):
    assert needle in SKILL.read_text(encoding="utf-8"), reason


def test_rule_exists_and_covers_both_toolchains():
    text = RULE.read_text(encoding="utf-8")
    for tool in ("tectonic", "Quarto/pandoc"):
        assert tool in text, (
            f"rules/manuscript-build.md must carry a recipe for {tool}: the defect "
            "class spans both toolchains across the paper repos"
        )
    assert ".DELETE_ON_ERROR" in text, (
        "the rule must state .DELETE_ON_ERROR — without it a rejected PDF stays "
        "newer than its sources and the next build reports 'up to date', so the "
        "failure silences its own alarm"
    )


def test_rule_is_indexed():
    assert "manuscript-build.md" in RULES_INDEX.read_text(encoding="utf-8"), (
        "rules/README.md must index manuscript-build.md — the index is the single "
        "source of truth on when each rule file applies"
    )
