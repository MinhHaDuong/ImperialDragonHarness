---
name: Use full hierarchical group codes for Jussieu cohort
description: When labelling SVCST student groups, always use the full code (SVCST1-2A etc.), never bare A/B
type: feedback
originSessionId: 07f858c6-cb8e-4b42-8ea0-40987d104a0d
---
When working with the Jussieu 2026 student groups, label them with their full hierarchical Moodle code: `SVCST1-2A`, `SVCST1-2B`, `SVCST3-1A`, `SVCST3-1B`. Never use bare `A` / `B`.

**Why:** The hierarchy is `SVCST{year}-{semester}{section}`. The `A`/`B` letter is a section within one parcours/semestre — it's only meaningful inside its parent. `SVCST1-2A` and `SVCST3-1A` are unrelated groups; pooling them is meaningless. Bare `A`/`B` invites that pooling once rows are filtered, sorted, or merged across sheets.

**How to apply:** Any roster, score grid, attendance file, or report that names these groups should carry the full code in every row, even when a single sheet is dedicated to one parcours. Same rule for any future SVCST-style identifier the user shows me — preserve the full hierarchy, don't shorten the leaf.
