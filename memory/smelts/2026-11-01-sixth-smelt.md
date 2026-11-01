# Sixth smelt — consolidation after the ruleset review

Date: 2026-11-01. Project: ImperialDragonHarness, selected by invocation in
its repository (`/smelt` run from the harness checkout, no argument).
Prompt: `memory/SMELT.md`, v8-r5 (2026-10-30).
Runtime: Mistral Vibe CLI agent session on padme; model id as served (not
self-reported). Branch: `smelt-2026-11-01`. Base: `9b289f77` (main at run
start). Status: submitted for review; not accepted processing until merged.

Companion: [native-note annex](2026-11-01-sixth-smelt-native-notes.md).

## Coverage and migration

Migration preflight (dry-run) and isolated apply each returned 0 moves and 0
active reference edits (AGENTS.md inventoried): already migrated.

Rebuild, not append: every page was re-derived from its previous page, the
journal episodes it linked, and the 20 journal entries no page linked yet
(2026-10-31 and 2026-11-01, read in full), one department per context. All
older entries are processed by the accepted fifth smelt (PR #2049, merged
52f63b18; ticket 1349 closed 2026-10-31) with unchanged blobs; none changed
since. Encrypted entries: 0 `.age` files under `memory/`; none skipped (the
only `.age` files in the tree are test fixtures under `.claude/worktrees/`).
Unavailable sources: none; the Claude Code native store was readable
(39 notes).

Native notes were read as attributed sources; the text each page used is in
the annex. They were neither edited nor drained.

## Editorial changes (per page)

