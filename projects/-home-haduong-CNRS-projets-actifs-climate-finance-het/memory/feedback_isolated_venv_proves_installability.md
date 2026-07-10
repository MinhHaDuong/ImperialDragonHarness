---
name: feedback_isolated_venv_proves_installability
description: "Green tests from an env that already has a dep don't prove a package installs; test in a fresh isolated venv"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d9716599-b52c-4dc7-baf5-da1344799cab
---

When extracting/packaging a library, a passing test suite run against the
**shared/host interpreter** does NOT prove the package is installable — that env
may already carry the dependency. In ticket 0170 the new `openalex-corpus`
package declared only `pandas` but `crawl.py` imported `requests`; "23/23 green"
via the shared `.venv` masked it, and a clean consumer install would have failed
at `import openalex_corpus`. A gaze reviewer caught it.

**Why:** installability is a property of the *declared* dependency closure, not
of whatever happens to be importable in the dev env. Shared envs hide missing
declarations.

**How to apply:** to verify a package installs, build a throwaway venv and
install it alone —
`uv venv .venv-check && VIRTUAL_ENV=$PWD/.venv-check uv pip install -e . && .venv-check/bin/python -c "import <pkg>"` —
then run its tests there. Gitignore the check-venv. Related: a package consumed
by a "pure/minimal-imports" host module needs a lazy `__init__` (PEP 562
`__getattr__`) so pure symbols don't drag heavy deps, and `py.typed` +
annotations so re-exporting call sites don't hit mypy `no-any-return`. See
[[feedback_manuscript_number_provenance]] for the sibling "verify against the
real artifact, not a convenient proxy" discipline.
