# Python tool baseline: the GitHub runner facts behind rules/coding-python.md

Context: on 2026-10-30 the author ruled that rules name no forge (PR 2037)
and that forge specifics are implementation detail kept in memory: the rule
states the principle, memory holds how it is applied today. The Python rule
used to define an "exotic" tool against GitHub's `ubuntu-latest` runner image;
it now says every Python tool comes from the lock, uv excepted.

Facts (as of 2026-10-22, from the rule text it replaced):
- The `ubuntu-latest` runner image (actions/runner-images, `Ubuntu2404-Readme.md`)
  ships no `uv`, `ruff` or `pytest`. Recheck when `ubuntu-latest` moves to 26.04.
- This harness's CI installs uv with the `astral-sh/setup-uv` action, then runs
  `uv sync --locked`.
- The former baseline: what the runner image lacks counted as exotic and had to
  come from the lock; the new rule makes the lock the source for every Python
  tool, a stricter and forge-free reading of the same practice.
