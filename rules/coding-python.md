<!-- last-reviewed: 2026-08-14 -->
# Coding Rules

## Python (3.10+)

Style:
- Built-in generics: `list[str]`, `dict[str, int]`, `str | None`. Never `from typing import List, Dict, Tuple, Optional`.
- `X | Y` union syntax, not `Union[X, Y]`. No `from __future__ import annotations`.
- Imports grouped at the top of the file; keep only imports that are used. Ruff flags unused imports (F401) and unsorted blocks (I001) via the post-edit hook, but it only *reports* — it does not auto-delete or reorder (`--unfixable F401,I001,UP`), so an import that is briefly unused while you wire up its first use is safe; finish the usage and the report clears.
- No ABC classes. Use Protocol for structural subtyping if needed.
- Type hints where they clarify intent. Skip where they add noise.
- Assertions at system boundaries. Trust internal code.

Script structure:
- **Every entry point gets argparse.** If `__name__ == "__main__"` exists, it gets an `ArgumentParser`.
- **Lean main() functions.** Delegate to well-named helpers.
- **No hardcoded paths.** Use `--output` and `--named-input` CLI params, with defaults from config.
- **No `sys.path` hacks.** Use proper packaging (`pyproject.toml`).
- **Logging, not print.** Use `logging` module.

Dependencies: **always `uv sync`** (never pip). `uv run python scripts/...` to execute.

**Keep the uv cache and the project env on one filesystem.** uv hardlinks wheels from its cache (`UV_CACHE_DIR`) into `.venv`. Hardlinks cannot cross filesystems, so when cache and env sit on different ones uv silently copies the whole dependency closure (≈1.8 GB with torch) into every env — slow enough to make worktree creation time out and fail. If big regenerable things live on a separate disk, put the env there too, beside the cache, and symlink `.venv` to it (symlinks cross filesystems; hardlinks do not). Pre-create the target first: a dangling `.venv` symlink makes `uv run` error.

## Testing

- Tests live in `tests/test_<module>.py`. A new script or changed behavior starts with a test.
- `make check-fast`: fast tier only (`-m "not slow and not integration and not adherence"`), < 30 s — run during development.
- `make lint`: adherence tier only (`-m adherence`) — ruff / mypy / hygiene / contracts.
- `make check`: everything — the default pre-PR gate. A project's AGENTS.md may declare a lighter merge gate (e.g. `check-fast` + `lint`) when an ex-post full-suite run on main covers the slow tiers; the project contract wins (climate-finance-het, 2026-07-28). No coverage is lost by tiering a test slower; `make check` still runs it, per PR or ex post.
- **pytest spawn failure under the rtk hook.** If `pytest` or `python3 -m pytest` dies under the rtk Bash hook with `Failed to spawn process: No such file or directory (os error 2)`, run it as `rtk proxy python3 -m pytest …` to bypass the rewrite. rtk has no command-passthrough knob (checked `~/.config/rtk/config.toml`, 2026-07-11), so this is the standing workaround. The spawn error can also mean the pytest shim itself is broken — a stale pipx venv after a Python upgrade leaves `~/.local/bin/pytest` pointing at a deleted interpreter; `pipx list` confirms it, `pipx reinstall-all` fixes it.

Every Python project must have a ruff adherence test so lint failures are caught locally before CI. Declare `ruff` as a **pinned dev dependency** (e.g. `ruff>=0.11,<0.12`) and `uv lock` it — an adherence guard's verdict must be machine-independent, and an ambient/system ruff drifts between machines and silently changes rules on upgrade. Resolve the binary with `shutil.which`, not a nested `uv run ruff`: pytest already runs inside the project venv under `make lint`, so the pinned ruff is on PATH; a nested `uv run` re-enters uv from inside uv, spawns a subprocess per call, and breaks under `UV_NO_SYNC` in a clean CI/cloud container.

```python
@pytest.mark.adherence
def test_ruff():
    ruff = shutil.which("ruff")
    assert ruff is not None, "ruff not found — declare it as a pinned dev dependency"
    result = subprocess.run([ruff, "check", "."], capture_output=True)
    assert result.returncode == 0, result.stdout.decode()
```

A project that maintains a bibliography (manuscript, report, docs) should also
have a **cited-works-availability** adherence test: assert every work cited in
the prose resolves to a locally-stored fulltext (a `file=`/attachment whose PDF
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

Adherence is a gate, not a unit tier: `make lint` (`-m adherence`) runs it apart from the logic loop, so `make check-fast` stays pure and quick. The named dependencies are examples of the *heavy numerical dependency* category, not a fixed list.

When writing new tests:
- CLI flag presence: check via source inspection (`open().read()` + string match), not subprocess `--help`.
- Tests using `subprocess.run()` or `time.sleep()`: mark `@pytest.mark.integration`.
- Tests needing heavy modules only for `inspect.getsource()`: read the file directly instead.

Two patterns keep the fast tier honest — generalizable, adopt per project (reference implementations live in the climate-finance-het repo, ticket 0216):
- **Collection-time auto-mark** — a conftest hook marks any test whose module imports a heavy dependency `slow`, so the per-worker import tax never lands in the fast loop.
- **Duration ratchet** — an `adherence` test fails when a fast-path test exceeds a recorded budget, catching heavy *compute* that no heavy *import* reveals.

## Build (Make)

- **One output per rule.** Each target should produce a known file so timestamps work.
- **The target must be the exact path the recipe writes.** `make` checks the recipe's *exit code*, not whether the file appeared — so a tool that writes elsewhere leaves the rule "succeeding" (exit 0) with `$@` absent, silently breaking every downstream consumer and forcing an eternal rebuild. The trap bites when a tool ignores the output path you configured: Quarto's single-file `quarto render <f>.qmd` ignores the project `output-dir` and writes *next to the source*. Name the target where the tool actually writes, or `mv … $@` in the recipe (climate-finance-het deliverables/ reorg, 2026-07-10 — a Makefile-text test can't catch this; only a real build does).
- **Sentinel stamps for dynamic outputs.** Use a stamp file when a script produces data-dependent filenames.
- **No `.PHONY` for real work.** Use `.PHONY` only for aliases.
- **No hand-curated data in the pipeline.** Every CSV/tex file referenced by slides or report must have a Makefile target that generates it from `measurements.jsonl` or another tracked source.
- **Split the build by workpackage.** Analysis (Python/R, data access) and writing (LaTeX, Quarto) workpackages live in separate Makefiles. A writing-side build must produce the manuscript from handoff artifacts alone — no `uv run`, no data fetch. Enables clean-room builds and enforces the artifact discipline in [git.md](./git.md).
