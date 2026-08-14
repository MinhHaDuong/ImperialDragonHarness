"""doctype/, lang/ and typo/ rule bodies for the injection hook (tickets 0256, 0425).

The axis engine (PR #404) resolves doctype and lang, but until these bodies
exist those axes inject nothing. Two ratchets:

1. Coverage — the in-use doctype values (techreport, slides, book) and the
   documented langs (fr, en) each have a rule body, indexed in rules/README.md.
   The typo axis is keyed by lang too, so it needs the same coverage.
2. Reachability — every rules/doctype/*.md, rules/lang/*.md and rules/typo/*.md
   file corresponds to a value the hook's resolver can actually emit; an orphan
   file that can never be injected is dead content.

Each body is injected verbatim and composes with format + prose bodies under
the hook's MAX_CONTEXT cap, so every file also gets a size budget.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"
_HOOK = REPO / "scripts" / "inject_rule_on_edit.py"


def _load():
    spec = importlib.util.spec_from_file_location("inject_rule_on_edit", _HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inj = _load()

# Langs are manifest-supplied (free-form), so reachability can't be derived
# from the hook; this documented set is the allowlist. Extend it when a
# project's manifest introduces a new lang.
DOCUMENTED_LANGS = {"fr", "en"}

REQUIRED_DOCTYPES = {"techreport", "slides", "book"}

# Composability budget: format (~3k) + doctype + lang + prose/_all (~3k) must
# fit under MAX_CONTEXT (9500), so each axis body stays small.
SIZE_BUDGET = 2000


def doctype_files() -> list[Path]:
    return sorted((RULES / "doctype").glob("*.md"))


def lang_files() -> list[Path]:
    return sorted((RULES / "lang").glob("*.md"))


def typo_files() -> list[Path]:
    return sorted((RULES / "typo").glob("*.md"))


def test_required_doctype_bodies_exist():
    stems = {f.stem for f in doctype_files()}
    missing = REQUIRED_DOCTYPES - stems
    assert not missing, (
        f"rules/doctype/ lacks bodies for in-use doctypes: {sorted(missing)}"
    )


def test_documented_lang_bodies_exist():
    stems = {f.stem for f in lang_files()}
    missing = DOCUMENTED_LANGS - stems
    assert not missing, (
        f"rules/lang/ lacks bodies for documented langs: {sorted(missing)}"
    )


def test_doctype_files_are_reachable():
    reachable = set(inj.DOCUMENTCLASS_DOCTYPE.values())
    for f in doctype_files():
        assert f.stem in reachable, (
            f"rules/doctype/{f.name} is unreachable: '{f.stem}' is not a "
            "DOCUMENTCLASS_DOCTYPE value, so the hook can never inject it "
            "(manifest-only doctypes must be added to the map or documented)"
        )


def test_lang_files_are_reachable():
    for f in lang_files():
        assert f.stem in DOCUMENTED_LANGS, (
            f"rules/lang/{f.name} is unreachable: '{f.stem}' is not a "
            "documented lang value (extend DOCUMENTED_LANGS when a project "
            "manifest introduces it)"
        )


def test_documented_typo_bodies_exist():
    stems = {f.stem for f in typo_files()}
    missing = DOCUMENTED_LANGS - stems
    assert not missing, (
        f"rules/typo/ lacks fine-typography bodies for documented langs: "
        f"{sorted(missing)}"
    )


def test_typo_files_are_reachable():
    for f in typo_files():
        assert f.stem in DOCUMENTED_LANGS, (
            f"rules/typo/{f.name} is unreachable: the typo axis takes the lang "
            "value, and '{f.stem}' is not a documented lang"
        )


def test_typo_bodies_carry_the_finishing_precondition():
    # The axis exists to say WHEN the pass runs; a body that only lists glyph
    # rules would have been reworded, not conditioned (ticket 0425).
    for f in typo_files():
        body = f.read_text(encoding="utf-8").lower()
        assert "finition" in body or "finishing" in body, (
            f"rules/typo/{f.name} must state that it is a finishing pass on a "
            "rendered deliverable, not a drafting obligation"
        )


def test_lang_bodies_do_not_demand_render_typography():
    # The clause moved to typo/; a surviving twin in lang/ would fire while
    # drafting and defeat the split.
    for f in lang_files():
        body = f.read_text(encoding="utf-8")
        assert "insécable" not in body and "insecable" not in body, (
            f"rules/lang/{f.name} still demands non-breaking spaces: that clause "
            "belongs to rules/typo/, injected only for a rendered deliverable"
        )


@pytest.mark.parametrize(
    "file",
    doctype_files() + lang_files() + typo_files(),
    ids=lambda f: f"{f.parent.name}/{f.name}",
)
def test_axis_body_stays_terse(file):
    size = len(file.read_text(encoding="utf-8"))
    assert size <= SIZE_BUDGET, (
        f"{file.relative_to(REPO)} is {size} chars (> {SIZE_BUDGET}): axis "
        "bodies are injected verbatim and must compose with format + prose "
        "bodies under the hook's MAX_CONTEXT cap"
    )


def test_readme_indexes_every_axis_body():
    readme = (RULES / "README.md").read_text(encoding="utf-8")
    for f in doctype_files() + lang_files() + typo_files():
        rel = f"{f.parent.name}/{f.name}"
        assert rel in readme, (
            f"rules/README.md must index {rel} — the index is the single "
            "source of truth on when each rule file applies"
        )
