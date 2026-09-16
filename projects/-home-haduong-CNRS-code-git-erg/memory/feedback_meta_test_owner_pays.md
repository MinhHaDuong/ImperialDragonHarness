---
name: meta-test-owner-pays
description: Design coverage meta-tests so the PR that adds the key/command pays for its fixture; expect the first CI catch to hit a parallel in-flight PR
metadata: 
  node_type: memory
  type: feedback
  originSessionId: df33291b-b7e0-4267-8f65-a75c859e7ac1
---

The 0227 fixture-coverage meta-test (every `v1HeaderKeys` key needs an invalid fixture) caught its first prey on its maiden CI run: parallel ticket 0222 merged `Superseded-by` minutes earlier without a fixture. By design the key's OWNER pays for the fixture — but when the owner already merged, the guard's own PR absorbs the fixture (never an exemption); 2026-06-04, PR #270 added `0001-bad-superseded-by.erg` for 0222's key.

**Why:** self-syncing guards (iterate the registry/map, demand coverage) convert silent drift into a red CI; the failure lands on whichever PR is in flight when the race resolves.

**How to apply:** when adding such a guard, (1) check `origin/main` for keys added since your branch base right before merge; (2) treat a post-rebase CI failure of the guard as the guard WORKING — add the missing fixture in your PR, do not exempt. Symmetric command-axis guard: ticket 0236 (implemented same day, PR #279).
