---
name: feedback-make-stamp-discipline
description: "Not all Make .done stamps are hacks: dynamic multi-output needs them, single-known-output dressed as a stamp is the hack — and .DELETE_ON_ERROR is what makes plain rules safe"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e8c40ecf-0bdc-4652-a245-d5dfe63fb696
---

When tempted to "remove Make stamp hacks" in this repo, split the cases first —
do not remove wholesale.

- **KEEP** stamps that guard a recipe emitting many files with data-dependent
  names the Makefile cannot enumerate. The four `armN_flat/.done` rules in
  `experiments/derived/score.mk` extract ~60 files each (`anthropic_run01.json`
  …) — the stamp is the *correct* idiom, mandated by the project build rules.
- **CONVERT** a stamp whose recipe produces ONE known output to a plain-file
  rule on that output. `exp1_cross_eval/.done` was this hack: `score_exp1`
  writes exactly one CSV and mkdirs its own parent, so the stamp + its dedicated
  directory were ceremony (and the dir was an orphan untracked file). Converted
  in ticket 0460 / PR #785.

**Why:** a plain `CSV: inputs` rule loses the failure-atomicity a stamp gives
for free (stamp `touch`es only on success). `score_exp1` appends, so the recipe
`rm -f`s then writes; a mid-write crash would leave a partial CSV with a fresh
mtime that Make treats as current → silent stale artifact.

**How to apply:** pair any stamp→plain conversion with `.DELETE_ON_ERROR:`. It
was set NOWHERE in the build before 0460 — a build-wide latent gap (the cosmetic
question surfaced a real correctness hole). It is per-`make`-invocation global,
so one line in `experiments/paths.mk` (included by score.mk + render.mk) covers
both phases; the root `Makefile`, `acquire.mk`, `report/Makefile`,
`slides/Makefile` are separate invocation roots each needing their own. Ticket
0461 generalizes it across all makefiles + an adherence guard.

Still open (noted in 0460/0461, not yet ticketed): the `$(wildcard run*/*.json)`
prereqs in the armN stamp rules are parse-time fragile — empty list on a fresh
checkout before the JSONs land → stamp never rebuilds when data appears.

See [[project-phase-build-layout]].
