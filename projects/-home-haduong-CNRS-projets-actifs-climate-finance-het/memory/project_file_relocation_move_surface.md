---
name: project_file_relocation_move_surface
description: "Relocating a script/entry-point in climate-finance-het touches 8 surfaces, not just git mv — the full repoint checklist"
metadata: 
  node_type: memory
  type: project
  originSessionId: d329f489-e346-4cba-8c47-36d92cd64019
---

Moving a `scripts/*.py` entry point to a subdir (or renaming it) in
climate-finance-het is **never** just `git mv`. The 0240 reorg (132 files across
qa→harvest→analysis→figures) discovered the surface incrementally — each move
found one more the prior missed. The complete repoint checklist:

1. **Build refs** — `Makefile` + `scripts/analysis/*.mk` + `deliverables/*/*.mk`
   (rule prerequisites AND recipe paths). A rule line often mixes a mover with
   stay-flat libs (`plot_style.py`, `utils.py`) — repoint only the mover.
2. **`dvc.yaml`** — Phase-1 `catalog_/enrich_/corpus_/qa_` scripts are dvc
   stages; repoint `cmd:` and `deps:`. A stale dvc dep is a silent dangling dep
   (no guard catches it). (`dvc.lock` self-heals on next `dvc repro` — don't
   hand-edit it.)
3. **Test refs, 3 kinds** — bare-name `from X import` (subdirs aren't source
   roots), `spec_from_file_location("scripts/X.py")`, source-inspection
   `open("scripts/X.py").read()`.
4. **Doc provenance** — `deliverables/_shared/_includes/*.md`, `docs/*.md`
   (incl. `editorial-brief.md`), `.agent/guidelines/*.md`, the moved file's own
   docstring. Path lines only, no prose change.
5. **`pyproject.toml` per-file-ignores** — a `[tool.ruff.lint.per-file-ignores]`
   keyed on `"scripts/X.py"` narrows on the move and resurfaces intentional
   F401s as errors ([[feedback_ruff_fix_breaks_reexport_facades]]).
6. **Subprocess-from-foreign-cwd** — a test that subprocess-runs a moved script
   from a tmp dir needs `tests/_source_roots.py::source_root_env()` (its own dir
   is no longer the flat root).
7. **Guard predicates** — scans gated on `name.startswith(PREFIX)` must use
   `os.path.basename(name).startswith(...)`, or every subdir'd file drops out
   silently ([[feedback_moving_files_narrows_guard_globs]]).
8. **Archive cp-loops** — `build/build_*_archive.sh` must `cp --parents` the real
   path, not a flat `cp "scripts/$s"` (ticket 0261).

**Verify a move** by recipe-identity (`make -n <target>` differs only by the
path segment — the [[feedback_bytecheck_old_vs_new_not_golden]] discipline for
build graphs) + a **repo-wide union grep** at integration time, NOT per-PR greps
alone: the 0240 integration sweep caught a dangling `venues.mk` ref that all
per-move greps + green `make check-fast` missed (green tests never build).
Imports resolve because the repo puts source roots (`scripts` +
`libs/openalex-corpus/src`) on the path in every execution context — see
architecture.md § Shared conventions (ticket 0253); a move needs no `import`
edit inside the moved file.