- **Commission.** New pinned rulings: author workspace (2026-11-01, ticket
  1372, now in `rules/git.md`); cross-family gate removed ("Une bonne barrière
  est une barrière supprimée", PR 2085); one data store under the "our data"
  folder (tracker 1401); ticket store is the inter-project channel (author
  overruled the 1409 dissent; kept 1126). Retired: the 1372 and 1374 open
  questions (both closed by author rulings). New open question: the
  `feedback_dont_idle_on_background` description line vs
  `rules/workflow.md` § Escalation protocol — ticket 1439.
- **Git, worktrees, sessions.** Added the author-workspace ruling and its
  backdoor (`ALLOW_MAIN_COMMIT=1 git -c idh.mainGuard=warn commit`; pre-commit
  also refuses, PRs 2129/2131), the autosave line (PR 2130, padme
  `afterDelay`), the workpackages pen rule; retired the old "main read-only"
  workspace line; added the stash-scope open question — ticket 1437.
- **Raids, review, merging.** Cross-family gate dropped (PR 2085) with the
  confounded +0.28/seat measure; seat parsing unified (PRs 2115, 2118); local
  seat family from the served model's grid row (PR 2093); `subagent` reason
  untrusts a forged headless header (PR 2102); gate-admission ancestor rule
  (1403, PR 2149); close-claim grammar (`**Ticket:**`, PR 2122); after-merge
  red folding under a carrier ticket (1396); script-only seats write no
  attribution record. Retired the "no catch rate measured" hypothesis line and
  the raid-1072 invented-waiver hazard (history).
- **CI and doctors.** run_pool throttle `wait -n "${pids[@]}"` (PR 2105,
  hypothesis not reproduced, 127-race remains); `IDH_SESSION_MODEL` /
  `IDH_SESSION_RUNTIME` deleted by an autouse conftest fixture (PR 2097);
  after-merge red on main opens a ticket (1419); `close-and-clean.sh:67` open
  `consider:` (1381); cadens double pytest run noted (0052).
- **Hosts and services.** Data locations ruling: `DATASETS_DIR` /
  `MIRRORS_DIR` per host via `~/.config/environment.d/50-datasets.conf`;
  transcript archive at `$DATASETS_DIR/ours/agent-sessions` with layout and
  cadens backfill (1391, PR 2086); doudou push drop-in (PR 2120); monitoring
  redesign four steps, 40-85 USD, compression dropped (1382 memo); archive
  timer first run; August hole attribution. Retired the separate cadens store
  and the Nextcloud-trash open question.
- **Runtimes.** Rules reach Codex and Pi via generated `~/.codex/AGENTS.md` /
  `~/.pi/agent/AGENTS.md` plus conditional rules (1424) — supersedes the
  same-morning "load none" measurement; `pi --print` needs `</dev/null`; Pi
  agents projected without a `model:` line (unpinned child takes the
  dispatcher's model; routes.json:100 stale; FOREIGN file on padme); padme LLM
  service configurable, never name the model (PR 2065).
- **Memory system.** 1349 closed (fifth smelt accepted, PR #2049); departments
  fixed; prompt v8-r5; skill case notes mechanism (PR 2114, Pi PR 2150) and
  smelt's curation lane (1431, 1432); brood ran once (1351, PR 2152); journal
  now 770 KB; native-note triage lane (39 notes listed below).
- **Skills, docs, hooks.** workflow.md diet (PR 2137: procedure to
  skills/hunt/references, § Cycle); guards.md rewrite (PR 2142: tickets the
  only inter-project channel); resident budgets 18000 loaded / 15100
  comments-stripped; rules-loading re-probe; case-notes bullet; severity-floor
  open question — ticket 1438.
- **Index.** Fifth smelt line now "accepted 2026-10-31"; sixth smelt line
  added; department one-liners refreshed. 37 lines (cap 40).

## Net change

Measured with `python3 scripts/memory_sizes.py --before main` (capped bytes:
everything except Retired and Sources):

```
ci-and-test-suite.md                         3860 ->   4080  net +220
commission.md                                7823 ->   9441  net +1618
git-worktree-session-guards.md               4088 ->   4081  net -7
host-environment.md                          4092 ->   4090  net -2
memory-v8-governance.md                      4084 ->   4088  net +4
raid-review-and-merge.md                     3937 ->   4035  net +98
runtime-observations.md                      4090 ->   3998  net -92
skills-docs-and-hooks.md                     3519 ->   4060  net +541
total                                      net +2380
```

Growth explained: `commission.md` is over the 4096 cap entirely by pinned
rulings, which are never cut — per SMELT.md this overflow signals rulings
waiting for the author to promote (brood, ticket 1351); four rulings were
added this run. `skills-docs-and-hooks.md` grew by the ruleset-review facts
(workflow diet, guards rewrite, budgets, rules loading). `ci-and-test-suite`
and `raid-review-and-merge` grew by the 10-31/11-01 episodes; both stay under
the cap.

## Coherence and exposed contradictions

All indexed pages were compared against the current `rules/` (git.md,
workflow.md, guards.md rewritten 2026-11-01) as authority sources. Three
contradictions are exposed, each filed as a ticket (question only, no side,
no proposed rule):

- Ticket 1437 — `rules/git.md` stash ban "in a shared checkout" (stack
  repo-global) vs a session's own throwaway worktree. Exposing page:
  git-worktree-session-guards.md.
- Ticket 1438 — severity floor "bites the science" (`rules/workflow.md`) vs
  "misleads a model into a wrong act" (`skills/harness-doctor/SKILL.md`).
  Exposing page: skills-docs-and-hooks.md.
- Ticket 1439 — native note `feedback_dont_idle_on_background` description
  line ("ask Fable before EVERY author decision, even ones that look like the
  author's by right") vs `rules/workflow.md` § Escalation protocol (author's
  calls by right never delegated; they wait). The note's 2026-11-01 body
  update matches the rule; the description line does not. Exposing page:
  commission.md.

Resolved this run (were open questions, now ruled): ticket 1372 (author
workspace, in `rules/git.md`) and ticket 1374 (claim B withdrawn). No
remaining indexed claim contradicts a rule.

## Case-note curation lane

`memory/skills/merge.md` re-selected: all four cases kept, none added or
dropped. Each is dated, sourced to a journal episode, ends in a `Use:` line,
and the four cover the four most decision-relevant merge failure modes
(rebase after sibling merge PR 2150; stale gate records PR 1725; hand close
dropping a ticket PR 1924; push-by-commit-id PRs 2033/2035). File stays at
2433 bytes, under the ~400-word cap. No other skill has a note; the recurring
episodes this run (seat parsing, gate admission) belong to the raids page,
not to a skill note.

## Native-note triage table

Store: `~/.claude/projects/-home-haduong--agents/memory/`, 39 notes, read
2026-11-01 via `scripts/smelt_native_notes.py` (read-only). "unchanged" =
carried by the accepted fifth smelt report with an unchanged blob (ledger) or
unchanged text in its annex. Dispositions are proposals for the author;
smelt wrote no rule, edited no note and deleted none.

| Note | sha | Substance | Proposed disposition |
|---|---|---|---|
| feedback_check_exit_codes_not_pipe_tails | 0ede6fd3 | check each command's own exit code, not pipe tails | unchanged |
| feedback_cired_digital_push_login | 39f542ed | pushes to CIRED go through the author's personal gh login | promote to repo memory — host-environment (credentials) |
| feedback_classifier_blocks_rule_mandated_git | ff64c363 | classifier refused rule-mandated git commands; narrow allow rules now present | delete — in force: git-worktree-session-guards hazard (2026-10-29 allow rules) |
| feedback_delta_format | 4332fcd4 | full table with delta above it | unchanged |
| feedback_doctor_kit_tools | 072a9dc5 | diagnostics delivered as doctor's-kit tools, not waiting tickets | delete — in force: Commission pinned 2026-10-28 |
| feedback_dont_idle_on_background | f7579ac3 | don't idle on background; ask-up-first; night-mode Fable | delete — pinned parts in force in Commission; description line contradicts rules/workflow.md, ticket 1439 |
| feedback_dragon_skill_names | c0ad9add | dragon-themed lifecycle names; rename only when misleading | unchanged |
| feedback_gate_record_staleness | bbbbf60b | gate record bound to the exact candidate; record, retry once | delete — in force: raid-review-and-merge; names deleted helpers |
| feedback_gh_admin_delegated | 39bb1e43 | superseded by 1196 option 1 (narrow PAT) | delete — in force: Commission / host-environment credentials |
| feedback_grep_every_site_before_delegating_contract_change | 2619db36 | grep every restatement of a contract before delegating | unchanged |
| feedback_nested_gaze_records_nothing | 68971793 | nested gaze records on notes; gate/merge diffs need an other-family seat | promote to repo memory — raid-review-and-merge (seats) |
| feedback_no_blocking_waits | 300c7eb2 | no blocking waits; one background command with hard timeout | delete — in force: Commission pinned + rules/coding-bash.md |
| feedback_no_second_order_guards | e7854f52 | guard management is test-doctor work only | unchanged (fifth annex) — also pinned in Commission |
| feedback_no_wait_tickets | ab878605 | no wait tickets; doctors use journal revisits | unchanged (fifth annex) — pinned in Commission; 1374 closed |
| feedback_peer_relayed_rulings | c482cff7 | apply peer-relayed reversible rulings, log the source | delete — in force: Commission pinned 2026-10-29 |
| feedback_pi_is_first_class | 715e4c29 | design for Claude Code, Codex and Pi together | delete — in force: Commission pinned + runtime-observations |
| feedback_prose_edits_are_on_main | 2233661e | author edits in the primary checkout; backdoor command | delete — in force: rules/git.md (PR 2129, ticket 1372 closed); note updated to match |
| feedback_regex_filtering_rarely_works | 917d2e56 | regex secret/content filtering rarely works; don't propose rounds | promote to rules — rules/guards.md (credential display section) |
| feedback_reload_helpers_in_long_sessions | fd2ed878 | reload a helper's --help in long sessions | unchanged |
| feedback_review_trust_verify_monitor | e01decaa | Trust, Verify, Monitor doctrine | unchanged |
| feedback_rules_are_law_memory_is_decree | 9d99483d | rules=law, memory=jurisprudence taxonomy | unchanged |
| feedback_sync_local_main_after_merge | 0971f649 | sync local main after every merge | unchanged |
| feedback_ticketwork_automerge | 02327943 | ticket-only PRs merge right away | unchanged |
| feedback_vscode_sessions_share_worktree | 18f364c2 | one VS Code window's sessions share a worktree | unchanged (fifth annex) — in force: git page hazard |
| project_agent_pat_rotation | fedb8273 | agent PAT expires ~2027-10-27; rotation steps | delete — in force: host-environment credentials |
| project_attribution_friction | 49759a14 | attribution capture "still not smooth" | unchanged |
| project_cired_history_purge_pending | 2981a5c8 | CIRED history purge waits on a CIRED admin | delete — cross-project; belongs in CIRED's ticket store (guards.md channel) |
| project_faster_gaze_orchestrator | ab86232f | try a faster gaze orchestrator from arena data | unchanged |
| project_government_memo_cooldown | 0b47108e | government memo in cooldown | unchanged (fifth annex) — pinned in Commission; ticket 1369 open |
| project_idh_tracked_tmp_leak | 0d06be9f | idh-tracked-* left in TMPDIR on killed runs | delete — in force: ci-and-test-suite hazards |
| project_main_guard_enforce | db0ee9ac | main guard enforcing; watch journal until 2026-11-03 | unchanged (fifth annex) — in force: git page hazard |
| project_pulse_gaze_visit_agenda | f4b0d029 | next /test-doctor visit agenda (gaze slow) | unchanged |
| project_verify_gate_double_test_run | b7749cb7 | verify-gate ran pytest twice on a project with no check set (cadens PR 63) | promote to repo memory — ci-and-test-suite open questions (cadens 0052) |
| reference_doudou_nextcloud_sync | dcf23ba9 | sync is doudou's concern | delete — in force: host-environment |
| reference_padme_cores | 9706b157 | padme 3975WX, 32 cores / 64 threads | delete — in force: host-environment |
| reference_padme_home_snapshots | d5b5a84b | btrfs/snapper state 2026-10-30 | delete — in force: host-environment disk bullet |
| reference_padme_llm_service | f303e369 | padme LLM service configurable; never name the model | delete — in force: runtime-observations (PR 2065); "family Local" sentence stale (PR 2093) |
| reference_padme_tmp_sweep | 41ebf979 | tmp-sweep.timer 6 h, >24 h idle | delete — in force: host-environment |
| reference_pi_print_stdin | 9a14edea | pi --print hangs on open stdin; use </dev/null | delete — in force: runtime-observations |

## Second pass over the same revision set

Nothing imported as new. Retired-line counts per page vs the previous page:
ci 6→6, commission 2→4, git 8→9, host 3→5, memory 9→11, raids 9→10, runtime
5→6, skills 6→7 — every caveat, condition or exception of the previous pages
is still present or has a Retired line naming the change that retired it. Spot
checks of corrections against evidence: 1372 ruling read in
`rules/git.md` § Branch and commit (PR 2129 wording, `ALLOW_MAIN_COMMIT=1`
backdoor present); 1349 closure read in `tickets/closed/` and the 2026-10-31
journal entry; rules-loading claims read in `rules/README.md` § Loading per
runtime (re-probe 2026-11-01); severity-floor wording verified in
`rules/workflow.md` and `skills/harness-doctor/SKILL.md`; journal size
re-measured (`du -sb` = 769 712 B). The 1439 nuance (note body updated to
match the rule, description line not) was caught and recorded in the ticket.

## Validation

`python3 -m pytest tests/test_memory_sizes.py tests/test_smelt_migrate.py
tests/test_smelt_native_notes.py tests/test_skill_case_notes.py
tests/test_memory_v8_smoke.py tests/test_on_start_memory_injection.py -q`:
78 passed. `erg validate` on tickets 1437-1439: PASS. Index line count:
`wc -l memory/MEMORY.md` = 37 (cap 40). Page caps: `memory_sizes.py --before
main` — all pages OK except commission.md, over by pinned rulings only
(reported above, per SMELT.md).

## Examined input revisions

Journal entries read in full this run (blobs at main):

- memory/journal/2026/2026-10-31-1349-closed-heading-renamed.md blob 9fafc19908ad5fdf81390521a4eb5422a628ea3e
- memory/journal/2026/2026-10-31-agent-sessions-store-1391.md blob 282c562473423423a4c3b204fdffd5ebbec863da
- memory/journal/2026/2026-10-31-cross-family-gate-dropped.md blob 462fbd998f6631ad41b40edb2cfdb8b9929c4aa0
- memory/journal/2026/2026-10-31-monitoring-and-data-locations.md blob f24ac5f510a38a5490859836fd904935505133a7
- memory/journal/2026/2026-10-31-raid-3d5ae7-skill-case-notes.md blob c1d34d59383aab99c7530305105df6d86a3e7306
- memory/journal/2026/2026-10-31-raid-8ad75a-monitoring-redesign.md blob e27b2a77d8aeba573f90ba6f92190c7eded50f62
- memory/journal/2026/2026-10-31-raid-dd72df-t1402.md blob 61ff26fad50a0bf753c98f854ba31617355852ed
- memory/journal/2026/2026-10-31-raid-f3ac96-seat-identity.md blob af976cf2222d243ec17a757934bf7a380be4d588
- memory/journal/2026/2026-10-31-skill-case-notes-design.md blob b777c23c3e2ab22b8b52c28d32f403c986715cf7
- memory/journal/2026/2026-10-31-t1381-result-names-checks.md blob 436d53ba320f2412d8783c052c9adbe33eae9633
- memory/journal/2026/2026-10-31-t1396-run-pool-throttle.md blob 1076193398712de8ab9c27e6753622c54aed30ca
- memory/journal/2026/2026-10-31-t1396-seat-forgery-regression.md blob ed59ceefd4016b73adc32b65e242b5c3c8a3aa7f
- memory/journal/2026/2026-10-31-t1396-session-identity-leak.md blob be54cecc71cf19df04124ce4565d7ff30496bb94
- memory/journal/2026/2026-11-01-author-workspace-rule-1372.md blob 368c727527c49e0453d76bc6852306edac16b551
- memory/journal/2026/2026-11-01-raid-1f0534-late-merges.md blob 281c46fe785b5e73da5b1a73d1a2d89d27f6a85b
- memory/journal/2026/2026-11-01-raid-1f0534-wave3-pi-agents.md blob c0f0ef8d1cf67af98e2cf8fa9058649129e0548d
- memory/journal/2026/2026-11-01-raid-1f0534-wrapup.md blob eb0aa75da1e671f2bd658ef1c113ab164558b9a2
- memory/journal/2026/2026-11-01-raid-bdf7dd-2fb774-seat-parsing.md blob 1467ed089e6dc11cf8714742b2777a808cef9a05
- memory/journal/2026/2026-11-01-ruleset-review-and-diet.md blob d323fa835316102c6969967371435055018b61f5
- memory/journal/2026/2026-11-01-t1409-cross-repo-handoff-dissent.md blob a4ce4cb1c926d109a8ffeb980ac20cdcba063cb7

Previous pages (blobs at main): topics ci-and-test-suite d1d451d4, commission
f54ecd9e, git-worktree-session-guards 2266a9c4, host-environment 7547b7b0,
memory-v8-governance 15f55d22, raid-review-and-merge acf7c1e2,
runtime-observations 393a550d, skills-docs-and-hooks bffc4821; MEMORY.md
63d07fda; SMELT.md a7c4339199e823e73254b0f70008c3f49f11e866;
skills/merge.md cd1b6442f9e4262d2428bc32dde56da12a3ca352.

Rules and files read as authority or evidence: rules/git.md 4715338b,
rules/workflow.md e41e4522, rules/guards.md 31a29259, rules/README.md
a355126e, rules/state.md d0c940a9, skills/harness-doctor/SKILL.md fed52ae8;
tickets/ (open 1369, 1415, 1417, 1432; closed 1372-1374, 1349, 1351, 1381,
1391-1394, 1401-1426 as cited); conception/2026-10-31-monitoring-redesign.md,
conception/2026-10-31-skill-case-notes.md,
conception/research/2026-10-31-cross-family-seat-measure.md (cited by its
journal entry).

Native notes used (untracked, blob ids as read 2026-11-01; text in the
annex): feedback_dont_idle_on_background f7579ac3e31ce3e49fbf72aa30b3e78739fc805a,
feedback_prose_edits_are_on_main 2233661e74a6f7bb3608b01ad8cad057a2f6d607,
reference_padme_llm_service f303e36989b6d28ebd7ecdce41d97941cab53943,
reference_pi_print_stdin 9a14edeaa8daa764b2a9f356abe095de8b449433.

New tickets filed this run: tickets/1437-stash-ban-scope-own-worktree.erg,
tickets/1438-severity-floor-wording.erg,
tickets/1439-night-mode-escalation-target.erg.
