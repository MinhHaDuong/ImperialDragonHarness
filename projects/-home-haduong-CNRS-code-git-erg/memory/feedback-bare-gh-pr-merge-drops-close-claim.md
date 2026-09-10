---
name: feedback-bare-gh-pr-merge-drops-close-claim
description: "A PR's **Ticket:** close claim is executed by erg-pr-merge, not by GitHub — merging with bare `gh pr merge` silently leaves the ticket open"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 66e60b89-dd60-41a4-8f88-17567531b19a
  modified: 2026-09-10T10:03:40.137Z
---

The `**Ticket:** tickets/NNNN-...` line in a PR body does not close anything by
itself. It is honoured by `erg-pr-merge`
(`~/.claude/skills/merge/erg-pr-merge`, driven by the `/merge` skill), which
runs `erg close` on the named ticket. Merging with a bare `gh pr merge`
bypasses that entirely, and the claim is dropped with no output.

**Why:** nothing downstream notices. `erg check` passes either way — an open
ticket is not an error — so the missed close and the clean merge produce
identical evidence. On 2026-09-10 (git-erg PR #334) the fix for ticket 0276
sat on `main` while 0276 stayed in `tickets/` with no `Closed:` header; it took
a `/perch` pass to spot it, and a second PR (#335) to repair.

**How to apply:** use `/merge` (or `erg-pr-merge` directly) for any PR whose
body carries a real close claim. When merging with `gh` for another reason,
verify afterwards that the ticket moved to `tickets/closed/` and gained a
`Closed:` header — do not infer it from a green `erg check`. A PR body carrying
`**Ticket:** none` is unaffected, which is why seven merges the same afternoon
lost nothing.

Related: [[reference-erg-update-fetches-from-the-repos-own-origin]],
[[feedback-sweep-for-cli-callers-must-cover-variable-invocations]].
