---
name: feedback_branch_from_stale_local_main
description: Always verify local main == origin/main before creating a feature branch; stale local commits contaminate the PR
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 96338ef9-a3c4-4926-9dac-2a3c8bcca36f
---

Before `git switch -c <new-branch>`, run `git log origin/main..main --oneline` to confirm local main is in sync. If there are local commits not yet on origin/main, those commits will be included in the new branch and show up as unrelated changes in the PR diff.

**Why:** During the raid-244-243 session, the main repo had 6 Exp3 ticket/protocol commits that hadn't been pushed. `exp2-brerun1-phase-b` branched from this state, including all 6 commits. The initial PR #459 had to be closed and replaced with a cherry-picked clean branch (PR #460).

**How to apply:** Standard pre-branch check: `git fetch origin && git log origin/main..HEAD --oneline`. If non-empty, either push those commits to their own branch first, or start from `origin/main` explicitly: `git switch -c <branch> origin/main`.

**Stronger failure mode — reinventing already-merged work (2026-05-26):** Worked an entire ticket (0346: recover Exp2 mistral/anthropic 4-arm F1 coverage) from a worktree branched off a local main that was ~15 commits behind origin/main. Parallel raid/nightbeat agents had *already* fixed the exact same issues and merged them (mistral raw-fallback, prose-glued-header parser fix, 80/80 rescore, even a 2×2 builder file name). Discovered only when the user said "sync first" before opening the PR. Hours of duplicated, less-complete work (76/80 vs their 80/80). **Before starting substantial work — not just before branching — `git fetch origin` and scan `git log HEAD..origin/main --oneline` + `git diff --name-only origin/main...HEAD` for overlap, especially in an actively-raided area (Exp2 here). The 2×2 table builder survived as the one genuinely-novel piece; everything else was redundant.** Salvage pattern when caught: abandon the redundant branch, cut a fresh branch off origin/main, cherry-pick only the novel file(s), decouple them from any local-only refactor they depended on.
