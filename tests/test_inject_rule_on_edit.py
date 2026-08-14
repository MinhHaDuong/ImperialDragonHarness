"""Tests for scripts/inject_rule_on_edit.py — the PreToolUse hook that injects
matching global rule bodies on the first edit of a file per session."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

_HOOK = Path(__file__).resolve().parent.parent / "scripts" / "inject_rule_on_edit.py"


def _load():
    spec = importlib.util.spec_from_file_location("inject_rule_on_edit", _HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inj = _load()


# --- format axis (extension, project-agnostic) -------------------------------

def test_format_for_known_extensions():
    assert inj.format_for("/a/b/foo.py") == "python"
    assert inj.format_for("x.sh") == "bash"
    assert inj.format_for("paper.tex") == "tex"
    assert inj.format_for("book.qmd") == "qmd"


def test_format_for_unstyled_is_none():
    assert inj.format_for("data.json") is None
    assert inj.format_for("table.csv") is None
    assert inj.format_for("ticket.erg") is None


# --- doctype sniff (markup, .tex only today) ---------------------------------

@pytest.mark.parametrize(
    "cls,expected",
    [("report", "techreport"), ("article", "article"), ("beamer", "slides"), ("memoir", "memoir")],
)
def test_sniff_doctype_from_documentclass(tmp_path, cls, expected):
    f = tmp_path / "main.tex"
    f.write_text(f"\\documentclass[a4paper,11pt]{{{cls}}}\n\\begin{{document}}\n")
    assert inj.sniff_doctype(str(f), "tex") == expected


def test_sniff_doctype_none_without_class(tmp_path):
    f = tmp_path / "frag.tex"
    f.write_text("just some \\section{x} text\n")
    assert inj.sniff_doctype(str(f), "tex") is None


def test_sniff_doctype_skips_non_tex(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("\\documentclass{report}\n")  # not parsed for .md
    assert inj.sniff_doctype(str(f), "md") is None


# --- manifest (project-local mapping) ----------------------------------------

def _manifest_repo(tmp_path, toml_body):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "rules-map.toml").write_text(toml_body)
    (tmp_path / "slides" / "manuscript").mkdir(parents=True)
    return tmp_path


def test_manifest_default_lang_applies(tmp_path):
    repo = _manifest_repo(tmp_path, 'default_lang = "fr"\n')
    f = repo / "slides" / "manuscript" / "main.tex"
    f.write_text("x")
    axes = inj.manifest_axes(str(f), repo / ".claude" / "rules-map.toml")
    assert axes["lang"] == "fr"


def test_manifest_glob_sets_doctype_and_overrides_lang(tmp_path):
    repo = _manifest_repo(
        tmp_path,
        'default_lang = "en"\n\n[[map]]\nglob = "slides/manuscript/**/*.tex"\n'
        'doctype = "techreport"\nlang = "fr"\n',
    )
    f = repo / "slides" / "manuscript" / "main.tex"
    f.write_text("x")
    axes = inj.manifest_axes(str(f), repo / ".claude" / "rules-map.toml")
    assert axes["doctype"] == "techreport"
    assert axes["lang"] == "fr"  # per-glob lang beats default_lang


# --- composition -------------------------------------------------------------

def test_resolve_axes_composes_format_prose_doctype(tmp_path):
    repo = _manifest_repo(tmp_path, 'default_lang = "fr"\n')
    f = repo / "slides" / "manuscript" / "main.tex"
    f.write_text("\\documentclass{report}\n")
    axes = inj.resolve_axes(str(f))
    assert axes["format"] == "tex"
    assert axes["prose"] == "_all"
    assert axes["doctype"] == "techreport"  # sniffed
    assert axes["lang"] == "fr"  # manifest default


def test_resolve_axes_empty_for_data_file():
    assert inj.resolve_axes("/x/data.json") == {}


def test_manifest_doctype_overrides_sniff(tmp_path):
    repo = _manifest_repo(
        tmp_path,
        '[[map]]\nglob = "slides/manuscript/**/*.tex"\ndoctype = "slides"\n',
    )
    f = repo / "slides" / "manuscript" / "main.tex"
    f.write_text("\\documentclass{report}\n")  # would sniff techreport
    axes = inj.resolve_axes(str(f))
    assert axes["doctype"] == "slides"  # manifest wins


# --- rule-file resolution (convention + legacy alias) ------------------------

def test_candidate_rule_files_convention_and_alias(tmp_path):
    rules = tmp_path
    (rules / "format").mkdir()
    (rules / "prose").mkdir()
    (rules / "format" / "tex.md").write_text("tex rules")
    (rules / "coding-bash.md").write_text("legacy bash rules")  # alias target
    (rules / "prose" / "_all.md").write_text("prose rules")

    # tex prose file -> format/tex.md + prose/_all.md (doctype/lang absent)
    files = inj.candidate_rule_files(
        {"format": "tex", "prose": "_all", "doctype": "techreport"}, rules
    )
    names = [f.name for f in files]
    assert names == ["tex.md", "_all.md"]  # techreport.md does not exist -> skipped

    # bash resolves via the legacy coding-bash.md alias
    bash_files = inj.candidate_rule_files({"format": "bash"}, rules)
    assert [f.name for f in bash_files] == ["coding-bash.md"]


# --- end-to-end: injection + per-session dedup -------------------------------

@pytest.mark.integration
def test_hook_injects_then_dedups(tmp_path):
    rules = tmp_path / "rules"
    (rules / "format").mkdir(parents=True)
    (rules / "format" / "python.md").write_text("PYRULE-MARKER body")
    tmpdir = tmp_path / "tmp"
    tmpdir.mkdir()
    payload = json.dumps(
        {"session_id": "sess1", "tool_input": {"file_path": str(tmp_path / "x.py")}}
    )
    env = {"TMPDIR": str(tmpdir), "PATH": "/usr/bin:/bin"}

    def run():
        return subprocess.run(
            ["python3", str(_HOOK), "--rules-dir", str(rules)],
            input=payload, capture_output=True, text=True, env=env,
        )

    first = run()
    assert first.returncode == 0
    out = json.loads(first.stdout)
    assert "PYRULE-MARKER" in out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    second = run()  # same session -> deduped -> no output
    assert second.returncode == 0
    assert second.stdout.strip() == ""


@pytest.mark.integration
def test_hook_silent_for_unstyled_file(tmp_path):
    payload = json.dumps({"session_id": "s", "tool_input": {"file_path": "/x/data.json"}})
    res = subprocess.run(
        ["python3", str(_HOOK)], input=payload, capture_output=True, text=True
    )
    assert res.returncode == 0
    assert res.stdout.strip() == ""


# --- glob matcher (direct) ---------------------------------------------------

@pytest.mark.parametrize(
    "rel,glob,expected",
    [
        ("slides/manuscript/main.tex", "slides/manuscript/**/*.tex", True),
        ("slides/manuscript/sub/main.tex", "slides/manuscript/**/*.tex", True),
        ("slides/x.qmd", "**/*.qmd", True),
        ("book/index.qmd", "*.qmd", True),  # slash-less -> basename fallback
        ("a/main.tex", "slides/**/*.tex", False),
        ("src/foo.py", "*.py", True),  # basename fallback
        ("src/foo.py", "src/*.py", True),
        ("src/deep/foo.py", "src/*.py", False),  # * does not cross /
    ],
)
def test_glob_match(rel, glob, expected):
    assert inj.glob_match(rel, glob) is expected


def test_glob_match_rejects_pathological_glob():
    # Many '*' would drive catastrophic backtracking; the complexity cap returns
    # False fast instead of hanging past the hook timeout.
    assert inj.glob_match("a/b/c/d/e/f.tex", "**a**b**c**d**e**f**g") is False


def test_manifest_non_match_leaves_sniffed_doctype(tmp_path):
    repo = _manifest_repo(
        tmp_path,
        '[[map]]\nglob = "other/**/*.tex"\ndoctype = "slides"\n',  # does NOT match
    )
    f = repo / "slides" / "manuscript" / "main.tex"
    f.write_text("\\documentclass{report}\n")
    axes = inj.resolve_axes(str(f))
    assert axes["doctype"] == "techreport"  # sniff survives when no glob matches


def test_candidate_prefers_convention_over_alias(tmp_path):
    rules = tmp_path
    (rules / "format").mkdir()
    (rules / "format" / "python.md").write_text("canonical")
    (rules / "coding-python.md").write_text("legacy alias")  # both exist
    files = inj.candidate_rule_files({"format": "python"}, rules)
    assert [f.name for f in files] == ["python.md"]  # canonical wins, alias skipped


# --- typo axis: fine typography applies to a RENDERED deliverable only -------
# Ticket 0425. The author's arbitrage: fine typography is a finishing pass on a
# rendered deliverable, crossing two axes — the language of the text and the
# markup language. A draft that nothing renders owes it nothing. The tests below
# are the negative control: if the draft and the deliverable resolve the same
# axes, the rule was reworded rather than conditioned.

def _render_repo(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "rules-map.toml").write_text(
        'default_lang = "fr"\n\n[[map]]\nglob = "livrables/**/*.md"\nrender = true\n'
    )
    (tmp_path / "conception").mkdir()
    (tmp_path / "livrables").mkdir()
    return tmp_path


def test_unrendered_markdown_draft_has_no_typo_axis(tmp_path):
    repo = _render_repo(tmp_path)
    f = repo / "conception" / "note.md"
    f.write_text("brouillon")
    axes = inj.resolve_axes(str(f))
    assert axes["lang"] == "fr"  # language norms still apply while drafting
    assert "typo" not in axes  # fine typography does not


def test_rendered_markdown_deliverable_gets_typo_axis(tmp_path):
    repo = _render_repo(tmp_path)
    f = repo / "livrables" / "rapport.md"
    f.write_text("livrable")
    assert inj.resolve_axes(str(f))["typo"] == "fr"


def test_tex_is_rendered_by_construction(tmp_path):
    # LaTeX/Quarto sources exist to be compiled: no manifest flag needed.
    repo = _render_repo(tmp_path)
    f = repo / "conception" / "main.tex"
    f.write_text("\\documentclass{report}\n")
    assert inj.resolve_axes(str(f))["typo"] == "fr"


def test_manifest_render_false_overrides_format_default(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "rules-map.toml").write_text(
        'default_lang = "fr"\n\n[[map]]\nglob = "frag/**/*.tex"\nrender = false\n'
    )
    (tmp_path / "frag").mkdir()
    f = tmp_path / "frag" / "part.tex"
    f.write_text("\\section{x}\n")
    assert "typo" not in inj.resolve_axes(str(f))


def test_typo_axis_needs_a_resolved_lang(tmp_path):
    # Typography is language-specific: no lang, nothing to inject.
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "rules-map.toml").write_text(
        '[[map]]\nglob = "*.md"\nrender = true\n'
    )
    f = tmp_path / "x.md"
    f.write_text("x")
    assert "typo" not in inj.resolve_axes(str(f))


def test_candidate_rule_files_places_typo_after_lang(tmp_path):
    rules = tmp_path
    for d in ("lang", "typo", "prose"):
        (rules / d).mkdir()
    (rules / "lang" / "fr.md").write_text("lang body")
    (rules / "typo" / "fr.md").write_text("typo body")
    (rules / "prose" / "_all.md").write_text("prose body")
    files = inj.candidate_rule_files(
        {"format": "md", "lang": "fr", "typo": "fr", "prose": "_all"}, rules
    )
    assert [f"{f.parent.name}/{f.name}" for f in files] == [
        "lang/fr.md",
        "typo/fr.md",
        "prose/_all.md",
    ]


@pytest.mark.integration
def test_negative_control_insecable_demanded_only_when_rendered(tmp_path):
    """End-to-end against the REAL rulebook (ticket 0425's Test section).

    A French Markdown draft must draw no injected rule demanding non-breaking
    spaces; a French Markdown deliverable declared rendered must draw one.
    Identical injections here would mean the rule was reworded, not conditioned.
    """
    real_rules = Path(__file__).resolve().parent.parent / "rules"
    repo = _render_repo(tmp_path)
    tmpdir = tmp_path / "tmp"
    tmpdir.mkdir()

    def context_for(path, session_id):
        payload = json.dumps(
            {"session_id": session_id, "tool_input": {"file_path": str(path)}}
        )
        res = subprocess.run(
            ["python3", str(_HOOK), "--rules-dir", str(real_rules)],
            input=payload, capture_output=True, text=True,
            env={"TMPDIR": str(tmpdir), "PATH": "/usr/bin:/bin"},
        )
        assert res.returncode == 0
        if not res.stdout.strip():
            return ""
        return json.loads(res.stdout)["hookSpecificOutput"]["additionalContext"]

    draft = repo / "conception" / "note.md"
    draft.write_text("brouillon\n")
    deliverable = repo / "livrables" / "rapport.md"
    deliverable.write_text("livrable\n")

    draft_ctx = context_for(draft, "sess-draft")
    deliverable_ctx = context_for(deliverable, "sess-deliverable")

    assert draft_ctx, "a French prose draft still draws its prose + lang rules"
    assert "insécable" not in draft_ctx, (
        "an unrendered draft must draw no rule demanding non-breaking spaces"
    )
    assert "insécable" in deliverable_ctx, (
        "a rendered French deliverable must draw the fine-typography rule"
    )
    # The injected-body header, not a mere mention: lang/fr.md legitimately
    # points at typo/fr.md without injecting it.
    header = "----- typo/fr.md -----"
    assert header in deliverable_ctx and header not in draft_ctx


@pytest.mark.integration
def test_hook_truncates_oversized_context(tmp_path):
    rules = tmp_path / "rules"
    (rules / "format").mkdir(parents=True)
    (rules / "format" / "python.md").write_text("X" * 20000)  # > MAX_CONTEXT
    tmpdir = tmp_path / "tmp"
    tmpdir.mkdir()
    payload = json.dumps(
        {"session_id": "big", "tool_input": {"file_path": str(tmp_path / "x.py")}}
    )
    res = subprocess.run(
        ["python3", str(_HOOK), "--rules-dir", str(rules)],
        input=payload, capture_output=True, text=True,
        env={"TMPDIR": str(tmpdir), "PATH": "/usr/bin:/bin"},
    )
    ctx = json.loads(res.stdout)["hookSpecificOutput"]["additionalContext"]
    assert len(ctx) < 10000
    assert "truncated" in ctx
