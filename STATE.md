# Imperial Dragon Harness — State

Last updated: 2026-09-08T08:52Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-08T08:52Z · as of 24fdac1 -->

**Tickets:** 16 ready · 8 blocked — `erg ready tickets/` for full list
  next: 0207 Agnostic CLI reviewer seat — one config, OpenRo… · 0392 Round 1 fans out the full review panel regardle…
**In flight:** 3 open PRs, oldest #794 1d · CI main: success
**Recent (first-parent):**
  24fdac1 Merge pull request #835 from MinhHaDuong/chore-close-0880
  792b125 Merge pull request #834 from MinhHaDuong/t0877-cause-isolated-2026-09-08
  64ebd38 Merge pull request #833 from MinhHaDuong/t0880-roar-memory-order

## Blockers

(none)

## Next actions
- **Cool-down doctrine in force** (2026-07-14): file a tooling ticket only if the defect blocks a merge, corrupts state, or bites a science project; throughput points at the science repos.
- **External-reviewer trial: the seats now actually run.** 0207 accrues again after the 0873 credential fix; before it, five gates in one night lost both CLI seats to fail-open and nobody noticed. Two caveats measured 2026-09-07: `openrouter-budget` returns garbage (its model's cutoff predates the repo clock, so it flagged today's date as a future date) and `copilot` is quota-limited, and harvest counts a quota notice as a response. Scorecards could not be written from any worktree — `erg log` refuses a foreign branch — so the trial has no entries from these runs.
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects.
- **Lint gate has no holes** (2026-08-26, 0470 + 0590): `.ruff.toml` carries no suppression; reopening one is argued in a ticket, not slipped into config.
- **0873 open, half done**: `~/.claude/.env` now carries `KEYS=openrouter:OPENROUTER_API_KEY_IDH` (narrow form; the seven sibling keysets stay unset), and both CLI reviewer seats authenticated on three gates the same night after five runs of silent fail-open. Still open: 0854's `SessionEnd` hook is wired in tracked `settings.shared.json` only, so scratch cleanup is inert until the live `settings.json` is aligned — an operator act, both files git-ignored by design.
- **A merge verdict recorded in a ticket expires**: 0872 measured `t393` as merging *clean* into `reviewers.sh` and warned the clean exit was the trap. One day later it conflicted — main had moved again. Right about the shape, wrong about the fact. The marker grep and the suite settle it; the recorded verdict does not.
- **0572 filed** (2026-09-06): rule files drift by accumulation; trim `workflow.md`, split Claude Code idiosyncrasies from the core, make the review cadence catch growth.
- **0875 filed 2026-09-07**: `tests/test_bash_tests_are_hermetic.sh` reports "29 of 29 hermetic" while its `_SPAWN_RE` requires a `-c`, so 78 script-path spawns across 16 files are invisible to it. Its all-clear cannot be told from "I could not look" — in the guard written to eliminate that class.
- **0877 cause isolated 2026-09-08** (#831, #834; ticket still open): a hook's `if:` filter hands over the whole compound it could not decompose, so `block-pr-merge` now reads the command itself instead of blocking every Bash call. Two gaze defects seen during the same gates are filed, not fixed — 0878 (gaze does not stop when its subject merges) and 0879 (the gate writes malformed log lines). Branches triaged by 0872 survive on origin as `archive/<branch>` tags; their local copies are cleared.

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
