<!-- last-reviewed: 2026-06-18 -->
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
- `make check-fast`: unit tests + lint, < 30 s — run during development.
- `make check`: full suite including integration + slow tests — run before opening a PR.

Every Python project must have a ruff adherence test so lint failures are caught locally before CI:

```python
@pytest.mark.adherence
def test_ruff():
    result = subprocess.run(["uv", "run", "ruff", "check", "."], capture_output=True)
    assert result.returncode == 0, result.stdout.decode()
```

| Marker | Meaning | Excluded from |
|--------|---------|---------------|
| *(none)* | Unit test — pure logic, no subprocess, no sleep | — |
| `@pytest.mark.integration` | Spawns subprocesses or uses sleep-based timing | `check-fast` |
| `@pytest.mark.slow` | Requires network access or real data | `check-fast` |

When writing new tests:
- CLI flag presence: check via source inspection (`open().read()` + string match), not subprocess `--help`.
- Tests using `subprocess.run()` or `time.sleep()`: mark `@pytest.mark.integration`.
- Tests needing heavy modules only for `inspect.getsource()`: read the file directly instead.

## Build (Make)

- **One output per rule.** Each target should produce a known file so timestamps work.
- **Sentinel stamps for dynamic outputs.** Use a stamp file when a script produces data-dependent filenames.
- **No `.PHONY` for real work.** Use `.PHONY` only for aliases.
- **No hand-curated data in the pipeline.** Every CSV/tex file referenced by slides or report must have a Makefile target that generates it from `measurements.jsonl` or another tracked source.
- **Split the build by workpackage.** Analysis (Python/R, data access) and writing (LaTeX, Quarto) workpackages live in separate Makefiles. A writing-side build must produce the manuscript from handoff artifacts alone — no `uv run`, no data fetch. Enables clean-room builds and enforces the artifact discipline in [git.md](./git.md).
