# Imperial Dragon Harness — State

Last updated: 2026-09-07T04:27Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-07T04:27Z · as of 222f1ea -->

**Tickets:** 13 ready · 8 blocked — `erg ready tickets/` for full list
  next: 0207 Agnostic CLI reviewer seat — one config, OpenRo… · 0392 Round 1 fans out the full review panel regardle…
**In flight:** 1 open PR, oldest #794 0d · CI main: success
**Recent (first-parent):**
  222f1ea Merge pull request #819 from MinhHaDuong/t0875-spawn-re-script-path
  eb5a70e Merge pull request #820 from MinhHaDuong/chore-memory-2026-09-07
  9ada03d Merge pull request #816 from MinhHaDuong/t0873-align-live-settings

## Blockers

(none)

## Next actions
- **Cool-down doctrine in force** (2026-07-14): file a tooling ticket only if the defect blocks a merge, corrupts state, or bites a science project; throughput points at the science repos.
- **External-reviewer trial: the seats now actually run.** 0207 accrues again after the 0873 credential fix; before it, five gates in one night lost both CLI seats to fail-open and nobody noticed. Two caveats measured 2026-09-07: `openrouter-budget` returns garbage (its model's cutoff predates the repo clock, so it flagged today's date as a future date) and `copilot` is quota-limited, and harvest counts a quota notice as a response. Scorecards could not be written from any worktree — `erg log` refuses a foreign branch — so the trial has no entries from these runs.
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects.
- **Lint gate has no holes** (2026-08-26, 0470 + 0590): `.ruff.toml` carries no suppression; reopening one is argued in a ticket, not slipped into config.
- **0873 open, half done**: `~/.claude/.env` now carries `KEYS=openrouter:OPENROUTER_API_KEY_IDH` (narrow form; the seven sibling keysets stay unset), and both CLI reviewer seats authenticated on three gates the same night after five runs of silent fail-open. Still open: 0854's `SessionEnd` hook is wired in tracked `settings.shared.json` only, so scratch cleanup is inert until the live `settings.json` is aligned — an operator act, both files git-ignored by design.
- **0872 closed 2026-09-07**: three revives merged (#810 0359, #811 0500, #813 0393), `memory-rtk` dropped as superseded, `t0425` deliberately kept. 0359 and 0500 closed on the author's ruling (#817); 0393 stays open holding the 0870 arbitration — whether a seat skipped for an unresolved credential counts as `attempted`, which decides if an all-seats-skipped panel may exit 0. Every triaged branch survives under an `archive/<branch>` tag on origin.
- **A merge verdict recorded in a ticket expires**: 0872 measured `t393` as merging *clean* into `reviewers.sh` and warned the clean exit was the trap. One day later it conflicted — main had moved again. Right about the shape, wrong about the fact. The marker grep and the suite settle it; the recorded verdict does not.
- **0572 filed** (2026-09-06): rule files drift by accumulation; trim `workflow.md`, split Claude Code idiosyncrasies from the core, make the review cadence catch growth.
- **0875 filed 2026-09-07**: `tests/test_bash_tests_are_hermetic.sh` reports "29 of 29 hermetic" while its `_SPAWN_RE` requires a `-c`, so 78 script-path spawns across 16 files are invisible to it. Its all-clear cannot be told from "I could not look" — in the guard written to eliminate that class.
- **Worktree git, settled 2026-09-06** (harness memory, promoted): two guards refuse git in a worktree session, not one. `\git` beats the rtk rewrite and is cheaper than `/usr/bin/git`; neither beats the containment refusal on `-C`, which only a script file reaches. The guard reads command text, not intent, and a refusal takes the whole compound with it.

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
