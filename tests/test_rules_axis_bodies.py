"""doctype/ and lang/ rule bodies for the axis resolver (ticket 0256).

The axis resolver (`scripts/prose_predicate.py`) tells reviewers a file's
doctype and lang; a body must exist for each value it can name. Two ratchets:

1. Coverage — the in-use doctype values (techreport, slides, book) and the
   documented langs (fr, en) each have a rule body, indexed in rules/README.md.
2. Reachability — every rules/doctype/*.md and rules/lang/*.md file corresponds
   to a value the resolver can actually emit; an orphan file that can never
   be named is dead content.

Each body is loaded verbatim alongside format + prose bodies, so every file
also gets a size budget.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "rules"
_RESOLVER = REPO / "scripts" / "prose_predicate.py"


def _load():
    spec = importlib.util.spec_from_file_location("prose_predicate", _RESOLVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inj = _load()

# Langs are manifest-supplied (free-form), so reachability can't be derived
# from the resolver; this documented set is the allowlist. Extend it when a
# project's manifest introduces a new lang.
DOCUMENTED_LANGS = {"fr", "en"}

REQUIRED_DOCTYPES = {"techreport", "slides", "book"}

# Composability budget: format (~3k) + doctype + lang + prose/_all (~3k) must
# stay small together, so each axis body stays small.
SIZE_BUDGET = 2000


def doctype_files() -> list[Path]:
    return sorted((RULES / "doctype").glob("*.md"))


def lang_files() -> list[Path]:
    return sorted((RULES / "lang").glob("*.md"))


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
            "DOCUMENTCLASS_DOCTYPE value, so the resolver can never name it "
            "(manifest-only doctypes must be added to the map or documented)"
        )


def test_lang_files_are_reachable():
    for f in lang_files():
        assert f.stem in DOCUMENTED_LANGS, (
            f"rules/lang/{f.name} is unreachable: '{f.stem}' is not a "
            "documented lang value (extend DOCUMENTED_LANGS when a project "
            "manifest introduces it)"
        )


@pytest.mark.parametrize(
    "file", doctype_files() + lang_files(), ids=lambda f: f"{f.parent.name}/{f.name}"
)
def test_axis_body_stays_terse(file):
    size = len(file.read_text(encoding="utf-8"))
    assert size <= SIZE_BUDGET, (
        f"{file.relative_to(REPO)} is {size} chars (> {SIZE_BUDGET}): axis "
        "bodies are loaded verbatim and must compose with format + prose "
        "bodies"
    )


def test_readme_indexes_every_axis_body():
    readme = (RULES / "README.md").read_text(encoding="utf-8")
    for f in doctype_files() + lang_files():
        rel = f"{f.parent.name}/{f.name}"
        assert rel in readme, (
            f"rules/README.md must index {rel} — the index is the single "
            "source of truth on when each rule file applies"
        )
