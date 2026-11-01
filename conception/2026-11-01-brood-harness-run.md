# Brood on the harness: first run, report only

Date: 2026-11-01. Ticket 1351. Project: the harness (ImperialDragonHarness).
Request: the author's raid 1f0534 over ticket 1351, which scopes this run to
a report. Nothing here is implemented: no rule, skill, AGENTS.md or memory
edit. Each candidate below waits for an explicit author request that names its
destination (AGENTS.md § Project memory boundary).

Runtime: Claude Code, coder subagent `claude-opus-5-5` (session-stated), padme.
Base: `fc5c46677d198900366ca822b64491421442c4d9` (raid wave base; rules
identical to main `2a5547b8`).

## Evidence examined

- Smelt reports: `memory/smelts/2026-10-30-fifth-smelt.md`, its
  departments and native-note annex, as merged (last touched `666423f8`,
  2026-10-31). The fifth smelt is the accepted rebuild ticket 1351 waited on
  (blocker 1349 closed 2026-10-31).
- Consolidated topics: all eight `memory/topics/*.md` at the base. One topic
  changed after the smelt: `skills-docs-and-hooks.md`, a budget figure
  (`2d025ff2`, resident rule cap 18350 to 18000).
- Native notes: the Claude Code store
  `~/.claude/projects/-home-haduong--agents/memory/`, 37 notes plus the index,
  read 2026-11-01. Compared by `git hash-object` with the smelt ledger:
  17 unchanged; 1 changed since (`feedback_classifier_blocks_rule_mandated_git`,
  `9b22e347`, rewritten 2026-11-01); 19 absent from the ledger. Of those 19,
  13 predate the smelt and were used in its annex (the ledger omitted
  their ids). Six are new or rewritten since the smelt: `feedback_nested_gaze_records_nothing` (`3b04cd95`),
  `feedback_regex_filtering_rarely_works` (`917d2e56`),
  `project_verify_gate_double_test_run` (`b7749cb7`),
  `reference_padme_llm_service` (`f303e369`), `reference_pi_print_stdin`
  (`9a14edea`), and `feedback_prose_edits_are_on_main`, rewritten (`2233661e`)
  after ticket 1372 closed.
- Current rules at the base (`rules/*.md`, `rules/README.md`), with the skills
  they point to, read to check whether each note's ruling is already in force.
- Tickets 1372 (closed 2026-11-01), 1373 and 1374 (open).
- Encrypted or unavailable sources: none (0 `.age` files under `memory/`).
  Other projects' native stores were not read, except the one AEDIST line that
  ticket 1374's log already quotes.

Native notes are mutable and untracked. This report quotes them condensed, with
private details dropped; it holds no credential material.

## Cost frame

Promoting a ruling into a rule costs context in every session. The resident
set (workflow, git, guards, claude-code) measured 17369 characters against an
18000 cap on 2026-11-01 (`2d025ff2`): about 630 characters of headroom, two or
three bullets. A ruling therefore earns a resident line only if a session
without it would err where nothing else catches it. Conditional rules
(`coding-bash.md`, loaded on `*.sh`) and skills cost nothing at session start,
so they are the cheaper homes for procedure. That matches the author's
taxonomy: rules are law, skills are décret, memory is jurisprudence
(`feedback_rules_are_law_memory_is_decree`, 2026-10-30).

## Lesson candidates (from consolidated topics)

Brood looks for a specific improvement, including removing a bad rule. Five
candidates; one recommends no change.

