---
paths:
  - "**/*.py"
last-reviewed: 2026-10-22
---
# Coding rules — Python

## Python (3.10+) style

- Run `ruff check` before committing: nothing lints on edit, and the ruff adherence test is the gate.
- Type hints where they clarify intent; neither required everywhere nor refused. Skip where they add noise.
- Built-in generics and `X | Y` unions (`list[str]`, `str | None`); never `typing.List`, `Dict`, `Tuple`, `Optional`, `Union`, and no `from __future__ import annotations`.
- No ABC classes. Use Protocol for structural subtyping if needed.
- Assertions at system boundaries. Trust internal code.
- Every entry point gets argparse. If `__name__ == "__main__"` exists, it gets an `ArgumentParser`.
- No hardcoded paths: inputs and `--output` are CLI parameters with defaults.
- No `sys.path` hacks. Use proper packaging (`pyproject.toml`).
- Logging, not print. Use `logging` module.

## Environment

Principles which settle any case the rules below do not cover:
1. Do not pollute the system: a project declares every tool it runs beyond a bare Linux base (shell, coreutils, git, make).
2. uv, not pip.
3. Commit to Linux, with no gratuitous incompatibility.
4. The uv cache and `.venv` are machine state: never synced, snapshotted or backed up (host configuration, not repo content).

Rules:
- Commit `pyproject.toml` and `uv.lock` (`--frozen` fails without it); generate any required `requirements.txt` from the lock. A repo that is not a package sets `[tool.uv] package = false`. `pytest`, `pytest-xdist` and a pinned `ruff` go in the `dev` group. A legacy repo (`requirements.txt`, hand-made venv) migrates when next touched.
- Every Python tool a project runs comes from its lock (or a script's inline metadata), never from the system: `ruff` and `pytest` included. uv is the one exception, the bootstrap that the host or CI installs before `uv sync --locked`.
- Makefile recipes that run Python take the `RUN` prefix: see [make.md](./make.md).
- Linux is the target. Use `pathlib`, `/` separators and `env` shebangs; a Linux-only tool needs a concrete need that no portable tool meets.


**Keep the uv cache and the project env linkable.** When they sit on different filesystems or btrfs subvolumes, uv cannot hardlink and copies the whole dependency closure (≈1.8 GB with torch) into every env, which has made worktree creation time out. Keep both on one subvolume, or set `UV_LINK_MODE=clone` (a reflink works across subvolumes of one btrfs filesystem); never `copy`. Across genuinely different filesystems, put the env beside the cache and symlink `.venv` to it, pre-creating the target (a dangling `.venv` symlink makes `uv run` error); that env is excluded from sync and snapshots like the cache.

## Testing

- Tests live in `tests/test_<module>.py`. A new script or changed behavior starts with a test.
- When tests get too slow, suggest the test-doctor skill.
- `make check-fast`: fast tier only (`-m "not slow and not integration and not adherence"`), under 10 s, the development loop.
- `make lint`: adherence tier only (`-m adherence`) — ruff / mypy / hygiene / contracts.
- `make check`: everything; a project's full gate unless it declares a lighter one (e.g. `check-fast` + `lint`).
- **pytest spawn failure under the rtk hook.** If `pytest` or `python3 -m pytest` dies under the rtk Bash hook with `Failed to spawn process: No such file or directory (os error 2)`, run it as `rtk proxy python3 -m pytest …` to bypass the rewrite. If that fails too, the pytest shim is stale (a pipx venv after a Python upgrade leaves `~/.local/bin/pytest` on a deleted interpreter): `pipx list` confirms it, `pipx reinstall-all` fixes it.

Every Python project has an `adherence` ruff test running the locked ruff, resolved with `shutil.which`, not a nested `uv run ruff`: pytest already runs inside the project venv under `make lint`, and a nested `uv run` re-enters uv from inside uv and breaks under `UV_NO_SYNC` in a clean CI/cloud container. Reference: `tests/test_ruff.py` in the harness.

Test tiers, by **cost**:

| Tier | Marker | Belongs here | Gate |
|------|--------|--------------|------|
| fast | *(none)* | pure-Python logic; no heavy numerical dependency (dcor / torch / ot / sentence_transformers / matplotlib), no subprocess, no lint | `make check-fast` |
| integration | `@pytest.mark.integration` | spawns a subprocess / drives a script / sleep-based timing | `make check` |
| slow | `@pytest.mark.slow` | network, real data, a heavy numerical dependency, or heavy compute | `make check` |
| adherence | `@pytest.mark.adherence` | ruff / mypy / hygiene / contracts | `make lint` |

When writing new tests:
- CLI flag presence: check via source inspection (`open().read()` + string match), not subprocess `--help`.
- Tests needing heavy modules only for `inspect.getsource()`: read the file directly instead.

Two patterns keep the fast tier honest — generalizable, adopt per project:
- **Collection-time auto-mark** — a conftest hook marks any test whose module imports a heavy dependency `slow`, so the per-worker import tax never lands in the fast loop.
- **Duration ratchet** — an `adherence` test fails when a fast-path test exceeds a recorded budget, catching heavy *compute* that no heavy *import* reveals.

## Data pitfalls

- **Null keys.** `dropna` the key before `merge(on=...)`: pandas matches NaN keys to each other, and a few thousand nulls can explode a join into tens of millions of rows. A float NaN is truthy, so `str(x or "")` yields `"nan"`, as does `row.get(k, "")` when the key holds NaN; blank with `pd.isna` and grep shipped artifacts for `\bnan\b`.
- **Human judgments never live in a regenerable file.** Keep them in their own append-only artifact keyed by (item, annotator); a generator that emits a fill-me-in column exits non-zero if the target already holds annotations.
- **JSON newlines.** A single-object JSON file ends with exactly one newline; JSONL writers add no trailing blank line.
