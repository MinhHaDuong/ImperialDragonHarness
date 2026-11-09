# Adherence review — PR 1386

```yaml
adherence: PASS
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

Reviewed branch `separate-arena` at `b731a7287d1448ae57396197c3a9a219bbe9715a`, against local `origin/main`. Source read-only; no commits, pushes or ticket edits.

Runner declaration: Makefile:28–32 explicitly declares the adherence gate; rules/coding-python.md:40–41 confirms `make lint`. `make -n lint` exit 0 resolved to `uv run --frozen python3 -m pytest tests/ -m adherence`. `make lint` with approved host access exited 0: **185 passed, 1397 deselected**, 7.18 seconds. Full output: `adherence-lint-host.log`. Initial sandbox run failed because `/data/cache/uv` was read-only (`adherence-lint.log`); a writable-cache retry encountered blocked DNS (`adherence-lint-retry.log`). Those environmental errors were recovered and are not test failures.

Static reference resolution skipped: no `.tex`, `.qmd` or `.bib` changes. `git diff --check origin/main...HEAD` passed. No trace supplied, so path-access scan was omitted.

Architecture semantic fallback performed by this reviewer, as caller authorized. No nested semantic reviewer was launched; concurrency seats were occupied. Identity/route: caller-selected gpt-6.1-sol, medium, OpenAI, same producer family; this is not an independent family perspective.

Rule evidence:
- rules/workflow.md, Rename and refactor sweeps: removal covers the arena protocol, runners, generators, reports, tests and numerical plotting dependencies; ownership remains explicitly documented at conception/arena-integration.md:9–12. Search found no surviving executable harness reference to removed scripts.
- rules/workflow.md, Validate pure refactors: conception/arena-integration.md:35–38 and tickets/1094-separate-arena-from-harness.erg:9 preserve migration manifest and byte/reproduction evidence. Cross-repository manifest and reproduction were not independently rechecked in this bounded adherence seat; they belong to the migration integration review.
- skills/route/SKILL.md, Update discipline: grid and coverage numeric/structural contents compare identically with origin/main after excluding documentary comments and role notes. Route doctrine now points to the independent producer at skills/route/SKILL.md:28–30 and conception/arena-integration.md:18–23.
- rules/coding-python.md, Testing and Dependencies: new tests/test_route_grid.py:5–12 checks the retained grid/coverage join without removed arena modules; removed matplotlib/numpy dependencies correspond to migrated plotting scripts. Dependency and ruff adherence tests passed.
- AGENTS.md, Skills Catalog: README.md removes the deleted arena skill; skill reference/frontmatter adherence tests passed. No memory files or historical journals changed.

No concrete semantic rule violation found. The evidence boundary is the harness diff and its adherence runner; standalone arena validation is recorded externally and remains a separate integration verification responsibility.
