---
name: project_het_submission_branches_protected
description: "climate-finance-het repo blocks deletion of submission/* branches via a server-side push rule — they are permanent records, not stale branches"
metadata: 
  node_type: memory
  type: project
  originSessionId: c40a15a0-a05a-4167-aa8f-6b7351eb49a6
---

The `climate-finance-het` repo (`MinhHaDuong/climate-finance-het`) rejects
`git push origin --delete submission/*` with "Cannot delete submission
branches" — a server-side rule, not just convention. Confirmed 2026-07-07
when the generic merged-branch cleanup loop from `[[git]]` tried to remove
`submission/rdj-data-paper` (merged into main since March 2026) and was
bounced.

**Why:** Submission branches (`submission/oeconomia-varia`,
`submission/rdj-data-paper`, etc.) are permanent historical records of what
was actually sent to a journal/reviewer, mirroring the `papiers/<state>/<track>/`
convention for non-code submission artifacts (architecture.md, ticket 0159).
They are deliberately exempt from the merged-branch GC even after their
content lands on main.

**How to apply:** Skip `submission/*` when running the merge-base-ancestor
branch-cleanup loop on this repo — don't bother attempting the delete, it
will fail (harmlessly) and waste a round-trip. If you need to actually
retire one, that requires an explicit repo-admin action (ruleset edit), not
a routine hygiene pass.
