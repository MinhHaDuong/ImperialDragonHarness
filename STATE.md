# Imperial Dragon Harness — State

Last updated: 2026-09-09T17:45Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-09T16:43Z · as of 3e88928 -->

**Tickets:** 16 ready · 8 blocked — `erg ready tickets/` for full list
  next: 0207 Agnostic CLI reviewer seat — one config, OpenRo… · 0392 Round 1 fans out the full review panel regardle…
**In flight:** 4 open PRs, oldest #794 3d · CI main: in progress
**Recent (first-parent):**
  3e88928 Merge pull request #845 from MinhHaDuong/memory-census-2026-09-09
  b8086b9 Merge pull request #844 from MinhHaDuong/t0884-census-handoff
  c20afb4 Merge pull request #842 from MinhHaDuong/t0883-simplify-settings

## Blockers

(none)

## Next actions
- **Slimming pass done, portage next** (2026-09-09, tickets 0881-0884, ~11 600 lines removed). A usage census over 3,42 GB of local session traces — all repositories — drove four merged cuts: eleven never-invoked skills reduced to seven, the nightbeat block removed entire (its scheduler had been uninstalled for months), 31 dead permission rules dropped. **`HANDOFF-2026-09-09.md` carries the full state**: numbers behind each decision, three arbitrations that remain the author's, five identified-but-unstarted threads. `scripts/census/` holds the instruments; re-running them a month out is how the cut gets verified.
- **Rules-tree residency: mechanism isolated, first cut landed** (2026-09-09, 0572). The runtime loads `~/.claude/rules/**.md` itself — a `paths:` frontmatter makes a body conditional, its absence makes it resident in every session of every project. Not a hook, not `CLAUDE.md`: `state.md` was the one body absent from the prompt and the one file carrying `paths:`. **The pointer-table design was never in force**, so the index described in full what the runtime already shipped in full. Scoping the eight path-expressible bodies took the resident set 28 400 → 21 600 tokens; `tests/test_rules_resident_budget.py` now caps it. Left, in order: trim `workflow.md` (7 918) + `git.md` (6 053), then move the seven situation-scoped bodies (~6 500) out of the auto-loaded directory. **What an adapter must inject is exactly the resident set.**
- **Cool-down doctrine in force** (2026-07-14): file a tooling ticket only if the defect blocks a merge, corrupts state, or bites a science project; throughput points at the science repos.
- **External-reviewer trial: the seats now actually run.** 0207 accrues again after the 0873 credential fix; before it, five gates in one night lost both CLI seats to fail-open and nobody noticed. Two caveats measured 2026-09-07: `openrouter-budget` returns garbage (its model's cutoff predates the repo clock, so it flagged today's date as a future date) and `copilot` is quota-limited, and harvest counts a quota notice as a response. Scorecards could not be written from any worktree — `erg log` refuses a foreign branch — so the trial has no entries from these runs.
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects.
- **Lint gate has no holes** (2026-08-26, 0470 + 0590): `.ruff.toml` carries no suppression; reopening one is argued in a ticket, not slipped into config.
- **0873 open, half done**: `~/.claude/.env` now carries `KEYS=openrouter:OPENROUTER_API_KEY_IDH` (narrow form; the seven sibling keysets stay unset), and both CLI reviewer seats authenticated on three gates the same night after five runs of silent fail-open. Still open: 0854's `SessionEnd` hook is wired in tracked `settings.shared.json` only, so scratch cleanup is inert until the live `settings.json` is aligned — an operator act, both files git-ignored by design. **The same alignment is now owed twice over**: 0883 and 0884 cut `settings.shared.json` from 76 rules to 45, and the live file still grants six permissions on scripts the nightbeat removal deleted. **Cause isolated 2026-09-09, and filed**: the split is right, the applier is missing — `check-settings-drift.sh` knows two volatile keys while three of the four keys it reports drifting are CLI-owned, so it can never go green, and a permanently red alarm carries zero bits. 0886 carries the reconciler; 0887 instruments whether the hooks half belongs in a skills-dir plugin instead (three experiments run on Claude Code 2.1.266, `scripts/probe-plugin-hook-loading.sh`).
- **A merge verdict recorded in a ticket expires**: 0872 measured `t393` as merging *clean* into `reviewers.sh` and warned the clean exit was the trap. One day later it conflicted — main had moved again. Right about the shape, wrong about the fact. The marker grep and the suite settle it; the recorded verdict does not.
- **0572 filed** (2026-09-06): rule files drift by accumulation; trim `workflow.md`, split Claude Code idiosyncrasies from the core, make the review cadence catch growth.
- **0875 filed 2026-09-07**: `tests/test_bash_tests_are_hermetic.sh` reports "29 of 29 hermetic" while its `_SPAWN_RE` requires a `-c`, so 78 script-path spawns across 16 files are invisible to it. Its all-clear cannot be told from "I could not look" — in the guard written to eliminate that class.
- **0877 cause isolated 2026-09-08** (#831, #834; ticket still open): a hook's `if:` filter hands over the whole compound it could not decompose, so `block-pr-merge` now reads the command itself instead of blocking every Bash call. Two gaze defects seen during the same gates are filed, not fixed — 0878 (gaze does not stop when its subject merges) and 0879 (the gate writes malformed log lines). Branches triaged by 0872 survive on origin as `archive/<branch>` tags; their local copies are cleared.

## Backlog

- Fold the same-matcher `PreToolUse` hook blocks — needs a fixture first, showing whether a deny short-circuits its block-mates as it does later blocks (0883)
- Merge REALF guidelines and business rules
