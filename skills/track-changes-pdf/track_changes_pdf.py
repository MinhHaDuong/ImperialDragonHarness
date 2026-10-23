#!/usr/bin/env python3
"""Render a revision-marked PDF of a LaTeX manuscript between two git refs.

Extracts the manuscript source at ``--old-ref`` and ``--new-ref``, runs
``latexdiff --flatten`` to produce a diff ``.tex`` (insertions and deletions
marked up), then compiles it to a PDF. This mechanizes the review doctrine
"the review interface for prose is the recompiled PDF and latexdiff between
tags" — the diff is authored from the git history, not by hand.

The helper is pure I/O: it shells out to ``git``, ``latexdiff``, and a LaTeX
compiler (``latexmk`` preferred, else ``pdflatex``). It makes no network or
model calls. It hardcodes no paths — repo, refs, main tex, and output are all
command-line arguments.

If ``latexdiff`` or the LaTeX compiler is absent, the helper exits with a
clear, actionable message rather than a stack trace.

Example:
    python track_changes_pdf.py \\
        --repo . --old-ref v1-submitted --new-ref HEAD \\
        --main-tex manuscript/main.tex --output revision-marked.pdf
"""

import argparse
import hashlib
import re
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)


class ToolchainError(SystemExit):
    """Raised (as SystemExit) when a required external tool is missing."""


def require_git() -> str:
    """Return the git executable path, or exit with an actionable message."""
    git = shutil.which("git")
    if git is None:
        raise ToolchainError("git not found on PATH — this helper diffs a git repository.")
    return git


def require_latexdiff() -> str:
    """Return the latexdiff path, or exit with an install hint."""
    latexdiff = shutil.which("latexdiff")
    if latexdiff is None:
        raise ToolchainError(
            "latexdiff not found on PATH. Install it to render a revision-marked "
            "PDF:\n"
            "  Debian/Ubuntu:  sudo apt-get install texlive-extra-utils\n"
            "  macOS (MacTeX):  tlmgr install latexdiff\n"
            "  Fedora:          sudo dnf install texlive-latexdiff\n"
            "latexdiff ships with most full TeX Live installations."
        )
    return latexdiff


def resolve_compiler() -> list[str]:
    """Return the compile command prefix, or exit if no compiler is present.

    Prefers ``latexmk`` (handles multi-pass runs and the bibliography), falls
    back to two-pass ``pdflatex`` for documents without bibliography processing.
    """
    if shutil.which("latexmk"):
        return ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error"]
    if shutil.which("pdflatex"):
        return ["pdflatex", "-interaction=nonstopmode", "-halt-on-error"]
    raise ToolchainError(
        "no LaTeX compiler found on PATH (looked for latexmk and pdflatex). "
        "Install a TeX distribution:\n"
        "  Debian/Ubuntu:  sudo apt-get install texlive-latex-extra latexmk\n"
        "  macOS:           install MacTeX\n"
        "  Fedora:          sudo dnf install texlive-scheme-medium latexmk"
    )


