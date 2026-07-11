---
name: slash invocation data undercount
description: Slash invocation corpus reports only 28 rows but is a known undercount — user made substantially more. §4.5 and Fig 6 are disabled pending ticket 0026 fix.
type: project
originSessionId: caf5fc44-2576-40d1-ae30-62303fa6a0b3
---
`data/metrics/slash_invocations.csv` (as of 2026-04-23 window): 28 invocations, 4 distinct names (orchestrator, celebrate, review-pr, review-pr-prose), all `user-skill` category, all in April 2026. Zero built-in commands detected.

**Known bug (2026-04-23):** The user confirmed they made substantially more than 28 slash invocations. The harvester or classifier is undercounting. Ticket 0026 is open to find and fix the source. §4.5 (Tool mastery) and Fig 6 are commented out in `paper/main.tex` until fixed.

**Why:** Data is from `last-prompt` JSONL records. The undercount is likely due to missing log sources, surface coverage gaps, or classifier errors.

**How to apply:** Do not use the 28-invocation count as a reliable figure in any prose or analysis. When §4.5 is re-enabled (post ticket-0026), verify all Slash* macros reflect corrected data before committing.
