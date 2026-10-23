---
paths:
  - "**/Makefile"
  - "**/*.mk"
last-reviewed: 2026-10-23
---
# Make rules

A build that produces a document also reads [manuscript-build.md](./manuscript-build.md).

- **One output per rule.** Each target should produce a known file so timestamps work.
- **The target must be the exact path the recipe writes.** `make` checks the exit code, not whether the file appeared: a tool that writes elsewhere leaves the rule succeeding with `$@` absent and the target rebuilt forever. Quarto's single-file `quarto render <f>.qmd` ignores the project `output-dir` and writes next to the source. Name the target where the tool writes, or `mv … $@`; only a real build catches this.
- **`.DELETE_ON_ERROR:` at the top.** `make` leaves a target whose recipe failed; without it the bad output stays newer than its sources and the next `make` reports it up to date.
- **Python recipes take one `RUN` prefix**, defined at the top and prefixing the actual command on each recipe line that runs Python (`$(RUN) python3 -m pytest`, `$(RUN) ./scripts/x.py`), no `PYTHON` variable (copy the harness Makefile's definition: bare inside an activated env, `uv run --frozen` otherwise; bare when uv is absent is a degraded mode where the locked tools must already be on PATH, not a second way to get them). Where `RUN` expands to `uv run`, it needs a synced env to beat the PATH: with `UV_NO_SYNC` set and no synced `.venv` it runs the ambient `ruff` or `pytest`, so a sandbox runs `uv sync` once first (`uv sync` itself ignores `UV_NO_SYNC`; tested on uv 0.11.28).
- **No hand-curated data in the pipeline.** Every data file a manuscript or deck includes has a Makefile target that generates it from a tracked source.
- **Split the build by workpackage.** Analysis (Python/R, data access) and writing (LaTeX, Quarto) live in separate Makefiles. A writing-side build produces the manuscript from handoff artifacts alone: no `uv run`, no data fetch, so it builds clean-room ([prose/workpackages.md](./prose/workpackages.md)).