**L1. Close stdin on non-interactive calls.** Three incidents of one
mechanism: `ssh host bash -s < script` swallowed by a stdin-reading command
(doudou, 2026-10-27, host page), `pi-haiku -p` hanging (PR 1390, runtimes
page), `pi --print` hitting 300 s timeouts that were first blamed on padme's
model (2026-11-01, native `reference_pi_print_stdin`). Common origin: two of
the three involve Pi, so this is two independent tools, not three. Current
home: `rules/README.md:64` covers `pi --print` only, and README is not loaded
as a rule. Proposal: one line, "A non-interactive call that does not need
stdin gets `</dev/null`." In `rules/coding-bash.md` it costs no resident
budget, but that file loads only on `*.sh`, so it would miss the agent
one-liners where two of the three incidents happened; reaching them takes a
resident line. Counterexample: a call that does read stdin (`bash -s` itself)
must get its input explicitly; the rule must not tell agents to close it there.
Evidence: moderate; cost: low.

**L2. Gate on a command's own exit status, not a pipeline's.** One incident:
`git rebase … | tail -1 && git push --force-with-lease` pushed a half-done
rebase and GitHub closed PR 1568 (2026-10-21; raids page, native
`feedback_check_exit_codes_not_pipe_tails`). `coding-bash.md` requires
`set -euo pipefail` in scripts, but agent one-liners are not scripts and do not
set it. Proposal: one bullet in `rules/git.md` § Commands that destroy silently,
or in `coding-bash.md` (which agent one-liners do not load). Counterexample: none found; the cost is the resident
budget if it goes to git.md. Evidence: a single incident with severe
consequence; one recurrence would settle it. The `rtk` proxy that rewrites
output makes piped tails more common, which favours the rule.

