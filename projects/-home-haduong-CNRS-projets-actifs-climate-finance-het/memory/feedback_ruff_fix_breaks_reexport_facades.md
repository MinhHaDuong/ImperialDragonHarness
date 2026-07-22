---
name: feedback_ruff_fix_breaks_reexport_facades
description: "ruff --fix silently guts re-export facades; verify with a reach-through import probe, and per-file-ignores go stale on rename"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 09065d34-1e60-425f-ac1f-6118c4153d3e
---

A repo-wide `ruff check . --fix` (ticket 0232) silently removed F401 "unused"
imports from **re-export facade** modules — modules whose imports exist only so
tests/scripts can do `from <facade> import <symbol>` for a symbol defined
elsewhere. `--fix` broke `catalog_openalex` (`fetch_query`, `build_filter`),
`catalog_syllabi` (whole `syllabi_*` blocks), and `compute_clustering_comparison`
(`build_tfidf_space`, `build_citation_space`). check-fast caught it as
ImportError, but only because those tests happened to run.

**Root cause of the silent breakage:** the project's `per-file-ignores` facade
exemptions had gone **stale after two script renames** — `collect_syllabi.py` →
`catalog_syllabi.py` and `compare_clustering.py` →
`compute_clustering_comparison.py`. The ignore still named the pre-rename file,
so the facade lost its F401 shield without anyone noticing until `--fix` ran.

**Why:** F401 cannot tell "unused" from "re-exported public surface." The only
signals are `__all__`, a `# noqa: F401`, or a `per-file-ignores` entry — and the
last silently detaches when the file is renamed.

**How to apply:**
- After ANY repo-wide `ruff --fix`, run a reach-through probe before trusting it:
  parse every `from <scripts_module> import X` in `tests/`, `importlib` the
  module, assert `hasattr(mod, X)`. Catches facade breakage the fast tier misses
  if the consuming test isn't run. (Probe script pattern worked in 0232.)
- When renaming a script that appears in `[tool.ruff.lint.per-file-ignores]`
  (or any config filename list), grep the config for the old basename in the
  same commit — the ignore does not follow the rename.
- Restore a broken facade by reverting the file to the pre-fix version and
  fixing the `per-file-ignores` name, OR restore just the consumed symbols with
  a per-line `# noqa: F401 -- re-exported`.

Related: [[feedback_grep_before_commit]], [[project_repo_layout_decision]].
The 0230 ruff adherence guard (still open, unblocked by 0232) will pin the
clean state so this can't silently regress.
