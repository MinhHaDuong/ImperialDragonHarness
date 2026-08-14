---
name: track-changes-pdf
description: "Render a revision-marked PDF of a LaTeX manuscript between two git refs, highlighting insertions and deletions via latexdiff. Closes the annotate-reply-apply loop for journal revise-and-resubmit rounds."
user-invocable: true
disable-model-invocation: false
argument-hint: "--old-ref <tag/branch/commit> [--new-ref HEAD] --main-tex <path/to/main.tex> --output <marked.pdf> [--repo .]"
---

# Track-changes PDF $ARGUMENTS

Render a revision-marked PDF of a LaTeX manuscript: insertions and deletions
between two git refs highlighted, so the author (or a journal editor) can read
and annotate exactly what changed. This mechanizes the review doctrine "the
review interface for prose is the recompiled PDF and latexdiff between tags" —
the diff is authored from the git history, never marked up by hand.

The bundled script is `~/.claude/skills/track-changes-pdf/track_changes_pdf.py`.

## When to use it

- A journal revise-and-resubmit asks for a change-marked version of the
  manuscript alongside the clean one.
- The author wants to review, in one pass, everything that moved between the
  submitted version and the current draft before replying to reviewers.

## How it works

1. `git archive` extracts the whole tree at the old ref and at the new ref into
   two temp directories (the full tree, so figures, `.bib`, and class files
   resolve).
2. `latexdiff --flatten` compares the two main-tex sources — `--flatten`
   inlines `\input`/`\include` so a multi-file manuscript diffs correctly — and
   writes a marked-up `*-diff.tex` into the new tree.
3. A LaTeX compiler (`latexmk` preferred, `pdflatex` fallback) builds the diff
   `.tex` to PDF, which is copied to `--output`.

## Steps

1. **Resolve the refs.** The old ref is the baseline — typically the tag or
   commit of the submitted manuscript (e.g. a `v1-submitted` tag). The new ref
   defaults to `HEAD`. Confirm both resolve in the target repository.

2. **Locate the main tex.** `--main-tex` is the manuscript's root `.tex` file,
   given relative to the repository root. If the manuscript splits across
   `\input` files, still point at the root — `--flatten` handles the rest.

3. **Run the helper.**
   ```
   python ~/.claude/skills/track-changes-pdf/track_changes_pdf.py \
       --repo . --old-ref v1-submitted --new-ref HEAD \
       --main-tex manuscript/main.tex --output revision-marked.pdf
   ```

4. **Toolchain check.** The helper needs `latexdiff` and a LaTeX compiler
   (`latexmk` or `pdflatex`). If either is absent it stops with an actionable
   install message — relay it to the author rather than retrying. On
   Debian/Ubuntu: `texlive-extra-utils` provides latexdiff, `texlive-latex-extra`
   plus `latexmk` the compiler.

5. **Hand off the PDF.** Report the output path and offer to open it for
   annotation. The marked PDF is an author artifact, never a CI gate.

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
- Determinism: the diff is a function of the two refs' sources. Re-running with
  the same refs reproduces the same markup (compiler timestamps aside).
