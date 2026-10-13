# Portable simplification review — PR 1386

```yaml
simplify_route: portable
verdict: CLEAN
reviewed_sha: b731a7287d1448ae57396197c3a9a219bbe9715a
findings: []
must_fix: []
```

Separate phase-5 invocation; adherence approval was not reused as simplification evidence. Reviewer route supplied by caller: gpt-6.1-sol, medium, OpenAI. This is same-family replication, not a decorrelated independent perspective.

`review-pr-anchor.py 1386 --worktree /home/haduong/.agents/.claude/worktrees/review-1386` passed before and after examination, at the SHA above, with nonempty diff against origin/main. Logs: simplify-anchor-before.log and simplify-anchor-after.log. The initial sandbox metadata read failed; approved host network reads recovered it. Source remained read-only, no commits/pushes/edits.

Paths examined: actual `git -C` diff roster and content for README.md, STATE.md, docs/arena-integration.md, docs/2026-10-06-routing-doctrine-brief.md, pyproject.toml, skills/route/SKILL.md, skills/route/grid.json, skills/route/grid-coverage.json, tests/test_route_grid.py; removal roster for arena scripts/reports/tests/protocol. Surrounding integration evidence read from the independent arena checkout: migration/README.md, migration/from-harness-2026-10-13.json, tests/test_tournament_analysis.py, tests/test_tournament_report_completion.py, tests/child_env.py, tests/fixtures/route/{grid.json,grid-coverage.json}, scripts/tournament-analysis.py, skills/arena/SKILL.md. This pass evaluates simplification, not a fresh full migration validation.

Concrete candidates considered:

- **Replace the migration manifest with another tracking mechanism:** retain the existing manifest. It already records a single source harness commit and per-file original hashes, and docs/arena-integration.md:35–38 links it directly. A new checksum or inventory format would duplicate the authoritative migration record without reducing the integration contract.
- **Remove copied harness support from arena:** tests/child_env.py is the only copied helper identified here. It supplies the explicitly used `env=child_env()` calls at arena tests/test_tournament_report_completion.py:160 and :178. Retaining the small local helper avoids coupling standalone arena tests to harness imports and keeps subprocess-loader isolation. No copied live route skill or live route registry is present under arena skills/.
- **Eliminate duplicated route fixtures:** arena tests use frozen fixtures, while the harness owns live routing. The fixture grid is consumed by arena test_tournament_analysis.py:66, :83–85 and test_tournament_report_completion.py:111. Replacing it with live harness reads would reintroduce a cross-repository test dependency and allow later routing edits to alter historical arena tests. The duplicated join assertion exercises different data instances; retaining it in both repositories is justified.
- **Generalize the new route test:** tests/test_route_grid.py:5–12 is already a small direct contract for the retained live files. Sharing it through a new library or importing arena analysis would add a dependency larger than the duplicated assertion block. No safe simplification is needed.
- **Add a wrapper for refresh roots:** docs/arena-integration.md:18–19 invokes the existing arena CLI with explicit source and destination. arena scripts/tournament-analysis.py:233–248 already owns default arena resolution and sibling coverage output; the harness command reuses this mechanism. A wrapper would duplicate option handling. Explicit roots make the boundary reviewable and preserve the requirement to refresh routes.json manually in the same review pass.

No actionable simplification preserves the migration's standalone ownership and frozen evidence better than the present small integration contract. No must-fix or optional change proposed.