def resolve_ref(git: str, repo: Path, ref: str) -> str:
    """Resolve a user-supplied ref to a full commit SHA, rejecting option-like values.

    ``git archive`` (and git plumbing generally) parse a leading-dash argument as
    an option, not a tree-ish — ``git archive --format=tar -o/path HEAD`` writes an
    arbitrary file with exit 0. A crafted ``--old-ref``/``--new-ref`` value such as
    ``-o/path`` or ``--remote=<url>`` could redirect the archive write or trigger
    network access, so reject any option-like ref *before* it reaches a subprocess,
    then resolve it to a concrete SHA. Downstream callers thus only ever see a
    40-hex-char commit id, which can never start with ``-``.
    """
    if ref.startswith("-"):
        raise SystemExit(
            f"refusing ref {ref!r}: a value starting with '-' is parsed as a git "
            "option, not a commit. Pass a tag, branch, or commit SHA."
        )
    result = subprocess.run(
        [git, "-C", str(repo), "rev-parse", "--verify", "--end-of-options",
         f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"could not resolve ref {ref!r} in {repo} to a commit:\n"
            f"{result.stderr.strip() or '(no stderr)'}"
        )
    return result.stdout.strip()


def contained_join(base: Path, rel_str: str) -> Path:
    """Join ``rel_str`` under ``base``, rejecting absolute paths and ``..`` traversal.

    ``pathlib``'s ``/`` silently discards the left operand when the right is
    absolute (``Path('/a') / '/etc/passwd' == Path('/etc/passwd')``), and a ``..``
    component escapes the extracted tree. Either lets latexdiff or the compiler
    read arbitrary local files, so validate before returning the joined path.
    """
    rel = Path(rel_str)
    if rel.is_absolute():
        raise SystemExit(
            f"--main-tex must be relative to the repository root, got absolute {rel_str!r}"
        )
    base_resolved = base.resolve()
    joined = (base / rel).resolve()
    if not joined.is_relative_to(base_resolved):
        raise SystemExit(
            f"--main-tex {rel_str!r} escapes the extracted tree "
            f"({joined} is outside {base_resolved})"
        )
    return joined


def extract_ref(git: str, repo: Path, ref: str, dest: Path) -> None:
    """Extract the whole tree at ``ref`` into ``dest`` via ``git archive``.

    Extracting the full tree (not just the main tex) lets latexdiff --flatten
    resolve \\input/\\include and lets the compiler find figures, .bib, and
    class files.
    """
    dest.mkdir(parents=True, exist_ok=True)
    # git archive <ref> | tar -x -C dest, without a shell pipe.
    archive = subprocess.run(
        [git, "-C", str(repo), "archive", "--format=tar", ref],
        capture_output=True,
        check=False,
    )
    if archive.returncode != 0:
        raise SystemExit(
            f"git archive failed for ref {ref!r} in {repo}:\n"
            f"{archive.stderr.decode(errors='replace').strip()}"
        )
    tar = subprocess.run(
        ["tar", "-x", "-C", str(dest)],
        input=archive.stdout,
        capture_output=True,
        check=False,
    )
    if tar.returncode != 0:
        raise SystemExit(
            f"extracting the tree for ref {ref!r} failed:\n"
            f"{tar.stderr.decode(errors='replace').strip()}"
        )


def run_latexdiff(latexdiff: str, old_tex: Path, new_tex: Path, diff_tex: Path) -> None:
    """Run latexdiff --flatten and write the marked-up diff to ``diff_tex``."""
    if not old_tex.exists():
        raise SystemExit(f"main tex not found at old ref: {old_tex}")
    if not new_tex.exists():
        raise SystemExit(f"main tex not found at new ref: {new_tex}")
    result = subprocess.run(
        [latexdiff, "--flatten", str(old_tex), str(new_tex)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            "latexdiff failed:\n" + (result.stderr.strip() or "(no stderr)")
        )
    diff_tex.write_text(result.stdout)


def add_inputs(repo: Path, dest: Path, inputs: list[str]) -> None:
    """Copy only explicitly named, SHA-256-pinned supplementary files."""
    for item in inputs:
        parts = item.split("=", 2)
        if len(parts) < 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[1]):
            raise SystemExit("supplementary input must be PATH=SHA256[=SOURCE]")
        relative, expected = parts[:2]
        target = contained_join(dest, relative)
        source = Path(parts[2]) if len(parts) == 3 else repo / relative
        try:
            data = source.read_bytes()
        except OSError as exc:
            raise SystemExit(f"cannot read supplementary input {source}: {exc}") from exc
        if hashlib.sha256(data).hexdigest() != expected.lower():
            raise SystemExit(f"SHA-256 mismatch for supplementary input {source}")
        if target.exists():
            raise SystemExit(f"supplementary input would overwrite extracted path: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        log.info("supplementary input %s SHA-256 %s", relative, expected.lower())


def compile_pdf(compiler: list[str], workdir: Path, diff_tex: Path,
                input_root: Path | None = None) -> Path:
    """Compile ``diff_tex`` in ``workdir``; return the produced PDF path.

    latexmk resolves multi-pass and bibliography automatically. The
    pdflatex fallback is limited to documents without a bibliography processor.
    A fresh final log must confirm that citations and references resolved.
    """
    # Check literal bibliography declarations in latexdiff's flattened source.
    # Missing files must not resolve accidentally from a host BIBINPUTS path.
    input_root = (input_root or workdir).resolve()
    source = re.sub(r"(?<!\\)%[^\n]*", "", diff_tex.read_text())
    declarations = re.findall(
        r"\\(?:bibliography|addbibresource)(?:\[[^\]]*\])?\s*\{([^}]+)\}", source
    )
    for declaration in declarations:
        for resource in declaration.split(","):
            relative = resource.strip()
            if not relative.endswith(".bib"):
                relative += ".bib"
            resource_path = (workdir / relative).resolve()
            if (Path(relative).is_absolute() or not resource_path.is_relative_to(input_root)
                    or not resource_path.is_file()):
                raise SystemExit(
                    f"missing local bibliography input {relative!r}; "
                    "include it in the pinned tree or supply --new-input"
                )
    stem = diff_tex.stem
    for suffix in (".pdf", ".log"):
        (workdir / f"{stem}{suffix}").unlink(missing_ok=True)
    if compiler[0] == "latexmk":
        runs = [compiler + [diff_tex.name]]
    else:
        runs = [compiler + [diff_tex.name], compiler + [diff_tex.name]]
    for cmd in runs:
        result = subprocess.run(
            cmd, cwd=str(workdir), capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            tail = "\n".join(result.stdout.splitlines()[-25:])
            raise SystemExit(
                f"LaTeX compilation failed ({cmd[0]}). Last lines of the log:\n{tail}"
            )
        if compiler[0] != "latexmk":
            aux_text = "\n".join(p.read_text(errors="replace") for p in workdir.rglob("*.aux"))
            if r"\bibdata" in aux_text or (workdir / f"{stem}.bcf").exists():
                raise ToolchainError(
                    "bibliography processing requires latexmk and BibTeX/Biber; "
                    "install latexmk and the required backend, then rerun."
                )
    build_log = workdir / f"{stem}.log"
    if not build_log.is_file():
        raise SystemExit(f"cannot validate PDF: compiler produced no log at {build_log}")
    text = build_log.read_text(errors="replace")
    if re.search(r"undefined (?:citations|references)|(?:Citation|Reference)[^\n]*undefined",
                 text, re.IGNORECASE):
        raise SystemExit("PDF rejected: unresolved citations or references in final LaTeX log")
    pdf = workdir / f"{stem}.pdf"
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise SystemExit(f"compiler reported success but produced no PDF at {pdf}")
    return pdf


def render(repo: Path, old_ref: str, new_ref: str, main_tex: str, output: Path,
           workdir: Path | None = None, old_inputs: list[str] | None = None,
           new_inputs: list[str] | None = None) -> Path:
    """Render the revision-marked PDF; return the output path.

    ``main_tex`` is the manuscript path relative to the repository root.
    ``workdir`` lets tests inspect intermediates; when None a temp dir is used
    and cleaned up.
    """
    git = require_git()
    latexdiff = require_latexdiff()
    compiler = resolve_compiler()

    repo = repo.resolve()
    if not (repo / ".git").exists():
        # Path.exists() covers both a normal checkout's .git dir and a
        # worktree's .git file — either is fine, so a single check suffices.
        # Only warn — git archive will give the authoritative error if truly not a repo.
        log.warning("%s does not look like a git repository root", repo)

    # Reject option-like refs and pin each ref to a concrete commit SHA before it
    # reaches git archive (argument-injection guard).
    old_ref = resolve_ref(git, repo, old_ref)
    new_ref = resolve_ref(git, repo, new_ref)

    managed_tmp = None
    if workdir is None:
        managed_tmp = tempfile.mkdtemp(prefix="track-changes-pdf-")
        workdir = Path(managed_tmp)
    workdir = Path(workdir)

    try:
        old_dir = workdir / "old"
        new_dir = workdir / "new"
        if old_dir.exists() or new_dir.exists():
            raise SystemExit("workdir must not contain old/ or new/; use a fresh workdir")
        log.info("pinned refs old=%s new=%s", old_ref, new_ref)
        extract_ref(git, repo, old_ref, old_dir)
        extract_ref(git, repo, new_ref, new_dir)
        add_inputs(repo, old_dir, old_inputs or [])
        add_inputs(repo, new_dir, new_inputs or [])

        # Keep --main-tex inside the extracted tree (absolute/.. traversal guard).
        old_tex = contained_join(old_dir, main_tex)
        new_tex = contained_join(new_dir, main_tex)
        # Write the diff into the new tree so figures/.bib/class files resolve.
        diff_tex = new_tex.with_name(f"{Path(main_tex).stem}-diff.tex")
        run_latexdiff(latexdiff, old_tex, new_tex, diff_tex)

        pdf = compile_pdf(compiler, diff_tex.parent, diff_tex, input_root=new_dir)

        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, output)
        log.info("wrote revision-marked PDF to %s", output)
        return output
    finally:
        if managed_tmp is not None:
            shutil.rmtree(managed_tmp, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a revision-marked PDF between two git refs via latexdiff.",
    )
    parser.add_argument("--repo", type=Path, default=Path("."),
                        help="Path to the git repository (default: current dir).")
    parser.add_argument("--old-ref", required=True,
                        help="Baseline git ref (tag/branch/commit), e.g. the submitted version.")
    parser.add_argument("--new-ref", default="HEAD",
                        help="Revised git ref (default: HEAD).")
    parser.add_argument("--main-tex", required=True,
                        help="Main .tex file, relative to the repository root.")
    parser.add_argument("--output", type=Path, required=True,
                        help="Path to write the revision-marked PDF.")
    for side in ("old", "new"):
        parser.add_argument(f"--{side}-input", action="append", default=[],
                            metavar="PATH=SHA256[=SOURCE]",
                            help="Pinned supplementary file; repeat for each missing input. "
                                 "PATH is tree-relative; SOURCE defaults to repo/PATH.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose logging.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    render(
        repo=args.repo,
        old_ref=args.old_ref,
        new_ref=args.new_ref,
        main_tex=args.main_tex,
        output=args.output,
        old_inputs=args.old_input,
        new_inputs=args.new_input,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
