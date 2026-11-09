# TLC sprint brief, 2026-11-09 (as run)

Provenance: the brief the CNRS MOE session handed to each `team-lead` during the
2026-11-09 tidy sprint on padme (13 repos, 50 PRs merged, 28 tickets closed; report
in the per-repo journals). Copied verbatim below, then the two amendments made
mid-sprint. Reuse it as the starting brief for the next multi-repo TLC sprint.

---

# TLC sprint 2026-11-09 — common brief for team leads

Sprint: 2026-11-09 15:22Z → 19:22Z. MOE: the `CNRS` interface session (pid 1845575) on padme.
You lead ONE repository, named in your launch prompt. Everything below applies to it only.

## Goal

Tidy the repository: (1) dirty files, (2) branches and worktrees, (3) open PRs,
(4) ready tickets in priority order. Up to 8 tasks, orchestrated as you see fit
(sequential or parallel). Hygiene before new work: a merged PR counts more than a
new one; a new PR merged counts more than one left open.

## Authorized by the author (no need to ask)

1. Merge PRs that clear verify-gate: gaze → verify-gate → merge skill, pinned to
   the reviewed head, rebased on the default branch first. Read the merge back.
2. Delete branches whose tip is an ancestor of the default branch, and remove
   worktrees locked by exited pids (`git worktree remove`, then `git worktree
   prune`). Never delete an unmerged branch; list it in the report instead.
3. Preserve uncommitted edits: commit them to a WIP branch (or their own ticket
   branch) and push. Never discard, never `git stash`.
4. Work ready tickets (raid skill, "all open" semantics: skip-labelled tickets
   excluded), open PRs, merge when gated; roar after merges.

## Forbidden

- Any write outside your repository (other repos only via a ticket in their
  `tickets/`). The harness `~/.agents`, `climate-finance-het` and `JETP-observer`
  have live sessions: do not touch them at all.
- Any write to the primary checkout except `scripts/sync-local-main.sh`
  (`~/.agents/scripts/`) and committing the dirty files in authorization 3. All
  other work in worktrees made by plain `git worktree add` under
  `<repo>/.claude/worktrees/`. Never call `EnterWorktree`. Never `rm -rf` a
  worktree. Never `git checkout <ref> -- <path>`; never force-push; never
  `git branch -D`.
- Manuscript prose in a paper or book repo is the author's: do not edit it;
  queue such tickets (`~/.agents/rules/prose/workpackages.md`).
- No external services beyond GitHub for the repo and the model providers.
  External-model seats (codex / openrouter) ≤ 5 USD for this repo in total;
  one ledger line in the report.

## Procedure hints

- Harness root: `IDH_ROOT=/home/haduong/.agents`. Skills: `$IDH_ROOT/skills/`
  (molt, yawn, gaze, verify-gate, merge, hunt, raid, roar). Rules:
  `$IDH_ROOT/rules/` (git.md, workflow.md, guards.md, claude-code.md).
- Start with molt step 0 (active-session guard). If another live session
  holds a locked worktree in this repo, STOP and report it; do nothing else.
- Then `git fetch origin` and read STATE.md / ROADMAP.md / memory/MEMORY.md.
- Ticket priority: the ticket's Priority header (erg), then ripeness, then
  deliverable value per the project's north star (raid § Balance rule).
- Pin `model` on every launch and write the launch line (worker, family,
  effort, risk, reason): executors `sonnet`, bulk mechanical triage `haiku`,
  judgment-heavy review seats `opus`; decorrelated reviewers per
  `$IDH_ROOT/skills/route/references/decorrelation.md`.
- Context rule: at ~75% of 230K tokens, write a handoff note on the branch and
  hand the rest to a fresh agent.
- Time: start no new ticket after 18:00Z. Return your report by 18:20Z even if
  work is parked (say what is parked and where).
- Commit trailer: end every commit message with
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01WrxXK4eR18MbLhuYQq6LDZ`;
  end PR bodies with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
  and that session URL.

## Report (your final message; outcome first)

Line 1: `worker: model=<id> · family=<family>`.
Then a table: PRs merged (number, SHA read back), PRs left open (why),
branches deleted, worktrees removed, dirty files preserved (branch), tickets
worked (id → PR → state), tickets skipped (label / reason).
Then: decisions queued for the author (`decision · default · price`), residual
risks, external-seat ledger line, and the primary checkout's final state
(branch, clean?, in sync with origin?).

---

## Amendments made during the sprint

1. **Network.** "No external services beyond GitHub" was too strict: leads skipped
   deliverable tickets whose job is a read-only API (DOIfetch 0028 on HAL, archiveCIRED
   0023 on OpenAlex). Replace with: read-only HTTP to the services the project already
   targets is allowed; writes to live stores (Zotero) and anything that publishes or
   messages are queued for the author.
2. **Force-push.** Leads asked whether they may force-push after a rebase, and two used
   `--force-with-lease` on their own branch anyway. Say explicitly: bring a branch up to
   date by merging the default branch in, never by rebase.

Also worth stating next time: run roar after merges without being asked; a lead that
ends its turn with "Waiting." stalled on a wake that never fired (poll without
`--wait`, or hand the tail to a fresh agent).
