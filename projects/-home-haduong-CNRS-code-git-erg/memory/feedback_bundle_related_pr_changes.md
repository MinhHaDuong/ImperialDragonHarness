---
name: feedback_bundle_related_pr_changes
description: "apply a guidance change to its own artifacts in the SAME PR; don't reactively spawn a separate follow-up PR for the same theme"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 80a9388c-9a6a-429f-8b09-8c555e28e3ed
---

When you introduce a guidance/convention, apply it to your own artifacts **in the same
PR** — don't place the artifact wrong and then open a follow-up PR to fix it. Concretely:
the FANG-AUDIT report should have been written to `docs/<dated>.md` (per the artifact-storage
guidance) from the start, in the report PR — making the later relocation PR (#195) unnecessary.
And once a fix was needed, it should have ridden with the guidance PR (#193), not been a third PR.

**Why:** fewer PRs to review/merge, one atomic theme, far less rebase churn against a fast-moving
`main` (during a raid, every extra branch is another thing to rebase past every merge).

**How to apply:** before opening a second/third PR, ask — is this the same theme as an open PR,
or an *application* of a change I'm already making? If so, fold it in. Especially: never commit
an artifact in a way that violates a convention I'm introducing in the same session.
Related: [[feedback_edit_canonical_asset_not_live_copy]].
