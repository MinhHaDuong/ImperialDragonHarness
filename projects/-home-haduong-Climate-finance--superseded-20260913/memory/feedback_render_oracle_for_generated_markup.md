---
name: feedback_render_oracle_for_generated_markup
description: "A generated file that goes through a renderer needs a test on the rendered output, not the source — and the emitter owns escaping for any markup pandoc never sees."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cc257f08-8194-48e0-8227-e34bc61ce80c
  modified: 2026-07-27T18:45:25.693Z
---

When a script emits markup (LaTeX, Markdown) that a renderer later processes,
test the **rendered** output, not the emitted source. A source-level assertion
cannot see a rendering defect — the emitted file can be character-perfect and
the published page still wrong.

**Why:** ticket 0325 (2026-07-27). `render_markdown_table()` emitted a
raw-LaTeX `longtable` inside a ```` ```{=latex} ```` block. Pandoc never
inspects raw blocks, so the emitter alone owned escaping, and it escaped only
`& % # _`. The data paper's PDF published `df[ df['is_flagged'] | ...]` — the
tilde eaten as a non-breaking space, inverting the filter recipe into its
complement — while `tab_variables.md` on disk carried a faithful `~` the whole
way. Every existing test passed. Found by an external peer-review panel reading
the *PDF*. The same class hit `render_codebook()`: a raw `|` ends a Markdown
pipe-table cell, so the Zenodo-deposited codebook shipped the recipe truncated
at the pipe.

**How to apply:**
- Build the artifact in the test and read it back: render to PDF and compare
  `pdftotext` extraction; render Markdown through pandoc and inspect the HTML
  cell. Both run in seconds and are worth it.
- Make the oracle the *sibling pipeline*, not a second copy of the escaping
  table: typeset each value twice in one document — once through the emitter's
  raw block, once as ordinary Markdown down the renderer's own path — and
  require the extracted text to match. Asserting on expected escape strings
  only restates the implementation.
- Mirror pandoc's escaping when emitting raw LaTeX, including its smart
  punctuation (`...` → `…`), or the raw block drifts typographically from the
  prose around it.
- Escaping rules are context-dependent inside one cell: CommonMark reads a
  backslash as an escape in prose but literally inside a code span, so prose
  and code spans need separate rules. Verify each candidate rule by rendering,
  not by reasoning — checked against real pandoc, both the pipe-only rule and
  the escape-everything rule corrupt different inputs.
- Regenerate the artifact in the same PR when its generator changes: a Makefile
  dependency on the emitter means the next plain `make` overwrites a
  hand-edited generated file. See [[feedback_vars_file_provenance]].
- **Sweep by shape, file by reachability.** The shape is cheap to grep — any
  emitter that interpolates a value into markup it does not escape. Whether it
  deserves a ticket depends on whether the interpolated value can actually
  carry the character: free text from the corpus (title, journal, author) can;
  counts, percentages, and curated labels cannot. Check the real data, not
  intuition — `refined_works.csv` turned out to hold 10 journal names and 14
  titles containing a literal `|` (bilingual names joined with a pipe), which
  is what made the venue-table emitters worth ticketing (0339). By the same
  test, `compute_vars.py`'s `write_yaml()` has the identical shape — it hand-
  builds YAML and escapes `"` but not `\` — yet every vars value is a
  formatted number, so it was reported, not ticketed.
- **Pick the escaper by the sink's decoder, not by the markup language.** One
  repo holds two HTML sinks that need opposite settings. `plot_genealogy_html.py`
  and `plot_alluvial_html.py` write `data-tooltip="…"` attributes that the
  browser's own DOM parser decodes, so `html.escape(quote=True)` is right there.
  `plot_interactive_corpus.py` hands its string to Plotly, whose
  `convertEntities` is an eight-entry lookup table carrying no `quot`, so the
  same `quote=True` would have published a literal `&quot;` in roughly
  two dozen core paper titles; `quote=False` is what that sink needs (ticket
  0341). The two sibling scripts already calling `html.escape` read as
  precedent worth copying, and copying them would have shipped the defect. Read
  the consumer's decoder before choosing, then record the reason at the call
  site — the next reader meets an inconsistency and wants to normalize it.
- **A sink whose decoder is a lookup table is not an HTML parser.** Plotly,
  many charting libraries, and most tooltip layers decode a fixed handful of
  entities and pass the rest through verbatim. Assuming full entity support is
  the trap; the eight-entry list is discoverable in the library source in
  minutes, and a rendered-output check catches what the reasoning misses.
