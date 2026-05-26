---
name: feedback-main-repo-on-foreign-branch
description: "During a raid the main repo checkout may be on another session's feature branch, not main; commits meant for main (ticket closures, new tickets) silently land on the wrong branch — switch a worktree to main instead"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 55f2a08e-44fb-46c6-95ac-466b0b1f2e50
---

When committing to `main` during a raid (ticket closures via `erg close`, opening new `.erg` tickets, STATE housekeeping), do NOT assume `cd /home/haduong/aedist-technical-report && git commit` lands on main. The canonical main checkout is frequently held on a concurrent session's feature branch (e.g. `fix/0351-slide-wrap`) because many locked agent worktrees exist simultaneously. The commit lands on that foreign branch, and the push is rejected (non-fast-forward) because that branch is behind its own remote.

**Why:** Hit during raid 0345 (2026-05-26). `erg close 0345` modified the ticket in the main repo working tree, `git commit` landed it on `fix/0351-slide-wrap`, push rejected. Files written via the Write tool to `/home/haduong/<repo>/tickets/` also land in the main repo working tree — which is on the foreign branch — so they show as untracked there, not on main. See [[feedback_merge_leaves_worktree_on_main]] for the related post-merge variant.

**How to apply:**
- Before committing anything to main, run `git branch --show-current` in the target directory. If it is not `main`, do not commit there.
- Cleanest path: switch your *worktree* to main — `git checkout main && git merge origin/main --ff-only` — then write/copy the ticket files into the worktree's `tickets/` and commit + push from there.
- If `erg close` or a Write already dropped files into the main-repo working tree on the foreign branch, they are untracked. Copy them into the on-main worktree, commit there, then `rm` the stray untracked copies from the main repo so a future rebase of the foreign branch onto main doesn't hit "untracked working tree files would be overwritten."
