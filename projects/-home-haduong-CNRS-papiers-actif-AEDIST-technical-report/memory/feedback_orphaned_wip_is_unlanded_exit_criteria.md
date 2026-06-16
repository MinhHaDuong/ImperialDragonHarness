---
name: feedback_orphaned_wip_is_unlanded_exit_criteria
description: "Uncommitted WIP in a stale worktree may be a closed ticket's unlanded exit-criteria deliverable; inspect before discarding and verify it actually runs."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7b53f61c-a20c-44df-a541-3fc6bab72c28
---

When a `/lair` or `/roar` worktree sweep finds **uncommitted** changes in a
stale agent worktree, do not treat them as disposable build noise. They may
be a *closed* ticket's exit-criteria deliverable that never landed:
`erg-pr-merge` autocloses every ticket named in a PR's `**Ticket:**` line
**unconditionally**, regardless of whether the exit-criteria checkboxes are
ticked — so a PR can close a ticket having committed only part of the work.

2026-06-16: ticket 0609's Test section mandated a `\NumRefPlants` adherence
guard. PR #1111 autoclosed 0609 having committed only the data fix
(`macros_slides.tex` 173→177); the finished test sat uncommitted in an agent
worktree for weeks. The data half had *also* already landed via a later
commit, so only the test was novel.

**Why:** the close claim is the `**Ticket:**` line, not the work. Orphaned
WIP is the only trace that a deliverable was specified but dropped.

**How to apply:**
1. On any stale worktree with uncommitted changes, diff it and ask "is this
   a deliverable some closed ticket promised?" before `git worktree remove`.
2. Preserve first (commit `wip(NNNN):` on a branch, push), then adjudicate.
3. **Uncommitted WIP may never have been run** — the 0609 test had a latent
   `NameError` (a `@pytest.mark` decorator using `pytest` before its
   in-function `import pytest`). Always run it and prove RED-on-regression
   before trusting it; hoist in-function `import pytest` to module level
   (ruff's F821 guards this class for *committed* code, never for WIP).
4. Re-enter the work as a fresh ticket (renumber if the branch's old ID
   collided on main — see [[feedback_erg_id_collision]]), then execute.

Related: [[feedback_check_sister_files_first]], the close-then-merge
non-idempotence note in MEMORY.md, and the worktree-paths rule (tool
Read/Write paths must be worktree-rooted; a shared-checkout path silently
operates on main, not the worktree).
