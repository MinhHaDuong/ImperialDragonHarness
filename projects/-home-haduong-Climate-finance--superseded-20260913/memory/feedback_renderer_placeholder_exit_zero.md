---
name: feedback_renderer_placeholder_exit_zero
description: "Quarto substitutes a literal placeholder for a missing meta key or crossref and exits 0 — guard by rendering to markdown on stdout and grepping the output, which costs seconds."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 865fbacb-7066-4c68-8060-1935f1783217
  modified: 2026-07-28T07:38:48.639Z
---

A renderer given a **missing input** often does not fail. Quarto substitutes a
literal into the document and returns 0: `?meta:key` for a `{{< meta >}}` macro
naming an undeclared key, `?@fig-name` for an unresolved crossref, `**@key?**`
for an undefined citation. It warns on stderr, which nothing reads. The build
succeeds, the suite passes, and only a human reading the finished PDF sees it.

This is a different mechanism from the escaping class in
[[feedback_render_oracle_for_generated_markup]] — nothing is emitted wrongly;
the input simply is not there — but it has the same cure: assert on the
rendered output.

**Why:** ticket 0363 (2026-07-27). The data paper resolves every number it
reports through `{{< meta >}}`, and the only gate was someone remembering to
look. The nearest existing test compared prose against the `DOC_VARS` dict in
`compute_vars.py` — one layer above the generated `*-vars.yml` Quarto actually
loads — and was keyed off that dict, so `corpus-report.qmd`, absent from it,
was invisible: 12 unresolved keys, 22 placeholder occurrences, live. The
wrap-up sweep one mechanism over found `?@fig-companion-zseries` in
`multilayer-detection.qmd`, referenced three times, defined nowhere, orphaned
when the companion paper was retired (ticket 0420).

**Ticket 0420 (2026-07-28) hardened this with three writer-specific lessons:**
- **Measure the signal per mechanism AND per placement — predicted literals may
  be emitted by no writer.** The ticket predicted `**@key?**` for a bad
  citation; no Quarto writer emits it (citeproc renders `(key?)` in HTML/PDF,
  leaves `@key` untouched in markdown). A guard coded to the prediction passes
  forever. And a broken crossref inside a figure/table *caption* writes nothing
  to markdown stdout at all — the writer drops caption text — so the only
  signal is stderr (`Unable to resolve crossref`). Union stdout and stderr.
- **Citeproc only runs where a bibliography is declared**, so a citing document
  without one gets no warning for an unknown key. Cheapest closure: a static
  check that any deliverable citing (`[@key]`) declares a bibliography.
- **The live defect was a label mismatch, not a missing figure**: three refs
  restyled the image *filename* (`fig_companion_zseries`) as a label while the
  figure was defined as `{#fig-zseries}`. Verify a "missing" target really is
  missing before treating the fix as an author call — grep for the definition
  and read the producing plot script first.

**How to apply:**
- **Render to markdown on stdout — it is seconds, not a minute.** `quarto
  render doc.qmd --to markdown --no-execute --output -` resolves shortcodes over
  the same Lua-filter path as `--to pdf` (verified by diffing placeholder,
  warning, and exit code both ways) while skipping LaTeX entirely: 2–8 s per
  document. `--output -` means no rendered artifact lands beside a tracked
  source. This makes a real render cheap enough for the `integration` tier, so
  "a full render is too heavy to test" is usually false — measure before
  settling for a source-level proxy.
- **Grep the output for the placeholder family**, not just the one you were
  chasing: `?meta:`, `?@`, `**@key?**` are the same class and cost one regex
  each once you already hold the rendered text.
- **Pair it with a static resolver for the fast tier.** Parse the include tree
  for macros and resolve them against the *generated* metadata file — not the
  Python dict that produces it. It needs no toolchain, so it still covers the
  fresh worktrees where the render skips for want of a gitignored generated
  include.
- **Front-matter presence ≠ resolvable.** Quarto keeps some header keys for
  itself: `format`, `metadata-files`, and `number-sections` all render
  `?meta:` despite sitting in the YAML header. Establish such a set by probing
  a real render across every document, then pin it with a test that re-renders
  it, so a toolchain upgrade cannot change the answer silently.
- **Discover documents by glob and assert the glob found something.** An empty
  parametrize list is a pass with exit 0, so a directory rename removes every
  guard at once, silently.
