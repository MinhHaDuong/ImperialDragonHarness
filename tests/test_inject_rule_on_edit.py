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
