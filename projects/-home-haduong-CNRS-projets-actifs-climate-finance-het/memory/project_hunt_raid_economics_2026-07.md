---
name: project-hunt-raid-economics-2026-07
description: "Measured hunt/raid kill economics (2026-07-28) — verification 41%, ceremony 14%; interactive hunts 5.4× a detached executor; IDH tickets 0376-0378 hold the fixes"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7097781f-cc56-4cac-9050-a065d206cf60
  modified: 2026-07-28T09:13:00.570Z
---

Trace analysis of 22 hunt/raid kills (2026-07-21→28), report:
https://claude.ai/code/artifact/daa5be2e-0c1b-4ed1-9dba-3ab2416729b3

- Active kill time splits productive 45% / verification 41% / ceremony 14%.
  Test execution is the top bucket (27.8%, median 18 check runs per code
  kill); strict ceremony (git/PR/worktree/ticket admin) is small.
- Raid superstructure inverts the ratio: review panels 44–56% of subagent
  tokens, execution 20–30%, orchestrator +18–25%. One PR (1172) got 23
  verification agents vs 1 executor.
- Interactive `/hunt` runs inline in the author's session: 404k tokens and a
  68-min post-PR tail per kill, vs 74k and 13 min for a raid-style detached
  executor running the same contract (5.4×).
- Gates bite (TDD red honored 19/22, adherence blockers 21%, gaze REROLL
  29%) — the waste is flat round pricing, not the gates themselves.
- Mixed code+prose tickets are the risk class (2/4 merged; stalls were
  author-arbitration questions, e.g. 0334/0338). Pure prose rarely enters
  hunts (co-edited interactively instead).

**Why:** future raid/hunt planning should route judgment-shaped tickets to
the author and detach clean executions, not scale panels further.

**How to apply:** fixes are IDH tickets 0376 (test-run budget), 0377
(review round-scoping), 0378 (hunt triage pre-step / detach default) — check
their status before re-deriving any of this. Climate_finance already eased
its own merge gate to check-fast+lint (AGENTS.md, 2026-07-28). Analysis
scripts were ephemeral (job tmp); the artifact carries the numbers.
