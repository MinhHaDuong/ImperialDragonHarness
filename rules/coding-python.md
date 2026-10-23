---
paths:
  - "**/*.py"
last-reviewed: 2026-10-22
---
# Coding Rules

## Python (3.10+) style

- Imports grouped at the top of the file, sorted; keep only imports that are used. Ruff flags unused imports (F401) and unsorted blocks (I001); run `ruff check` before committing, since nothing lints on edit and the ruff adherence test is the gate.
- Type hints where they clarify intent. Skip where they add noise.
- Built-in generics: `list[str]`, `dict[str, int]`, `str | None`. Never `from typing import List, Dict, Tuple, Optional`.
- `X | Y` union syntax, not `Union[X, Y]`. No `from __future__ import annotations`.
- No ABC classes. Use Protocol for structural subtyping if needed.
- Assertions at system boundaries. Trust internal code.
- Every entry point gets argparse. If `__name__ == "__main__"` exists, it gets an `ArgumentParser`.
- Lean main() functions. Delegate to well-named helpers.
- No hardcoded paths. Use `--output` and `--named-input` CLI params, with defaults from config.
- No `sys.path` hacks. Use proper packaging (`pyproject.toml`).
- Logging, not print. Use `logging` module.

## Environment

Principles which settle any case the rules below do not cover:
1. Do not pollute the system: what the GitHub Ubuntu runner image lacks is exotic.
2. uv, not pip.
3. Commit to Linux, with no gratuitous incompatibility.
4. The uv cache is machine-level state: never synced, never snapshotted.

