"""track-changes-pdf renders a revision-marked PDF via latexdiff between refs.

Two layers of coverage:

- **Contract ratchets + toolchain-absent behaviour** (fast tier, no LaTeX):
  the skill bundles its helper, documents the toolchain and the deferred
  per-ticket-grouping scope, and the helper degrades with a clear, actionable
  message when latexdiff or a compiler is missing.
- **Real end-to-end** (integration + slow): on a synthetic two-ref git repo,
  the helper runs latexdiff + compile, produces a PDF, and the intermediate
  diff .tex carries latexdiff markup. Skipped when the toolchain is absent.
"""

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO / "skills" / "track-changes-pdf"
SKILL = SKILL_DIR / "SKILL.md"
SCRIPT = SKILL_DIR / "track_changes_pdf.py"


def load_helper():
    """Import the bundled helper by path (it is not an installed package)."""
    spec = importlib.util.spec_from_file_location("track_changes_pdf", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def skill_text() -> str:
    return SKILL.read_text()


# --- Contract ratchets (fast) -------------------------------------------------

def test_bundled_script_exists():
    assert SCRIPT.exists(), "track-changes-pdf must bundle track_changes_pdf.py"


def test_first_sentence_is_searchable():
    """Discoverability: plain keywords in the opening description sentence."""
    first = skill_text().split("description:", 1)[1].split("\n", 1)[0].lower()
    for kw in ("revision-marked", "latexdiff", "git"):
        assert kw in first, f"first sentence should mention {kw!r}"


def test_documents_toolchain_requirements():
    text = skill_text().lower()
    assert "latexdiff" in text
    assert "latexmk" in text or "pdflatex" in text


def test_documents_deferred_grouping_scope():
    text = skill_text().lower()
    assert "scope" in text and "ticket" in text, (
        "must record that per-ticket/remark grouping is deferred in v1"
    )


def test_helper_is_pure_io_no_model_calls():
    src = SCRIPT.read_text()
    assert "anthropic" not in src.lower(), "helper must make no Anthropic API calls"
    for flag in ("--repo", "--old-ref", "--new-ref", "--main-tex", "--output"):
        assert flag in src, f"helper must expose {flag} (no hardcoded paths)"


# --- Toolchain-absent degrade path (fast, no LaTeX needed) --------------------

def test_latexdiff_absent_gives_actionable_error(monkeypatch):
    mod = load_helper()
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as exc:
        mod.require_latexdiff()
    msg = str(exc.value)
    assert "latexdiff not found" in msg
    assert "install" in msg.lower(), "error must tell the user how to install it"


def test_no_compiler_gives_actionable_error(monkeypatch):
    mod = load_helper()
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as exc:
        mod.resolve_compiler()
    msg = str(exc.value).lower()
    assert "latexmk" in msg and "pdflatex" in msg
    assert "install" in msg


def test_compiler_prefers_latexmk(monkeypatch):
    mod = load_helper()
    monkeypatch.setattr(mod.shutil, "which",
                        lambda name: f"/usr/bin/{name}" if name in {"latexmk", "pdflatex"} else None)
    assert mod.resolve_compiler()[0] == "latexmk"


# --- Input-validation guards (fast, no LaTeX / no git needed) -----------------

def test_resolve_ref_rejects_option_like_ref(tmp_path):
    """A ref starting with '-' is a git-archive argument-injection vector.

    ``git archive --format=tar -o/path HEAD`` writes an arbitrary file with exit
    0, so an option-like ref must be rejected before it reaches any subprocess —
    and must never create a file.
    """
    mod = load_helper()
    git = shutil.which("git") or "git"
    bad_target = tmp_path / "pwned.tar"
    bad_ref = f"-o{bad_target}"
    with pytest.raises(SystemExit) as exc:
        mod.resolve_ref(git, tmp_path, bad_ref)
    assert bad_ref in str(exc.value), "error must name the offending ref"
    assert not bad_target.exists(), "option-like ref must never reach a subprocess"


def test_contained_join_rejects_absolute_main_tex(tmp_path):
    """An absolute --main-tex silently escapes the extracted tree via pathlib '/'."""
    mod = load_helper()
    with pytest.raises(SystemExit) as exc:
        mod.contained_join(tmp_path, "/etc/passwd")
    assert "absolute" in str(exc.value).lower()


def test_contained_join_rejects_traversal_main_tex(tmp_path):
    """A '..' --main-tex escapes the extracted tree."""
    mod = load_helper()
    base = tmp_path / "old"
    base.mkdir()
    with pytest.raises(SystemExit) as exc:
        mod.contained_join(base, "../../../etc/passwd")
    msg = str(exc.value).lower()
    assert "escape" in msg or "outside" in msg


# --- Real end-to-end (integration + slow) ------------------------------------


@pytest.mark.integration
def test_resolve_ref_resolves_to_full_sha(tmp_path):
    """A valid ref resolves to a 40-hex-char commit SHA (which can't start '-')."""
    mod = load_helper()
    repo = tmp_path / "manuscript"
    _make_two_ref_repo(repo)
    git = shutil.which("git")
    sha = mod.resolve_ref(git, repo, "v1-submitted")
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)


