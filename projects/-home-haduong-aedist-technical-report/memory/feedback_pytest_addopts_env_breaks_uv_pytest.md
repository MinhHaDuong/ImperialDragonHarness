---
name: feedback-pytest-addopts-env-breaks-uv-pytest
description: "Background-job env injects PYTEST_ADDOPTS=--cache-dir which this repo's pytest rejects — prefix pytest/make check with `env -u PYTEST_ADDOPTS`"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a7ab5764-47b2-427d-af56-e627422f2f08
---

In background-job sessions on padme, the environment carries
`PYTEST_ADDOPTS=--cache-dir=/data/cache/pytest`. This repo's pytest
(pyproject-configured) rejects `--cache-dir` as an unrecognized argument, so
`uv run pytest …` and `make check` fail with usage errors unrelated to the
code under test.

**Why:** the option belongs to a different tool/plugin set; the injection is
session-environment, not repo config. Hit twice in the 0538 raid (executor
agent, then orchestrator's `make check`).

**How to apply:** run `env -u PYTEST_ADDOPTS make check` (or prefix any
`uv run pytest` likewise) in this repo when the variable is present. A failing
`make check` with "unrecognized arguments: --cache-dir" is environmental, not
a regression.
