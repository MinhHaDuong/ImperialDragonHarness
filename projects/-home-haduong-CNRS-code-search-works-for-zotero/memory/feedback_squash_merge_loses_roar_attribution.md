---
name: feedback_squash_merge_loses_roar_attribution
description: "Squash-merging silently destroys roar's per-PR telemetry attribution, because its enumerator matches only GitHub merge-commit subjects"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6b5b468b-9d23-4a51-87cb-89cefd65f322
  modified: 2026-09-08T08:29:24.873Z
---

`~/.claude/skills/roar/enumerate-merges.py` matches exactly one shape:

    ^Merge pull request #(\d+) from [^/]+/(.+)$

A squash merge produces an ordinary commit (`ticket(0728): … (#448)`), so it is
**structurally invisible** to the enumerator. Roar then falls through to the
aggregate, whose reason line says "no merge commits in range — squash merge, or
nothing merged" — which reads like a benign degradation and is in fact the loss
ticket 0331 exists to prevent.

Cost, 2026-09-08 (search-works-for-zotero): five PRs merged with
`gh api … -f merge_method=squash` (#445, #447, #448, #455, #456) produced zero
enumerable rows. The two that went through `erg-pr-merge` (#444, #446) produced
proper merge commits. Every other session in that repo merges with merge
commits — #449, #452, #453, #454 — so the squashes were also a departure from
the repo's own convention, taken without reading it.

**Why:** `rules/git.md` already says to read the merge method at merge time,
because repo settings drift. What that rule does not say, and what this adds, is
that the method is not only a history-shape preference: it decides whether the
merge is visible to telemetry at all.

**How to apply:** prefer `erg-pr-merge`, which does the right thing. Merging by
API directly, pass `-f merge_method=merge` unless the repo actually disallows
it (`gh api repos/<slug> --jq '{squash:.allow_squash_merge,merge:.allow_merge_commit}'`).
If a squash was already used, say so in the roar summary rather than letting the
aggregate's reason line pass for normal — see
[[feedback_a_constant_cannot_witness_a_run]] for the same shape, a fallback that
looks like data.
