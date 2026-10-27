---
metadata:
  category: writing
name: track-changes-pdf
description: "Render a revision-marked PDF of a LaTeX manuscript between two git refs, marking insertions and deletions via latexdiff. Closes the annotate-reply-apply loop of journal revise-and-resubmit rounds."
user-invocable: true
disable-model-invocation: false
argument-hint: "--old-ref <tag/branch/commit> [--new-ref HEAD] --main-tex <path/to/main.tex> --output <marked.pdf> [--repo .]"
---

# Track-changes PDF $ARGUMENTS

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Render a revision-marked PDF of a LaTeX manuscript: insertions and deletions
between two git refs highlighted, so the author (or a journal editor) can read
and annotate exactly what changed. This mechanizes the review doctrine "the
review interface for prose is the recompiled PDF and latexdiff between tags" —
the diff is authored from the git history, never marked up by hand.

The bundled script is `"$IDH_ROOT/skills/track-changes-pdf/track_changes_pdf.py"`.

## When to use it

- A journal revise-and-resubmit asks for a change-marked version of the
  manuscript alongside the clean one.
- The author wants to review, in one pass, everything that moved between the
  submitted version and the current draft before replying to reviewers.

## How it works

1. `git archive` extracts the whole tree at the old ref and at the new ref into
   two isolated temporary directories. Only archived tracked files are included;
   ignored/untracked bibliography, figures or other build inputs are absent.
   Supply each missing input explicitly with a SHA-256 pin (see below).
2. `latexdiff --flatten` compares the two main-tex sources — `--flatten`
   inlines `\input`/`\include` so a multi-file manuscript diffs correctly — and
   writes a marked-up `*-diff.tex` into the new tree.
3. A LaTeX compiler (`latexmk` preferred, `pdflatex` fallback) builds the diff
   `.tex` to PDF. A fresh final build log is required; unresolved citations or
   references reject delivery before anything is copied to `--output`.
   The pdflatex fallback refuses documents needing BibTeX/Biber: install latexmk
   and the required backend instead.

## Steps

1. **Resolve the refs.** The old ref is the baseline — typically the tag or
   commit of the submitted manuscript (e.g. a `v1-submitted` tag). The new ref
   defaults to `HEAD`. Confirm both resolve in the target repository.

2. **Locate the main tex.** `--main-tex` is the manuscript's root `.tex` file,
   given relative to the repository root. If the manuscript splits across
   `\input` files, still point at the root — `--flatten` handles the rest.

3. **Run the helper.**
   ```
   python "$IDH_ROOT/skills/track-changes-pdf/track_changes_pdf.py" \
       --repo . --old-ref v1-submitted --new-ref HEAD \
       --main-tex manuscript/main.tex --output revision-marked.pdf
   ```

   For an ignored bibliography or other missing build input, repeat
   `--old-input 'PATH=SHA256[=SOURCE]'` and/or `--new-input` as needed. PATH is
   relative to the extracted repository root; SOURCE defaults to `repo/PATH`
   and may explicitly name a separate archived old/new file. Example:
   ```
   --old-input 'refs.bib=<64-hex-sha256>=/archive/submitted-refs.bib' \
   --new-input 'refs.bib=<64-hex-sha256>=/archive/revised-refs.bib'
   ```
   Compute each hash from the intended version (e.g. `sha256sum`), retain the
   command and files with the handoff, and verify the inventory against the
   manuscript's build recipe. Hash mismatches and overwriting tracked inputs
   are refused. The helper never silently imports the host working tree.
   It logs resolved commit IDs and input hashes. This pins document inputs;
   the installed TeX toolchain remains an external dependency.

4. **Toolchain check.** The helper needs `latexdiff` and a LaTeX compiler
   (`latexmk` or `pdflatex`). If either is absent it stops with an actionable
   install message — relay it to the author rather than retrying. On
   Debian/Ubuntu: `texlive-extra-utils` provides latexdiff, `texlive-latex-extra`
   plus `latexmk` the compiler.

5. **Hand off the PDF.** Only report success after the helper succeeds. On
   failure, any pre-existing output is an earlier artifact, not this run's PDF.
   Inspect rendered pages following `pdf-finish`; report the path, mechanical
   checks, pages inspected and any remaining limits. A clean build log does not
   establish good layout. The marked PDF is an author artifact, never a CI gate.

## Scope note (v1)

Grouping insertions and deletions **by ticket or reviewer remark** is out of
scope for v1. latexdiff diffs two source trees and has no per-remark concept —
it cannot know which ticket authored which change. The whole-revision diff
ships first because it is exact and needs no bookkeeping. The future hook for
per-remark grouping is either to drive latexdiff once per ticket (one diff over
each ticket's commit range, then merge the marked outputs) or to tag changes in
the source with a `\ticket{N}{...}` macro and colour by tag. Tracked in ticket
0288 (child of the R&R intake tracker 0265).

## Notes

- Forge-agnostic: the skill reads a git repository via refs; it opens no merge
  request and touches no forge.
- The helper is pure I/O — `git`, `latexdiff`, and a LaTeX compiler. No network,
  no model calls.
- Reproduction requires the two resolved commits, all supplementary files and
  their hashes, and a compatible installed toolchain. Archive those inputs.
- All markup and compilation occur in isolated copies. An explicit Python
  `workdir` must have no existing `old/` or `new/` directories; a reused build
  directory is refused to prevent stale inputs or products.
