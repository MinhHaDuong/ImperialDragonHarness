---
name: feedback_unpushed_main_contaminates_worktrees
description: "Unpushed commits on local main become the base for parallel isolation:worktree agents, causing cross-contamination between branches"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ded37554-580f-4a5a-944b-dea72d7dd972
---

Push local main commits before launching parallel execute agents.

**Why:** When local main has unpushed commits, `isolation: "worktree"` agents branch from local HEAD (not origin/main). Two agents launched in parallel share that same base — if Agent A commits and that commit lands in a shared location, Agent B's worktree may pick it up. In the raid on 0180+0181 (2026-05-29), t181 ended up carrying t180's commit because the worktrees were created from a local main that included a still-unpushed 0174-close commit. Both agents picked up the same base, and one then branched from the other rather than from origin.

**How to apply:** Before launching parallel execute agents in a raid, run `git push origin main` to flush any pending ticket-lifecycle or housekeeping commits. The pre-execute `git fetch origin` in Phase 2 (Sync before starting work) is not enough — it fetches but doesn't push.
