---
name: feedback_drain_stalled_green_prs
description: "Recipe for draining open PRs that are green-but-unmerged; gh pr update-branch is unavailable, use the REST endpoint"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6e907bdc-dd14-4bdc-9eba-7216bbdd3ffa
---

PRs pile up "green but unmerged" when auto-merge was never armed **and** the
branch is behind `main` (under the strict 4-check gate, behind-base shows as
`mergeStateStatus=BLOCKED`, not CLEAN). `mergeable=UNKNOWN` usually just means
GitHub hasn't recomputed — running `gh pr view N --json mergeable,mergeStateStatus`
pokes it.

**Why:** 2026-05-29 a sweep found 4 open PRs all with green checks sitting idle —
none had auto-merge armed and they were 18–104 commits behind. CLEAN ones merge
instantly; BLOCKED ones need their branch brought up to `main` first.

**How to apply** — per-PR by recomputed `mergeStateStatus`:
- `CLEAN` → `gh pr merge N --merge` (lands now).
- `BLOCKED` (green but behind base) → update the branch, then arm auto-merge:
  `gh pr update-branch N` **does not exist in this gh build** — use the REST
  endpoint: `gh api -X PUT repos/{owner}/{repo}/pulls/N/update-branch`, then
  `gh pr merge N --merge --auto`.
- `CONFLICTING` → check *which* files conflict before despairing: compare the
  PR's changed paths against `git rev-list --count <merge-base>..origin/main -- <path>`.
  Often only STATE.md churns (housekeeping) while the real code is conflict-free —
  cheap to recover. Resolve STATE.md by taking main's fresher bullets + re-adding
  only the PR's unique note. See [[feedback_ticket_id_collision_check]] — recovered
  PRs sometimes also carry a stale ticket-ID collision needing a renumber.
