---
name: read-the-schema-before-asking-for-state
description: "Before asking upstream for new state (a checkpoint, a ledger, a flag), read the schema — the state may already exist, and then the ask shrinks to a query and a call site, which is the handoff his pattern accepts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9cbf626-ad71-4884-b119-64be0b580c2a
  modified: 2026-09-02T10:21:00.632Z
---

On upstream #48 (2026-09-02, OpenAI 429 kills the embedding pass, resume
re-embeds all) the first draft comment asked for "a vector-missing set, or a
flag on the passage row". The author asked whether the asks were handoff
quality. Reading `sqlite-index.ts` showed `passages.vector` was already a
nullable column and already what upstream counts vectors with, so pending
embedding work was `SELECT id, text FROM passages WHERE vector IS NULL`, fed
to `embedPending` at the end of `build` and `update`, with no schema change.
The revised comment named that query, the call site, the transient/persistent
retry split behind the loop already in `http.ts`, the shape to avoid (a
cursor in the checkpoint blob, with the reason), and a five-step test on his
own `FakeEmbeddingProvider`.

**Why:** the maintainer builds contracts stated as tests and never replies in
the thread, so an ask he cannot implement without a reading pass gets built
in whatever shape he thinks of first. A vague "set or flag" is exactly the
wording that lets a checkpoint cursor through, the shape #24's contract got.
An ask that reduces to state he already has is one he can ship in a day.

**How to apply:** before an upstream ask that names new state, grep the
schema and the existing queries for that state. If it exists, the ask is a
query plus a call site plus a test; say so with file:line. Name the wrong
shape and why it fails, once. Keep the topology and the verb names out; the
invariant sentence is the seed for the design issue later. See
[[repo-prepares-upstream-it-ships-nothing]] and
[[feedback-execute-authorized-outward-actions]].
