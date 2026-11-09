# Design note — consolidate ticket-execution entry points (ticket 0251)

Imagine-phase analysis, 2026-07-12 nightbeat. Read-only; awaiting author
ratification per the ticket's exit criterion. Decision requested: ratify
Option A or amend.

## What the repo already tells us

1. **Half of Q2 is already done.** Ticket 0220 (closed, PR #304) renamed
   `start-ticket` → `hunt`. The `start-ticket` skill is now a 15-line
   deprecation stub delegating to `hunt`. There is no live interactive
   wrapper left to merge.
2. **`/hunt` is already the canonical core.** Its 13 steps (verify-open, own
   worktree, branch, first test, implement, adherence gate, PR, review loop)
   are the shared contract the ticket describes.
3. **`/raid` wraps it only in prose.** Phase 5 says "Each agent follows
   `/hunt` workflow" — a description, not a `Skill(hunt)` invocation. A
   paraphrase is exactly what drifted between the aedist Wave A and Wave B
   prompts.
4. **The headless case is already solved.** `scripts/beat.py` (~line 1219)
   spawns raids via `claude --print -p "/raid <id>"` — the CLI's skill loader
   supplies the live SKILL.md text, never a copy. This falsifies the premise
   that a new `raid-ticket` skill is needed.
5. **Q4 has a concrete bug.** `hunt` step 3 requires the worktree basename to
   equal `t$ARGUMENTS`, but `Agent(isolation:"worktree")` names worktrees
   `agent-<id>`. If a raid execute agent invoked `Skill(hunt)`, step 3 would
   fail its name check and re-attempt `EnterWorktree`, which hard-refuses
   from inside a worktree session — an error, not silent nesting, but wrong
   either way.
6. **Ticket 0252 owns the broader ownership audit.** 0251's Q4 is one narrow
   instance; keep it scoped and do not absorb 0252.

## Options

- **A — skill-invokes-skill (recommended).** `/hunt` stays the single core;
  every path invokes it mechanically: in-process `Skill(skill:"hunt",
  args:<id>)`, headless `claude -p "/hunt <id>"` as beat.py already does.
  Nothing new is built; two files get tightened. Residual risk: discipline —
  a future prompt could paraphrase again; mitigate by making the instruction
  imperative and greppable.
- **B — standalone contract document.** Rejected: a document is inert; the
  aedist drift happened precisely because the contract lived somewhere a
  hand-typed prompt could diverge from.
- **C — new headless skill.** Rejected: beat.py's pattern already is the
  headless entry point; a new skill would be a third entry point solving a
  solved problem.

## Answers to the ticket's four questions

1. One canonical core, as an invoked skill (`/hunt`), not a document.
2. `start-ticket` already merged (0220); `/hunt` is confirmed as `/raid`'s
   per-ticket unit; net live entry points stay at 2.
3. Headless agents get the contract from the harness (CLI skill loader or
   Skill tool), never from an orchestrator's memory.
4. Fix inside `hunt` step 3: generalize the ownership predicate beyond the
   `t<id>` name, and treat an `EnterWorktree` "already in a worktree"
   rejection as isolation-confirmed rather than an error.

## Migration, sized in PRs

- **PR1**: raid Phase 5 — imperative first-action `Skill(hunt)` instruction.
- **PR2**: hunt step 3 — generalized ownership check + rejection-as-
  confirmation branch; one added sentence pointing ad hoc orchestrators at
  the beat.py headless pattern.
- **PR3 (optional)**: delete the start-ticket stub.

No new skill, no architecture rewrite. Two of the four questions were
answered by prior work (0220) and existing infrastructure (beat.py); the
note's job was to surface that.
