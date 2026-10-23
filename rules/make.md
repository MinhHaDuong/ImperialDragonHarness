---
paths:
  - "**/Makefile"
  - "**/*.mk"
last-reviewed: 2026-10-23
---
# Make rules

Loaded when a Makefile is touched. Moved out of `coding-python.md` (2026-10-23):
these bind any Makefile, Python or not. The `RUN` prefix for Python recipes
stays in [coding-python.md](./coding-python.md); the manuscript-specific gate
is [manuscript-build.md](./manuscript-build.md).

- **One output per rule.** Each target should produce a known file so timestamps work.
- **The target must be the exact path the recipe writes.** `make` checks the recipe's *exit code*, not whether the file appeared — so a tool that writes elsewhere leaves the rule "succeeding" (exit 0) with `$@` absent, silently breaking every downstream consumer and forcing an eternal rebuild. The trap bites when a tool ignores the output path you configured: Quarto's single-file `quarto render <f>.qmd` ignores the project `output-dir` and writes *next to the source*. Name the target where the tool actually writes, or `mv … $@` in the recipe (climate-finance-het deliverables/ reorg, 2026-07-10 — a Makefile-text test can't catch this; only a real build does).
- **Sentinel stamps for dynamic outputs.** Use a stamp file when a script produces data-dependent filenames.
- **No `.PHONY` for real work.** Use `.PHONY` only for aliases.
- **No hand-curated data in the pipeline.** Every CSV/tex file referenced by slides or report must have a Makefile target that generates it from `measurements.jsonl` or another tracked source.
- **Split the build by workpackage.** Analysis (Python/R, data access) and writing (LaTeX, Quarto) workpackages live in separate Makefiles. A writing-side build must produce the manuscript from handoff artifacts alone — no `uv run`, no data fetch. Enables clean-room builds and enforces the artifact discipline in [prose/workpackages.md](./prose/workpackages.md).
