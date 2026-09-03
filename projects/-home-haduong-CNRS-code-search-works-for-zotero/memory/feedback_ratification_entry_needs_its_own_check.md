---
name: feedback_ratification_entry_needs_its_own_check
description: "A DECISIONS.md entry citing a number as its subject must have that number checked, not just the surrounding claims — review caught mine wrong"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 23ae8345-4e0c-469c-8519-4d269f82e902
  modified: 2026-09-03T13:52:04.346Z
---

PR #287's ledger entry argued for pinning `main` over a release tag, using the
tag-gap size as its own evidence: "moved three commits past the tag." A
correction commit in the same PR fixed that exact number — three to four — in
`UPSTREAM`, `SYNC.md`, the re-read report and the ticket. It did not touch
`DECISIONS.md`, which is the one document asking the author to *ratify* a
sentence containing that number. The reviewer caught it with one API call
(`gh api compare v1.13.0...main` → `ahead_by: 4`).

**Why:** a correction pass sweeps files by *kind* (spec, sync doc, ticket) and a
ledger entry doesn't look like a place a stale number would hide — it reads as
prose about a decision, not as a data point. But when an entry's subject *is* a
number, the entry is itself a claim with that number's error surface, and it is
the one place readers will trust unconditionally, since ratifying is the whole
point of writing it there.

**How to apply:** when a correction fixes a number across several files,
explicitly check whether any `DECISIONS.md` entry states that number as part of
its own argument — not just entries that reference the ticket, entries whose
prose contains the figure. Grep for the old value across the ledger specifically,
even after "correcting it everywhere." See
[[feedback_verify_the_load_bearing_claim]] — the load-bearing claim here was
inside the correction itself, which is the version of this trap that is easiest
to miss because it looks like the fix, not the bug.
