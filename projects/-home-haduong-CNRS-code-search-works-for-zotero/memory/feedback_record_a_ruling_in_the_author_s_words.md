---
name: feedback-record-a-ruling-in-the-authors-words
description: "A ruling goes into DECISIONS.md in the words the author chose; a coordinator's clarifying edit, however faithful, reads to the gate as a lane rewriting the record"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a85a8274-6df4-4e26-8e71-f5b87445cd12
  modified: 2026-09-24T00:45:50.135Z
---

On 2026-09-23 the author ruled, by choosing an option, "an empty .tmp-wal
beside its database counts as Zotero housekeeping". I wrote the
`DECISIONS.md` entry and mentioned that the file had been measured beside a
`.bak`. `/verify-gate` read the `.bak` as a condition and REROLLed PR #624; I
corrected the entry's wording myself and posted "WAIVED by the author's
ruling". Round 2 ESCALATEd: a lane editing the decision record to make a
finding go away, with no fresh word from the author on the record. One
question to the author settled it in a minute.

**Why:** the gate cannot tell a faithful clarification from a convenient
reinterpretation, and AGENTS.md makes interpretation a ruling. My context
beside the ruling (where it was measured) became a clause of it.

**How to apply:** write a DECISIONS entry in the author's own chosen words,
with measurement context in a separate sentence marked as context. When a
gate reads a ruling more narrowly than it was given, ask the author and log
the answer verbatim (question and chosen option) on the ticket and the PR
before touching the entry. Related: [[feedback-a-ruling-scope-is-its-reasoning]].