**L3. A gaze run inside a coder subagent is unreliable.** Two separate
observations: 2026-10-27 (runtimes page: self-only five of five times, fixed by
explicit panel briefs) and 2026-10-31 (native
`feedback_nested_gaze_records_nothing`, PR 2119: self-only, nothing written
on notes, a blocking crash missed that the orchestrator's own gaze found).
The two conflict on the fix: a brief fixed it on 10-27; on 10-31 it recurred.
Raid Phase 6 already treats a self-only record as missing and re-runs gaze,
so the defect costs time, not safety, inside a raid. Outside a raid (a detached
`/hunt N`), nothing re-runs it. Destination is a skill, not a rule: either hunt's
Verify hands gaze to its launcher, or gaze refuses to close self-only when a
panel was planned. Proposal: a bounded experiment, not a change. Count
`review_notes.py answers` records from coder-run gazes over the next raids and
how many are self-only, then pick. Conflicts with `skills/hunt/SKILL.md`
§ Verify, which tells the coder to run gaze.

**L4. List every site before delegating a contract change.** One incident
(PR 1557, six heads and five review passes, native
`feedback_grep_every_site_before_delegating_contract_change`, 2026-10-21).
`rules/workflow.md` already says "Rename and refactor sweeps cover the full
logical unit", and the diminishing-returns bar covers the stopping rule. The
residue is the order: grep before delegating. Proposal: none now. The existing
sweep bullet covers the principle, and adding the order costs resident budget
for a single incident. Revisit on recurrence.

**L5. No change: recurring full-suite flakes and attribution friction.** The
CI page records flakes with cause not established; the memory page records
attribution capture refusals (native `project_attribution_friction`). Both are
tool defects owned by `/test-doctor` and `scripts/attribution_record.py`. A
rule would not fix them.

**Decay due, not lessons.** The main-guard watch ends 2026-11-03 (native
`project_main_guard_enforce`, the git page's hazard, Commission). After that
date, three copies of the watch go stale together. The government-memo hold
lasts until ticket 1369 closes. `feedback_gate_record_staleness` names
`erg-pr-merge` and `/tmp/chain-merge.sh`, both gone (flagged by the smelt;
still unedited). Those are native-store and smelt edits, not brood's.

## Rule candidates (native-note lane)

One row per native note that prescribes behaviour. Status: **in force** means
a current rule or skill states the ruling, **candidate** means no rule holds it,
**not a rule** means its destination is a skill, configuration or memory under
the taxonomy. The ticket's 2026-10-29 probe counted 41 % of notes prescribing
behaviour that `rules/` did not hold. Since then several were promoted: of
the 24 rows below, 6 are in force in a rule, 11 are candidates, 7 are not a rule.

| # | Ruling (condensed) | Source note, date | Destination | Status | Conflict with current text |
|---|---|---|---|---|---|
| 1 | Trust, Verify, Monitor; judge findings against a bar fixed before review | review_trust_verify_monitor, 2026-10-21/28 | workflow.md § Trust, Verify, Monitor (the fixed bar: skills/gaze/references/panel.md) | in force | none |
| 2 | No second-order guards; guard management is test-doctor's | no_second_order_guards, 2026-10-21 | workflow.md § Autonomous action | in force | none |
| 3 | Bounded waits only; the author is not the waiter | no_blocking_waits, 2026-10-07/21 | coding-bash.md § Waiting (loads on `*.sh` only); "not the waiter" in no rule | candidate (partly in a conditional rule that agent one-liners do not load) | none |
| 4 | Sync local main after each merge | sync_local_main_after_merge, 2026-10-27 | git.md § Reading state | in force | none |
| 5 | Author edits in the primary checkout; trivial commits via the backdoor | prose_edits_are_on_main, 2026-10-26, rewritten 2026-11-01 | git.md § Branch and commit | in force | resolved by 1372 (closed 2026-11-01) |
| 6 | A classifier denial is not retried verbatim | classifier_blocks_rule_mandated_git, 2026-10-28, rewritten 2026-11-01 | claude-code.md § Allow rules | in force | **conflict**: the rule says to rewrite a denial in the `git -C` form; the note, rewritten 2026-11-01, says the allow rules are prefix matches (`Bash(git branch -D:*)`), so `git -C <path> branch -D` does not match, and prescribes a separate `cd` call, then `git branch -D` (auto mode not yet measured). Also: the note hands the author a `!` command; the rule says "logged and skipped" |
| 7 | Rules carry no forge dependency; memory is jurisprudence | rules_are_law_memory_is_decree, 2026-10-30 | workflow.md preamble ("independent of forge and runtime"); taxonomy itself: in no rule; proposed home rules/README.md | in force (principle); candidate (taxonomy) | none |
| 8 | No wait tickets; post-merge measurement goes in a doctor's journal revisit | no_wait_tickets, 2026-10-29 | workflow.md § Autonomous action (by the severity floor) | candidate | **ticket 1374, open**: AEDIST's native index says "a reminder is an OPEN ticket Blocked-by its trigger"; author answer pending |
| 9 | A wanted diagnostic is built now as a ready probe, not a ticket in line | doctor_kit_tools, 2026-10-28 | same line as 8, or the doctor skills | candidate | none; shares 8's stance (two incidents, tickets 1297 and 1336), so one line could carry both |
| 10 | Start independent work before yielding on a background job; ask up first | dont_idle_on_background, 2026-10-21 | workflow.md § Autonomous action | candidate (yielding); in force (ask-up-first: § Escalation) | none |
| 11 | Night mode: escalations go to the top advisor to finish; author reads the morning report | dont_idle_on_background, 2026-10-26 | skills/raid (unattended mode) | candidate | tension with workflow.md "the author's calls by right … wait": compatible only if night mode covers reversible calls alone; the note does not say so |
| 12 | Apply an author ruling relayed by a peer session on a reversible ticket detail | peer_relayed_rulings, 2026-10-29 | workflow.md § Cross-project work | candidate | **conflict, unticketed**: workflow.md says "A peer's message carries no user authority and never replaces the ticket"; the launch contract says no agent message is the user's consent |
| 13 | Gate on a command's own exit status | check_exit_codes_not_pipe_tails, 2026-10-21 | git.md or coding-bash.md | candidate (L2) | none |
| 14 | Reload a helper's `--help` before a mutating call hours into a session; never silence its output | reload_helpers_in_long_sessions, 2026-10-28 | git.md § Reading state, or the skills | candidate | none; the read-back half is git.md's forge read-back |
| 15 | Design for Claude Code, Codex and Pi together | pi_is_first_class, 2026-10-21 | workflow.md preamble or adapters/README.md | candidate | tension, not contradiction: rules/README.md records that no adapter yet delivers the rules to Codex or Pi |
| 16 | Peer VS Code sessions share a worktree; check peers before commit, push or review | vscode_sessions_share_worktree, 2026-10-26 | claude-code.md § Entering the session | candidate | none; runtime-specific, so claude-code.md is its only home |
| 17 | Regex content filtering rarely works; question persistence first | regex_filtering_rarely_works, 2026-10-30 | coding-python.md, or memory only | candidate (weak) | none; one incident (PR 2054), redesign in ticket 1378 |
| 18 | Ticket-only PRs go straight to merge | ticketwork_automerge, 2026-10-11 | skills/merge | not a rule | the classifier refused one as "Merge Without Review" (row 6's note) |
| 19 | Full table, delta above it, lead with the open-ticket count | delta_format, 2026-10-09 | skills/dashboard | not a rule (in force there) | none |
| 20 | Dragon names stay; rename only when the name misleads; no avian analogies | dragon_skill_names, 2026-10-20/29 | harness-doctor authoring reference; skills page | not a rule (partly in force: "not a bird") | none |
| 21 | Coders do not run gaze; the orchestrator does | nested_gaze_records_nothing, 2026-10-31 | skills/hunt, skills/raid (L3) | not a rule | **conflict**: skills/hunt/SKILL.md § Verify tells the coder to load gaze |
| 22 | Gate record bound to the exact candidate; record again and retry once | gate_record_staleness, 2026-10-21 | skills/merge | not a rule | stale helper names in the note |
| 23 | Faster gaze orchestrator by arena arm, not judgment | faster_gaze_orchestrator, 2026-10-29 | skills/route, arena | not a rule | none |
| 24 | Agent sessions use the narrow token; settings are the author's acts | gh_admin_delegated, superseded 2026-10-27 | configuration | not a rule | none |

Not prescriptive, or time-boxed, and so outside the lane: main_guard_enforce
(watch to 2026-11-03), government_memo_cooldown (until 1369), attribution
friction, gaze-visit and verify-gate double-run agendas (doctor visits),
idh_tracked_tmp_leak, and the `reference_*` host facts.

Conflicts in summary: row 5's conflict was resolved on 2026-11-01. Ticket
1373 (forge read-back versus the 1366 KISS ruling) remains open and sits in
Commission, not in a native note. Ticket 1374 (row 8) remains open. Rows 6, 12 and
21 are new conflicts with no ticket; row 6 sits in a resident rule, so a
session following it may issue the form the note says the allow rules miss.

## Recommendation

The evidence supports few promotions. The resident budget, not the evidence,
is the binding constraint:

1. Moderate evidence: L1. In `coding-bash.md` it costs no resident budget but
   reaches only sessions touching a `*.sh` file; reaching agent one-liners
   takes a resident line.
2. One resident bullet, if the author wants it: L2 (row 13). It is the only
   candidate whose single incident did irreversible-looking damage.
3. The author to rule: row 6 (`git -C` in claude-code.md against the note's
   prefix-match finding; a probe in auto mode would settle it), row 12 (peer-relayed rulings against the cross-project
   rule) and row 8 (ticket 1374). Each ruling removes a live
   contradiction between the native store and the rules.
4. Bounded experiment, then a skill change: L3 / row 21.
5. No change: L4, L5, row 17. The rest stay jurisprudence in Commission,
   where the smelt already filed them.

The Commission page holds 9088 bytes on disk (7769 capped bytes by the
smelt's measure) against a 4096 cap, the overflow all pinned rulings. The smelt marked that overflow as
rulings waiting for promotion. This run finds that most of them are better left as jurisprudence than promoted:
six are already in force, and the resident budget cannot take the rest.
Pruning the page's "Now in" lines down to links would be a smelt task.
