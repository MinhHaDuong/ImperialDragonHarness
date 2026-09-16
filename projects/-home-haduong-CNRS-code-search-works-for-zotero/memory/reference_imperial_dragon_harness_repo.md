---
name: reference-imperial-dragon-harness-repo
description: "~/.claude is itself a git repo (MinhHaDuong/ImperialDragonHarness) with its own tickets/*.erg store, worktree convention, and CI — file harness/skill-level bugs there, not in the project repo where they were observed"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ec860e90-d36f-4a14-9411-bfed986e87e4
  modified: 2026-09-14T04:10:48.481Z
---

`~/.claude` is not just config — it is a git-managed checkout of
`https://github.com/MinhHaDuong/ImperialDragonHarness`, on branch `main`, with
its own `tickets/*.erg` store (own `erg` binary at `~/.claude/tickets/erg`)
and its own worktree convention: `~/.claude/.claude/worktrees/<name>` (the
doubled `.claude` is correct, not a typo — worktrees live inside the config
dir's own `.claude/worktrees/`, same as any project). Unlike some project
repos (e.g. `search-works-for-zotero`, see
[[project_search_works_has_no_ci]]), this repo runs real CI on every PR:
`agnostic-guard`, `cross-pr-ticket-collision`, `grep-e-guard`,
`pipefail-guard`, `skill-lint`, `status-verb-guard`, `tab-ifs-guard`,
`pytest-guard`, `validate-tickets`. Squash merge is disabled here
(`squashMergeAllowed: false`); use `gh pr merge --merge`.

**Why this matters:** a bug found *in a skill* (e.g. `/gaze`'s worktree
isolation or its review-panel fan-out) is a harness bug, not a project bug —
it belongs in this repo's `tickets/*.erg`, not in whatever project repo the
symptom happened to surface in. `skills/*/SKILL.md` here is the actual
source for skill bodies; grep it directly when diagnosing a skill's behavior
rather than guessing from its resident description.

**How to apply:** when a task surfaces a defect in the harness itself
(a skill, a guard script, a rule file), `git -C ~/.claude` (or
`/usr/bin/git -C ~/.claude` if the rtk-hook/worktree-guard interaction is
misbehaving, see [[feedback_double_backgrounding_and_unverified_watch_claims]])
to inspect it, open a worktree under `~/.claude/.claude/worktrees/`, file the
ticket there with `~/.claude/tickets/erg new`, and PR against
`MinhHaDuong/ImperialDragonHarness` — never bolt a harness-level ticket onto
the project repo whose session happened to find it. The primary checkout at
`~/.claude` is shared across every project's sessions (many worktrees were
already live there from other work), so treat it exactly like any other
shared primary checkout: never edit on `main` directly, always branch.
