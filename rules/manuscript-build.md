<!-- last-reviewed: 2026-08-14 -->
# Manuscript builds — assert the product, not the exit code

Loaded when a manuscript build (LaTeX/tectonic, Quarto/pandoc) is set up or
changed. The Make rule in `coding-python.md` says that `make` checks the
recipe's exit code, not what the recipe produced. Here that takes a sharper
form: the recipe succeeds **and the product is wrong**.

## The defect class

A typesetting toolchain does not fail on an unresolved reference. `tectonic`
warns, writes the PDF, and the missing citation appears there as `[?]`.
Quarto/pandoc does the same with a different placeholder: citeproc warns
`citation X not found` and renders the key itself, in bold, where the
reference should be. In code an unresolved symbol is a link error.
A manuscript has no link step — `\cite`/`\ref` are external references, the
`.bib` is the symbol table, and nothing checks that they resolve. That this is
a warning is an arbitration of TeX, a batch typesetter built to always emit
output, not a property of the problem.

So a PDF with a `[?]` on page 17 reaches submission with nothing protesting.
Verify it by hand and you get a criterion checked a different way each pass —
which is not a criterion. Where a `.bib` is shared between manuscripts, the
risk is structural: a purge scoped to one manuscript removes an entry from
under another.

## The recipes

**tectonic.** No flag does this — `--help`, `-Z help` and the V2 interface
carry nothing, and `-Z continue-on-errors` runs the other way (an undefined
citation is a *warning*, so it never reaches the error gate). Verified on
0.15.0. Build with `--keep-logs` and read the `.log`; the PDF shows only a
question mark, the log names the key.

Two channels, and keep them separate. The **verdict** reads the summary lines
("There were undefined citations.", "… references.") — short, so they never
hit the log's 79-column wrap. The **naming** reads the detail lines and the
`.blg`, which *do* wrap mid-key, so unwrap first and treat as best effort.
Gating on the wrapping channel lies; naming from it alone silently drops a
long key.

**Quarto/pandoc.** Same class, different strings: citeproc emits `citation X
not found` on stderr and renders the bare key in bold, not `[?]`. Gate on the
warning, never on the rendered text.

## Wiring it

- **In the recipe, after the build — not as a prerequisite.** A prerequisite
  runs before the target and has nothing to read yet. The recipe is stronger
  anyway: `make` never splits one, so neither `-j` nor a build launched from
  the subdirectory can route around it.
- **`.DELETE_ON_ERROR:` is load-bearing.** `make` leaves a target whose recipe
  failed. Without it the rejected PDF stays on disk *newer* than its sources,
  the next `make` reports "up to date", and the guard never runs again — the
  failure silences its own alarm.
- **A permanent red fixture**, run on every build rather than once by hand: a
  guard whose "all clear" is indistinguishable from "I could not look" is not
  a guard.
- **Vendor the check into the repo.** A writing workpackage must build
  offline, clean-room, with no harness present — a co-author or a CI container
  has neither. The harness carries the norm and the recipe; the repo carries
  the few lines.
- **Don't fail on cosmetics**: `Underfull`, `Overfull`, and pre-existing
  BibTeX field warnings are known noise.

The build guard protects the manuscript being built, and can do no more. The
cross-manuscript purge, whose victim is not rebuilt in that change, is caught
at the review gate instead, by `verify-adherence` phase 1.0 (c), which reads
sources rather than logs. That gate runs even in a repo with no `scripts/`
directory. Reference implementation: `scripts/check_tex_unresolved.py`
in polycentric_activity (ticket 0091).
