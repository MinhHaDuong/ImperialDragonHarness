---
name: No typo callouts in artefacts
description: Don't reference the user's typos or fat-finger moments in tickets, commits, PR bodies, or any durable artefact
type: feedback
originSessionId: 866aa5a7-1cad-4ca5-8395-77ff1232844a
---
Do not cite, paraphrase, or hint at the user's typos in tickets, commits,
PR bodies, docs, or memory entries. Even framed as "the user's X question
prompted this," it reads as a jab.

**Why:** During ticket 0070 drafting (2026-04-30), I wrote "the user's
'sladh dream' question prompted this ticket" in the Context section. The
user called it a "fat fingered dyslexic" sneed and rejected the write.

**How to apply:** When a user prompt contains an obvious typo, parse the
intent silently and proceed. Never echo the typo back, never narrate it
as the origin of a follow-up artefact. Provenance like "discussed
2026-04-30" or simply nothing is fine; "the user typed X" is not.
