"""The /gaze prose/code routing is doctype-based, never extension-based (ticket 0550).

The 2026-08-17 audit of four real /gaze runs measured that the written rule —
"if any `*.qmd` changed → prose panel" — can never fire in a LaTeX repo: the
two manuscripts that got the prose panel got it by agent judgement, not by the
rule. The authoritative signal already exists: `resolve_axes()` in
`scripts/inject_rule_on_edit.py` yields a `doctype` for rendered deliverables
(project manifest `rules-map.toml`, else the `\\documentclass` sniff) and none
for process prose (`.md` notes, `.erg` tickets, `.py` scripts).

These tests pin the shared predicate (`scripts/prose_predicate.py`) and the
skill text that must name it:

- no routing rule in the review skills enumerates extensions;
- the predicate is true on manifest-mapped and `\\documentclass` LaTeX,
  false on process documents (the assertion that protects the correct code
  routing the audit measured on ticket-file diffs — a naive fix on
  `PROSE_FORMATS` regresses exactly here);
- mixed diffs route by any-semantics (one manuscript flips the diff);
- the `/simplify` prose guard is written in `skills/gaze/SKILL.md` § 5.
"""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parent.parent
GAZE = REPO / "skills" / "gaze" / "SKILL.md"
PROSE_SKILL = REPO / "skills" / "review-pr-prose" / "SKILL.md"
PREDICATE = REPO / "scripts" / "prose_predicate.py"

MANIFEST = """\
[[map]]
glob = "article-*/**/*.tex"
doctype = "techreport"
lang = "en"
"""


def _load_predicate():
    assert PREDICATE.is_file(), "scripts/prose_predicate.py does not exist"
    spec = importlib.util.spec_from_file_location("prose_predicate", PREDICATE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _repo_with_manifest(root: Path) -> Path:
    """A fixture repo shaped like polycentric_activity: manifest maps article-*."""
    repo = root / "repo"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "rules-map.toml").write_text(MANIFEST, encoding="utf-8")
    return repo


def test_no_bare_qmd_routing_rule():
    """No review skill routes by extension; both name the shared predicate.

    An illustrative extension mention stays acceptable; a condition keyed on
    changed extensions does not — that is what rotted the first time.
    """
    for skill in (GAZE, PROSE_SKILL):
        text = skill.read_text(encoding="utf-8")
        offenders = [
            (n, line.strip())
            for n, line in enumerate(text.splitlines(), 1)
            if "qmd" in line and "changed" in line
        ]
        assert not offenders, (
            f"{skill.relative_to(REPO)} still routes by extension: {offenders}"
        )
        assert "prose_predicate.py" in text, (
            f"{skill.relative_to(REPO)} does not name the shared prose predicate"
        )


def test_prose_predicate_covers_tex(tmp_path):
    mod = _load_predicate()
    # Manifest-mapped LaTeX manuscript — the shape the audit's MR 136 had.
    repo = _repo_with_manifest(tmp_path)
    tex = repo / "article-x" / "manuscrit.tex"
    tex.parent.mkdir()
    tex.write_text("\\section{Introduction}\n", encoding="utf-8")
    assert mod.is_manuscript(str(tex)), "manifest-mapped .tex must be a manuscript"
    # Bare .tex carrying \documentclass, no manifest anywhere above.
    bare = tmp_path / "bare" / "doc.tex"
    bare.parent.mkdir()
    bare.write_text("\\documentclass{article}\n\\begin{document}\n", encoding="utf-8")
    assert mod.is_manuscript(str(bare)), (
        "\\documentclass sniff must carry the predicate when no manifest exists"
    )


def test_prose_predicate_excludes_process_documents(tmp_path):
    """Prose *format* without doctype stays on the code panel.

    Guards the correct result the audit measured on MR 137/138: ticket-file
    diffs were well served by the code lenses. A fix keyed on PROSE_FORMATS
    alone regresses exactly here.
    """
    mod = _load_predicate()
    repo = _repo_with_manifest(tmp_path)
    note = repo / "conception" / "note.md"
    note.parent.mkdir()
    note.write_text("# Note de conception\n", encoding="utf-8")
    ticket = repo / "tickets" / "0001-x.erg"
    ticket.parent.mkdir()
    ticket.write_text("%erg 0.1\nTitle: x\n", encoding="utf-8")
    script = repo / "scripts" / "x.py"
    script.parent.mkdir()
    script.write_text("print('x')\n", encoding="utf-8")
    for path in (note, ticket, script):
        assert not mod.is_manuscript(str(path)), (
            f"{path.name} resolves to no doctype and must stay on the code panel"
        )


def test_mixed_diff_is_prose_by_any(tmp_path):
    """The audit's MR 139 shape: manuscrit.tex + a conception .md → prose.

    Also the known-negative control: a diff of process documents only stays
    code, so the any-rule cannot pass by firing on everything.
    """
    mod = _load_predicate()
    repo = _repo_with_manifest(tmp_path)
    tex = repo / "article-x" / "manuscrit.tex"
    tex.parent.mkdir()
    tex.write_text("\\section{Introduction}\n", encoding="utf-8")
    checklist = repo / "conception" / "checklist-venue.md"
    checklist.parent.mkdir()
    checklist.write_text("# Checklist\n", encoding="utf-8")
    assert mod.diff_is_prose([str(tex), str(checklist)]), (
        "one manuscript must flip a mixed diff to prose (any-semantics)"
    )
    assert not mod.diff_is_prose([str(checklist)]), (
        "a process-document-only diff must stay on the code panel"
    )


def test_simplify_prose_guard_documented():
    """§ 5 Simplify carries the prose guard, its motive, and its log line."""
    text = GAZE.read_text(encoding="utf-8")
    assert "### 5. Simplify" in text, "gaze § 5 heading moved — update this test"
    section = text.split("### 5. Simplify")[1].split("### 6.")[0]
    assert "simplify: skipped (prose workpackage)" in section, (
        "the prose skip must log like the tier skips"
    )
    assert "Prose workpackages" in section and "rules/git.md" in section, (
        "the guard must cite rules/git.md § Prose workpackages as its motive"
    )
