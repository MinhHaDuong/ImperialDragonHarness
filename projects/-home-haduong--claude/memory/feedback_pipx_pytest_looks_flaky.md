---
name: feedback_pipx_pytest_looks_flaky
description: The bare `pytest` on PATH is a pipx install without PyYAML; tests importing yaml fail under it and pass under `python3 -m pytest`, which reads as a flake
metadata:
  type: feedback
---

2026-09-29: two reviewers of PR #1060 each saw
`test_skill_subcommands_still_reach_perch` fail on a first run, then pass on
reruns. It was not random: it fails every time under `~/.local/bin/pytest`
(a pipx venv with no PyYAML) and passes 20/20 under `python3 -m pytest`, which
is what `make check` uses; PyYAML is in `requirements-dev.txt`.

**How to apply:** run tests with `python3 -m pytest` or `make check`, never the
bare `pytest`, and tell reviewer agents the same. A test that "fails once" is an
environment question before it is a flake: record the interpreter and the
traceback (with `RTK_DISABLED=1`, since the proxy cuts tracebacks) before
labelling anything flaky.