Environment rules: **uv, never pip.**
- Dependencies live in `pyproject.toml` with `uv.lock` committed (`--frozen` fails without it); no hand-kept `requirements.txt` (a file generated from the lock, for a deliverable that needs one, is fine). A repo that is not a package sets `[tool.uv] package = false`. `pytest`, `pytest-xdist` and a pinned `ruff` go in the `dev` group. `uv sync` builds the env, `uv run` executes (`uv run --script` for a script with inline metadata). A legacy repo (`requirements.txt`, hand-made venv) migrates when next touched.
- A Python tool absent from the `ubuntu-latest` runner readme is exotic and comes from the lock (or a script's inline metadata), never from the system: it ships no `uv`, `ruff` or `pytest` (actions/runner-images, `Ubuntu2404-Readme.md`, checked 2026-10-22; recheck when `ubuntu-latest` moves to 26.04). uv is the one exception; CI installs it with `astral-sh/setup-uv`, then `uv sync --locked`.
- Makefile: one `RUN` prefix at the top, prefixing the actual command on each recipe line that runs Python (`$(RUN) python3 -m pytest`, `$(RUN) ./scripts/x.py`), no `PYTHON` variable (copy the harness Makefile's definition: bare inside an activated env, `uv run --frozen` otherwise; bare when uv is absent is a degraded mode where the locked tools must already be on PATH, not a second way to get them). Where `RUN` expands to `uv run`, it needs a synced env to beat the PATH: with `UV_NO_SYNC` set and no synced `.venv` it runs the ambient `ruff` or `pytest`, so a sandbox runs `uv sync` once first (`uv sync` itself ignores `UV_NO_SYNC`; tested on uv 0.11.28). A build that only writes LaTeX or Quarto from handoff artifacts needs no `RUN` (see Build).
- Linux is the target. Use `pathlib`, `/` separators and `env` shebangs; a Linux-only tool needs a concrete need that no portable tool meets.

The cache is machine-local and rebuildable from `uv.lock`: keep `UV_CACHE_DIR` and `.venv` out of any synced, snapshotted or backed-up tree by excluding them there (a symlink target included), which is host configuration, not repo content.

**Keep the uv cache and the project env linkable.** uv hardlinks wheels from its cache (`UV_CACHE_DIR`) into `.venv`. Hardlinks cannot cross filesystems, nor btrfs subvolumes: when cache and env sit on different ones uv falls back to copying the whole dependency closure (≈1.8 GB with torch) into every env — slow enough to make worktree creation time out and fail. Either keep the cache and the projects on the same subvolume, or set `UV_LINK_MODE=clone`: a reflink works across subvolumes of one btrfs filesystem. Never `UV_LINK_MODE=copy`. Across genuinely different filesystems neither works: put the env beside the cache and symlink `.venv` to it (symlinks cross filesystems); that env falls under the same sync and snapshot exclusion as the cache. Pre-create the target first: a dangling `.venv` symlink makes `uv run` error.

## Testing

- Tests live in `tests/test_<module>.py`. A new script or changed behavior starts with a test.
- When testins get too slow, suggests the `/pulse` test-doctor skill.
- The harness does not maintain reg/green test caches for smart test selection, but a project might.
- `make check-fast`: fast tier only (`-m "not slow and not integration and not adherence"`), aim to stay under 10 s, it runs during development.
- `make lint`: adherence tier only (`-m adherence`) — ruff / mypy / hygiene / contracts.
- `make check`: everything. This is the default pre-PR gate for code changes, unless the project declared a lighter merge gate (e.g. `check-fast` + `lint`). Pure tickets, doc or comment-only changes must bypass the full test rerun.
- **pytest spawn failure under the rtk hook.** If `pytest` or `python3 -m pytest` dies under the rtk Bash hook with `Failed to spawn process: No such file or directory (os error 2)`, run it as `rtk proxy python3 -m pytest …` to bypass the rewrite. The spawn error can also mean the pytest shim itself is broken.

Every Python project must have a ruff test so lint failures are caught locally before CI. Declare `ruff` as a pinned dev dependency (e.g. `ruff>=0.11,<0.12`) and `uv lock` it. Resolve the binary with `shutil.which`, not a nested `uv run ruff`: pytest already runs inside the project venv under `make lint`, so the pinned ruff is on PATH; a nested `uv run` re-enters uv from inside uv, spawns a subprocess per call, and breaks under `UV_NO_SYNC` in a clean CI/cloud container.

```python
@pytest.mark.adherence
def test_ruff():
    ruff = shutil.which("ruff")
    assert ruff is not None, "ruff not found — declare it as a pinned dev dependency"
    result = subprocess.run([ruff, "check", "."], capture_output=True)
    assert result.returncode == 0, result.stdout.decode()
```

A project that maintains a bibliography (manuscript, report, docs) should also have a **cited-works-availability** test:
assert every work cited in the prose resolves to a locally-stored fulltext (a `file=`/attachment whose PDF
sits in the reference folder) or an explicit allowlist of the genuinely
unattainable. This turns the scholarly-integrity norm "cite only what you keep
locally" (`prose/_all.md`) into a mechanical gate. Keep the allowlist
source-agnostic about *how* works are acquired — that is the author's call — and
add a redundant-entry check so a work is removed from the list once its fulltext
lands. Reference implementation: `tests/test_cited_works_available.py` +
`config/no-fulltext-allowlist.txt` in climate-finance-het (ticket 0189).

Classify each test by **cost**, not by the mechanism it happens to use:

| Tier | Marker | Belongs here | Gate |
|------|--------|--------------|------|
| fast | *(none)* | pure-Python logic; no heavy numerical dependency (dcor / torch / ot / sentence_transformers / matplotlib), no subprocess, no lint | `make check-fast` |
| integration | `@pytest.mark.integration` | spawns a subprocess / drives a script / sleep-based timing | `make check` |
| slow | `@pytest.mark.slow` | network, real data, a heavy numerical dependency, or heavy compute | `make check` |
| adherence | `@pytest.mark.adherence` | ruff / mypy / hygiene / contracts | `make lint` |

Adherence is a gate, not a unit tier: `make lint` (`-m adherence`) runs it apart from the logic loop, so `make check-fast` stays pure and quick.
The named dependencies are examples of the *heavy numerical dependency* category, not a fixed list.

When writing new tests:
- CLI flag presence: check via source inspection (`open().read()` + string match), not subprocess `--help`.
- Tests using `subprocess.run()` or `time.sleep()`: mark `@pytest.mark.integration`.
- Tests needing heavy modules only for `inspect.getsource()`: read the file directly instead.

Two patterns keep the fast tier honest — generalizable, adopt per project:
- **Collection-time auto-mark** — a conftest hook marks any test whose module imports a heavy dependency `slow`, so the per-worker import tax never lands in the fast loop.
- **Duration ratchet** — an `adherence` test fails when a fast-path test exceeds a recorded budget, catching heavy *compute* that no heavy *import* reveals.

## Build (Make)

- **One output per rule.** Each target should produce a known file so timestamps work.
- **The target must be the exact path the recipe writes.** `make` checks the recipe's *exit code*, not whether the file appeared — so a tool that writes elsewhere leaves the rule "succeeding" (exit 0) with `$@` absent, silently breaking every downstream consumer and forcing an eternal rebuild. The trap bites when a tool ignores the output path you configured: Quarto's single-file `quarto render <f>.qmd` ignores the project `output-dir` and writes *next to the source*. Name the target where the tool actually writes, or `mv … $@` in the recipe (climate-finance-het deliverables/ reorg, 2026-07-10 — a Makefile-text test can't catch this; only a real build does).
- **Sentinel stamps for dynamic outputs.** Use a stamp file when a script produces data-dependent filenames.
- **No `.PHONY` for real work.** Use `.PHONY` only for aliases.
- **No hand-curated data in the pipeline.** Every CSV/tex file referenced by slides or report must have a Makefile target that generates it from `measurements.jsonl` or another tracked source.
- **Split the build by workpackage.** Analysis (Python/R, data access) and writing (LaTeX, Quarto) workpackages live in separate Makefiles. A writing-side build must produce the manuscript from handoff artifacts alone — no `uv run`, no data fetch. Enables clean-room builds and enforces the artifact discipline in [prose/workpackages.md](./prose/workpackages.md).

## Data pitfalls

- **Null keys.** `dropna` the key before `merge(on=...)`: pandas matches NaN keys to each other, and a few thousand nulls can explode a join into tens of millions of rows. A float NaN is truthy, so `str(x or "")` yields `"nan"`, as does `row.get(k, "")` when the key holds NaN; blank with `pd.isna` and grep shipped artifacts for `\bnan\b`.
- **Human judgments never live in a regenerable file.** Keep them in their own append-only artifact keyed by (item, annotator); a generator that emits a fill-me-in column exits non-zero if the target already holds annotations.
- **JSON newlines.** A single-object JSON file ends with exactly one newline; JSONL writers add no trailing blank line.
