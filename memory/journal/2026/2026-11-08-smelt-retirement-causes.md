# Smelt retirement record — 2026-11-08

The author requested no Retired section in topic pages. Retired rulings belong
in the append-only journal, grouped by retirement cause. This replaces the
earlier suggestion to retain them on topic pages for one smelt round.

The Commission entries below were already retired before this seventh Smelt;
removing their topic history does not retire any further active pin. Sources
and earlier journal entries remain intact. Integration includes skills and
documentation; it does not mean every retired ruling became a rule.

## Integrated into current rules, skills or documentation

- "Editing prose is on main" versus rules/git.md main-read-only (ticket 1372): resolved by the author's 2026-11-01 ruling — the primary checkout is the author's workspace, now in rules/git.md (PR 2129); the native note `feedback_prose_edits_are_on_main` was updated to match. Ticket 1372 closed.
- 2026-10-02 uncleared material as age ciphertext: rules/guards.md.
- 2026-10-05 Brood adopted (PR #1187): skills/brood/SKILL.md ([source](2026-10-05-brood-adoption-pr1187.md)).
- 2026-10-21 "We are KISSing the review system": rules/workflow.md § Trust, Verify, Monitor ([source](2026-10-27-doctrine-escalation-pr1778.md)).
- 2026-10-28 Diminishing-returns bar: rules/workflow.md; detail in skills/gaze/references/panel.md ([source](2026-10-28-diminishing-returns-bar.md)).
- 2026-10-21 "No second order guards" and 2026-10-09/10-13 "guards on guards; doctrine is to remove": rules/workflow.md ([source](2026-10-09-raid-1072-guard-and-invented-waiver.md), [source](2026-10-13-third-dream-index-duplication-and-merge.md)).
- 2026-10-21 Ask up first: rules/workflow.md § Escalation protocol.
- 2026-10-29 Departments, 4 KB pages, 40-line index, smelt name: the smelt skill; 1349 closed ([source](2026-10-29-memory-redesign-day.md)).
- 2026-10-21 Pi is first-class: adapters/README.md.
- 2026-10-09 "on veut pas que le delta !": skills/dashboard.
- 2026-10-23 transmissions to Claude, Codex and OpenRouter: scripts/on-start-context.sh ([source](2026-10-23-model-transmission-authorization.md)).
- 2026-11-01 the primary checkout is the author's workspace: rules/git.md § Branch and commit ([source](2026-11-01-author-workspace-rule-1372.md)).
- 2026-10-30 "NO EXPLICIT FORGE DEPENDENCY IN RULES"; memory is jurisprudence, not décret d'application: rules/workflow.md (rules independent of forge and runtime); the jurisprudence half lives on in the kept 2026-10-30 "Rules carry principles" pin.
- 2026-10-11 no `/compact` before roar: historical author ruling. Current guards prohibit compaction as a workaround for the context limit; Roar requires durable capture before recommending `/clear`. These are related protections, not a literal transcription of that ruling ([source](2026-10-11-roar-clear-verdict-survey.md)).
- 2026-11-01 "the ticket store is the inter-project channel": rules/guards.md and rules/workflow.md § Cross-project work; the 1126 half stays pinned ([source](2026-11-01-ruleset-review-and-diet.md)).

## Retracted or superseded

- "I trust you to admin my GH, yes" (2026-10-21): superseded by the author's choice of ticket 1196 option 1, 2026-10-27.
- Legacy advice to derive rules from consolidation: retired by the author's 2026-10-01 RETIRE LEGACY direction (memory/feedback_rules_come_from_memory_consolidation.md).
- "No wait tickets" versus "a reminder is an open Blocked-by ticket" (ticket 1374): claim B withdrawn by the author 2026-11-01; ticket closed.
- 2026-10-27 escalation forks reversible options, capped at 5 minutes: superseded; rules/workflow.md § Escalation protocol now sends a reversible call to an advisor model first, before considering alternatives; bounded forks remain available under skills/route/SKILL.md ([source](2026-10-27-doctrine-escalation-pr1778.md)).

## Completed work or dated observations

- 2026-10-27 main guard in enforce, watch until 2026-11-03: the watch ended with 0 refusals in 1246 journal rows (read 2026-11-07); `idh.mainGuard` still enforce. A host fact, not a ruling.
- 2026-10-27 held tickets 1243, 1285, 1164: closed by the author; reasons in their `Closed:` lines ([source](2026-10-27-session-close-held-tickets.md)).
- 2026-10-31 data locations (ticket 1391): 1391 closed, `DATASETS_DIR` consumed by transcript_spool.py; `MIRRORS_DIR` documented as layout, with no current harness-script consumer found. A host fact, not a ruling ([source](2026-10-31-monitoring-and-data-locations.md)).

## Other guidance withdrawn during the seventh Smelt

These are editorial dispositions of consolidated guidance, not additional
author rulings. Original source links remain on their department pages.

### ci-and-test-suite

- The old suite count (3041) is a dated 2026-10-29 state, not a current count; timing conditions remain dated above.
- The duplicate timing scope and malformed duplicate triage link carried no distinct condition and were merged.
- The 1419 red is historical: PR #2164 closed it. Its caller-reported cause was never re-isolated; the general after-merge policy remains above.

### git-worktree-session-guards

- Classifier advice “never retry, hand the author a ! command”: superseded by the narrow-allow fix already recorded in the accepted sixth report and current `rules/claude-code.md` (literal rewrite or log/skip).
- The blanket `.gitignore` example is episode-specific; the general ignored-file deletion caveat remains.
- Main-guard watch through 2026-11-03: ended; author-reviewed Commission records its outcome (1452), not a continuing watch.
- GC's 353 s → 76 s measurement: dated optimization history; expiry, ignored-file and liveness caveats remain above.

### host-environment

- Monitoring “1382 open”, four-step plan and USD 40–85 budget: superseded by completed integration and the author's interactive confirmation in closed 1382; this old plan is no current spend authority.
- First-run archive count and August-hole count: historical monitoring evidence, retained in the 2026-10-31 episodes rather than current host state.

### memory-v8-governance

- Native-store choice and trial-spend approval as open questions: superseded by author decisions on 1350 and 1354; sources are the closed tickets.
- Native “inbox smelt drains”: no drain was built or authorized; current skill lists proposals and edits no native note.
- Per-project prompt `memory/SMELT.md` v8-r5: retired by 1451; generic instructions live in the skill reference. This historical citation stays under the migration contract.
- “No stage promotes rules” as an unqualified pipeline claim: replaced by explicit Smelt nomination / separately authorized Brood discussion (1461); the author still decides.
- 770 KB journal size and 39-note inventory dated 2026-11-01: old measurements; current report measures inventory, without treating bytes as context tokens.
- Removed `skills/dream/` helpers: settled retirement history, source remains below. Brood's first run (1351/PR 2152) is history, not authority for another run.

### raid-review-and-merge

- Self-only refusal as current gating advice: superseded by the author's 2026-11-01 ruling in merge § Gating tiers. Historical catches remain evidence, not an eligibility rule.
- Older gate-less exceptions and override lists: historical, no fresh waiver; Commission scopes each decision to its PR.

### runtime-observations

- The named 2026-10-31 padme default: dated history; the service changes within days and current lineup was not probed here.
- “Codex runs the other-family seat” as an unconditional family claim: family depends on the actual producer and reviewer, not the runtime name.

### skills-docs-and-hooks

- Severity-floor disagreement (1438): resolved by author choice; workflow wording stands and the doctor cites it.