@pytest.mark.integration
def test_resolve_ref_bad_ref_errors(tmp_path):
    mod = load_helper()
    repo = tmp_path / "manuscript"
    _make_two_ref_repo(repo)
    git = shutil.which("git")
    with pytest.raises(SystemExit) as exc:
        mod.resolve_ref(git, repo, "no-such-ref")
    assert "no-such-ref" in str(exc.value)

def _toolchain_present() -> bool:
    return bool(shutil.which("latexdiff")) and bool(
        shutil.which("latexmk") or shutil.which("pdflatex")
    )


def _make_two_ref_repo(root: Path) -> None:
    """A tiny LaTeX manuscript committed at two refs, one sentence changed."""
    def git(*args):
        subprocess.run(["git", "-C", str(root), *args], check=True,
                       capture_output=True, text=True)

    root.mkdir(parents=True, exist_ok=True)
    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    tex = root / "main.tex"
    tex.write_text(
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "The original climate finance estimate was ten billion dollars.\n"
        "\\end{document}\n"
    )
    git("add", "main.tex")
    git("commit", "-q", "-m", "v1")
    git("tag", "v1-submitted")
    tex.write_text(
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "The revised climate finance estimate was twenty billion dollars.\n"
        "\\end{document}\n"
    )
    git("add", "main.tex")
    git("commit", "-q", "-m", "v2")


@pytest.mark.integration
def test_extract_ref_pulls_each_refs_content(tmp_path):
    """Real git-archive plumbing: each ref extracts its own tree (no latexdiff)."""
    mod = load_helper()
    repo = tmp_path / "manuscript"
    _make_two_ref_repo(repo)
    git = shutil.which("git")

    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    mod.extract_ref(git, repo, "v1-submitted", old_dir)
    mod.extract_ref(git, repo, "HEAD", new_dir)

    assert "original" in (old_dir / "main.tex").read_text()
    assert "twenty billion" in (new_dir / "main.tex").read_text()


@pytest.mark.integration
def test_extract_ref_bad_ref_errors(tmp_path):
    mod = load_helper()
    repo = tmp_path / "manuscript"
    _make_two_ref_repo(repo)
    git = shutil.which("git")
    with pytest.raises(SystemExit) as exc:
        mod.extract_ref(git, repo, "no-such-ref", tmp_path / "out")
    assert "no-such-ref" in str(exc.value)


@pytest.mark.integration
@pytest.mark.slow
def test_render_end_to_end(tmp_path):
    if not _toolchain_present():
        pytest.skip("latexdiff and/or a LaTeX compiler not installed")
    mod = load_helper()
    repo = tmp_path / "manuscript"
    _make_two_ref_repo(repo)
    workdir = tmp_path / "work"
    output = tmp_path / "revision-marked.pdf"

    result = mod.render(
        repo=repo, old_ref="v1-submitted", new_ref="HEAD",
        main_tex="main.tex", output=output, workdir=workdir,
    )

    assert result == output.resolve()
    assert output.exists() and output.stat().st_size > 0, "no PDF produced"

    diff_tex = workdir / "new" / "main-diff.tex"
    assert diff_tex.exists(), "latexdiff should have written the diff .tex"
    diff_src = diff_tex.read_text()
    assert "\\DIFadd" in diff_src, "insertions should be marked with \\DIFadd"
    assert "\\DIFdel" in diff_src, "deletions should be marked with \\DIFdel"
