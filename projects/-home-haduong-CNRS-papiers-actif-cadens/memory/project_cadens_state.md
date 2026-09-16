---
name: cadens project state
description: Corpus expanded to 522 sessions; all tickets closed; blog framing note is next human action as of 2026-04-29
type: project
originSessionId: 2a07b316-fb6a-4ac2-a49f-880d87094541
---
As of 2026-04-29 (housekeeping session). Main at `76c01a2`. **Pivoted from single paper to Hypotheses.org blog series.**

**Corpus expanded:** nightbeat ran overnight and closed ticket 0030 — doudou logs merged. 324 → 522 sessions, M_sync 4.08 → 5.33, unity crossing N=1→2, total agent-hours 190.8 → 515.5 h.

**All tickets closed:**
- 0026 — slash undercount fixed (dedup artifact)
- 0027 — gap classifier closed (patterns absent in corpus)
- 0030 — doudou/padme merge done (PR #43, dedup bug fixed)
- 0032 — framing note done (`blog/framing-note.md`)
- 0033 — editorial calendar done (`blog/calendar.md`, 17 posts)
- 0034 — nightbeat harvester done
- 0036 — framing note v2 Phase D done (PR #35 merged)
- Only 0018 (corpus schema v1) deferred to Phase 2

**Next action:** Human reads and finalises `blog/framing-note.md` before first post is written.

**Infra fix this session:** `deleteBranchOnMerge: true` enabled on all 23 non-archived GitHub repos. Cleanup pattern documented in `harness-rules/git.md`.

**Why:** Blog is the deliverable. Framing note is the editorial compass for all posts. HAL deposit after first post is live.
**Key numbers:** 522 sessions, M_sync = 5.33, ~$11,456, 90-day window (ends 2026-04-21).
