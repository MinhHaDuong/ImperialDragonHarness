# Fifth smelt — first rebuild by department

Date: 2026-10-30. Project: ImperialDragonHarness, selected by invocation in
its repository (`/smelt` run from the harness checkout, no argument).
Prompt: `memory/SMELT.md`, v8-r4 (2026-10-29).
Runtime: Claude Code, background session on padme. Orchestrator model
`claude-opus-5-5` (session-stated); effort not exposed. Department passes:
Opus for Commission, git, review and memory (judgment-heavy rewrites);
Sonnet for CI, hosts, runtimes and skills (factual condensation). Served
model ids of the delegates were not observed beyond the launch token.
Branch: `smelt-2026-10-30`. Base: `0cad157b8e42dca534139a80f7a7933c8be04975`,
rebased onto `eb2a0139` before submission.
Status: submitted for review; not accepted processing until merged.
Ticket 1349's exit criterion ("one harness hoard has run as a rebuild and was
accepted by the author") is met only on the author's acceptance.

Companions: [department returns](2026-10-30-fifth-smelt-departments.md)
(per-page sources, editorial changes, full second pass, coherence notes) and
[native-note annex](2026-10-30-fifth-smelt-native-notes.md).

## Coverage and migration

Migration preflight and isolated apply each returned 0 moves and 0 active
reference edits (AGENTS.md inventoried): already migrated.

Rebuild, not append: every page was re-derived from its previous page, the
journal episodes it linked, and the 92 journal entries no page linked
(2026-10-14 to 2026-10-30), one department per context. The 11 previous
topics became the 8 department pages SMELT.md allows (§ Job of a topic):

| Page | Department | Absorbed |
|---|---|---|
| commission.md (new) | Commission | rulings scattered in governance, raids and native notes |
| git-worktree-session-guards.md | Site practice: git, worktrees, sessions | branch-cleanup-incidents, shared-checkout-concurrency |
| raid-review-and-merge.md | Site practice: raids, review, merging | — |
| ci-and-test-suite.md | Site practice: CI, tests, doctors | — |
| host-environment.md | Environment: hosts and services | zotero-library |
| runtime-observations.md | Environment: runtimes and models | subagent-model-effort-levers |
| memory-v8-governance.md | Architecture: the memory system | memory-v8-acceptance-trial |
| skills-docs-and-hooks.md (new) | Architecture: skills, docs, hooks | — |

Filenames of surviving pages were kept: seven journal entries link into
`topics/`. One historical link (to `memory-v8-acceptance-trial.md`) now
resolves only in git history; the journal is append-only and was not edited.

Encrypted entries: 0 `.age` files in the tree; none skipped.

Coverage limit, stated plainly: the department passes read the new entries
in full but did not re-read in full the older episodes the previous pages
linked; they carried those claims from the previous page and checked them
against the current tree, tickets and git where they could. The orchestrator
spot-checked three carried claims against their episodes (1082 codex
usage-limit seat, Zotero 10 local-write floor, PR 1374 `update-ref -d`): all
three match. 19 entries are processed by a prior accepted report with an
unchanged blob; 2 changed only by the mechanical docs/ → conception/ link
rewrite (81500888). The large evidence containers (PR 1374 review evidence,
1090 remeasure directory, 48 KB PR 1390 review evidence) were not re-audited;
the last is attribution telemetry and yields no claim.

Native notes: the Claude Code auto-memory of the harness (32 notes,
`~/.claude/projects/-home-haduong--agents/memory/`) was read as an attributed
source; the text each department used is in the annex, adapted for this
public repository (condensed, private details and any credential material
dropped; a credential-pattern scan of pages and appendices found none). The
notes were neither edited nor drained: draining is ticket 1349's accepted
input design, not yet built. No other runtime's native store exists (Codex
memories off, Pi and Vibe none: ticket 1349 evidence).

Not smelt inputs, reported: loose legacy notes at `memory/` root
(`feedback_rules_come_from_memory_consolidation.md`,
`feedback_subagent_model_effort_levers.md`, `pending-capture-pr1211.md.txt`,
`reference_branch_cleanup_incidents.md`, `reference_git_in_a_worktree_session.md`,
`reference_zotero.md`) were read as sources; they sit outside smelt's write
area and stay. Fifth hoard branch `hoard-2026-10-29` (PR #1975, closed
unmerged) was not consulted.

## Editorial changes

Per-page detail and every retirement are in the department returns. Main
moves:

- **Commission (new).** 33 pinned rulings in four groups (memory and rules;
  review, guards, escalation; work shape; access and authority). Lines quote
  the source where it quotes the author; where the source records only a
  decision (Brood, encryption, departments, 1196 option 1, escalation fork,
  no `/compact`, Pi, faster gaze orchestrator) the line condenses the
  source's own wording — the author should check those against "never
  paraphrases". Rulings a harness file already states carry "Now in <file>".
  Per-PR waivers are one unpinned, PR-scoped line linking the raids page.
- **Raids, review, merging.** 16.6 KB to 3.9 KB: current tiers, landing,
  gate-record staleness, seat evidence, rounds, invocation, close claims.
  Retired: deleted merge-helper mechanics (1178), the 15-file breaker (PR
  1614), 2026-10-03..13 override lists, attribution counts (telemetry),
  TMPDIR-inside-worktree failures (re-run: 14 passed).
- **Git and sessions.** Three pages merged; rtk-rewrite catalogue retired
  (1078); GC, push-by-commit-id (1366, PR 2035) and branch-cleanup facts
  refreshed and checked against the scripts on padme.
- **CI and doctors.** "Ticket 1045 open" corrected (closed); suite economics
  of 2026-10-02..15 retired; gate-speed and doctor kit refreshed.
- **Hosts.** Zotero merged in. padme CPU contradiction (ticket 1349:
  3945WX/12 cores vs 3975WX/32 cores) settled by `lscpu`/`nproc` on padme
  2026-10-30: 3975WX, 32 cores, 64 threads.
- **Runtimes.** Levers merged in; tournament and routing numbers retired to
  the route skill (the page restates no grid).
- **Memory system.** Two pages merged; index-budget claim withdrawn (index no
  longer injected); AGENTS.md:74 append-only question closed (f78334e6 and
  SMELT.md § Bounds).
- **Skills, docs, hooks (new).** Catalog, naming rulings, resident budgets,
  docs placement, propagation duties, instruction sweep, hooks, taxonomy and
  the government-memo cooldown. "STATE at most 20 lines" (2026-10-19 entry)
  corrected to 40 (`rules/state.md`).

Orchestrator amendments after the department passes:

- git page: restored the 1077 accepted residual (restore/checkout aimed at
  another tree is unguarded) that the pass had cut for bytes — a condition,
  which the cap does not bind; corrected "`~/.claude/CLAUDE.md` links
  `AGENTS.md`" (removed by PR 1462, absent on padme) to "the primary checkout
  is the installed harness", with a Retired line; qualified the rtk exclusion
  (verified by `rtk hook check`) with `rules/git.md` governing SHA reads.
- raids page: moved the gaze `--repo` condition from Retired back to
  Hazards; pruned the escalation and wait lines as restatements of
  `rules/workflow.md` and `rules/coding-bash.md` (rulings kept in Commission).
- skills page: retired the 15-file-breaker hazard (contradicted the raids
  page: breaker removed by PR 1614) and the "workflow.md sends worktree naming
  to claude-code.md" hazard (the table is in workflow.md § Session start).
- CI page: reduced restated author rulings to a Commission link.
- memory page: journal size corrected from ~1.1 MB to 723 KB (`du -sb`).
- Commission: pinned the 2026-10-19 ruling "PRs are not waiting points; the
  existing ticket carries the follow-up" (1466 entry, previously unlinked);
  linked the annex.
- runtimes page: added the codex-door effort pin from the 1365 entry that
  landed during the run (rebased); retired the 2026-10-08
  `model: standard|strong` 404 as history.
- Index rebuilt: one line per department with its most-used fact.

Five 2026-10-19 entries linked only from the old index were read by the
orchestrator: the 1466 ruling was pinned; the harness-pull timer removal,
the 1117 helper behaviour (helper since deleted), the 1095 report profiling
and the timeout diagnosis are history and yield no current claim.

## Net change

Measured with `python3 scripts/memory_sizes.py --before 0cad157b` (capped
bytes: everything except Retired and Sources):

```
branch-cleanup-incidents.md                  4879 ->      0  net -4879
ci-and-test-suite.md                         6611 ->   3860  net -2751
commission.md                                   0 ->   7769  net +7769  reason required
git-worktree-session-guards.md               5516 ->   4090  net -1426
host-environment.md                          3514 ->   4092  net +578  reason required
memory-v8-acceptance-trial.md                7806 ->      0  net -7806
memory-v8-governance.md                      7895 ->   4084  net -3811
raid-review-and-merge.md                    16618 ->   3937  net -12681
runtime-observations.md                      7485 ->   4090  net -3395
shared-checkout-concurrency.md               6547 ->      0  net -6547
skills-docs-and-hooks.md                        0 ->   3495  net +3495  reason required
subagent-model-effort-levers.md              2576 ->      0  net -2576
zotero-library.md                            3556 ->      0  net -3556
total                                      net -37586
```

Growth explained: `commission.md` is new and holds 7769 bytes, over the
4096 cap entirely by pinned rulings, which are never cut; per SMELT.md this
overflow signals rulings waiting for the author to promote them (brood,
ticket 1351). `skills-docs-and-hooks.md` is new: the department had no page
and its 16 entries were unlinked. `host-environment.md` grew 578 bytes by
absorbing the Zotero page (3556 bytes removed there). `memory/MEMORY.md`:
37 to 34 lines.

## Coherence and open questions

Exposed, not settled:

- Native note "editing prose is on main" against `rules/git.md` (main
  read-only; sole exception manuscript prose) and `rules/prose/workpackages.md`
  ("The harness repo keeps its no-exceptions gate"). Shown as an open
  question on Commission. The auto-memory index (`feedback_prose_edits_are_on_main`)
  presents it as settled; that store is outside smelt's write area.
- `rules/git.md` requires forge read-back; the author's 1366 KISS ruling
  removed the ls-remote read-back and kept the commit-id push, and the
  author declined to narrow the rule. Commission pins the ruling; the git
  page leaves the conflict open.
- "No wait tickets" against "a reminder is an open Blocked-by ticket" (another
  store, ticket 1349 probe): the latter note was not found in the harness
  store.
- Stale native note: `feedback_gate_record_staleness` names `erg-pr-merge`
  and `/tmp/chain-merge.sh`, both gone; its point (record bound to the exact
  candidate) holds and is on the raids page.

Unresolved questions: whether the forge ruleset still requires seven checks
with no bypass; what shipped of the stop hook (1164 closed); the 2026-10-29
docs-visit items; doudou Nextcloud trash outcome; whether Strata/Flash-Next is
still production on padme; departments stay provisional until 1349 closes.

## Second pass over the same revisions

The second pass imports nothing as new. Each department return holds a
caveat-by-caveat comparison of its previous page(s) with the rebuild: every
caveat, condition or exception is "kept" or "retired: <reason>". Two
silent-drop risks were found and repaired by the orchestrator (1077 residual
on git; gaze `--repo` condition on raids). Corrections re-examined against
their evidence: 1045 closed (tickets/); STATE cap 40 (`rules/state.md`);
padme CPU (`lscpu`); CLAUDE.md symlink absent (`ls`); rtk git exclusion
(`rtk hook check`); journal 723 KB (`du -sb`); breaker removal (PR 1614 per
the raids return); workflow.md naming table (`rules/workflow.md`).

## Validation

See the merge request for the memory test run and the index line count.

## Examined input revisions

Journal entries (examined in this run unless marked), previous pages,
tickets, rules and other files cited by the returns, and native notes with
`git hash-object` ids of the untracked files as read:

- ~/.claude/projects/-home-haduong--agents/memory/feedback_check_exit_codes_not_pipe_tails.md blob 0ede6fd360a087b021791063f6d7f4c0ecf15675 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_classifier_blocks_rule_mandated_git.md blob e4e06adfadd189b8e682239adb9af884a9f90577 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_delta_format.md blob 4332fcd417647d8b36d31b0ae8ba9050e5021ead (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_dont_idle_on_background.md blob 2fdc4fae242d8bcc296313019a87918dc524e4db (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_dragon_skill_names.md blob c0ad9add05ad91258d923172c48dd91a4b5b09fd (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_gate_record_staleness.md blob 55bfe9c51f45d0bd73c6d5e3e703196b26c8b575 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_grep_every_site_before_delegating_contract_change.md blob 2619db36f7aae083256b3f81169acd4ea1f73879 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_no_blocking_waits.md blob ab04cf27b3e9d82cbe73df406cd85869084be11e (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_peer_relayed_rulings.md blob b50854680b97dd1c4db74d65c264a6aed70d3249 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_pi_is_first_class.md blob efd4e85fec78fea9778b900d120f9929d34654b9 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_reload_helpers_in_long_sessions.md blob fd2ed878692ba5405ceb17a6f1326c33c5f7b501 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_review_trust_verify_monitor.md blob e01decaac1d96950cef7482c19383f106649bd3c (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_rules_are_law_memory_is_decree.md blob 9d99483d83e43a842456e044d016c2fcbb09b933 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_sync_local_main_after_merge.md blob 0971f6494ae0aa9de49e6aa2d0ca0c7361f73159 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_ticketwork_automerge.md blob 023279430aacb947831435b56d71f72685f73358 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/project_attribution_friction.md blob 49759a144cbf3181175481a40cf5d574d91a7e5f (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/project_faster_gaze_orchestrator.md blob ab86232fd4b88cc9cf633ac41e9c5471465a82d1 (native, untracked)
- ~/.claude/projects/-home-haduong--agents/memory/project_pulse_gaze_visit_agenda.md blob f4b0d029f9dfe1a201fe271315abd5ba22edd745 (native, untracked)
- conception/2026-10-29-memory-system-audit.md blob 1cb506dabeec8191fd64da29df13fe70790b7657
- conception/2026-10-30-harness-government.md blob e6ef459a6a4b52dc427f62eb2431906e5625d686
- conception/memory-v8/legacy-retirement.md blob 213ea7b526284a167a21c7508c5699d6d2e196aa
- conception/memory-v8/pilot.md blob 1b15748313856b8482384dc7aaf7abf9c32068d9
- memory/evidence/attribution/2026-10-06-review-attribution-pr1211.md blob 4091544d9e840206642c5cb387acbdbba2f0e2a5
- memory/feedback_rules_come_from_memory_consolidation.md blob 46c31b3ade561205cf059b8f070335538f633c3e
- memory/feedback_subagent_model_effort_levers.md blob 4795361b0dbd28d363de79c03b75302e54dd23ac
- memory/journal/2026/2026-10-01-memory-helper-retirement.md blob 425d8b634b8e6ddaa5fd3804b57bb8fbd1e86316
- memory/journal/2026/2026-10-01-memory-v8-design-and-boundaries.md blob 9dc218a9ba723221b0d8702807ea0439cd9ab10c
- memory/journal/2026/2026-10-01-portable-registration-review.md blob f16cb521f03a2478d1b42880ad7fd01bcb461b4b
- memory/journal/2026/2026-10-02-capture-slug-collision-refused.md blob 35cf7c86f72ef7e9346550b49023a43fd8df1a61
- memory/journal/2026/2026-10-02-first-raid-on-pi-pr1153.md blob a6dee28a3934fbcf5c9401f57b0ae9292fd31da0
- memory/journal/2026/2026-10-02-hunt-0875-runner-nondeterministic-guard.md blob 75c10d8661da275cb4843efe243bc6943c175a03 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-02-local-main-double-carried-open-pr-commits.md blob ad0824902995397a05046d56d182376342cf1474
- memory/journal/2026/2026-10-02-memory-v8-0918-background-launch-without-cwd.md blob c8b257f36c2d012b7813d73ec16f46834df2a504
- memory/journal/2026/2026-10-02-memory-v8-0918-claude-surfaced-planted-contradiction.md blob c4ce2dd1b14397d4c67a9c23c45590d67bae8725
- memory/journal/2026/2026-10-02-memory-v8-0918-concurrent-detached-claude-sessions.md blob 50ac0065e823031da33da370da8398fa04450708
- memory/journal/2026/2026-10-02-memory-v8-0918-correction-link-catch-was-pre-merge.md blob 6099adf0388d6d1243838b42975e891f69e82267
- memory/journal/2026/2026-10-02-memory-v8-0918-correction-worktree-guard-misattribution.md blob ceed6f9c2d01eceedd397d1d6bae28c7759ef116
- memory/journal/2026/2026-10-02-memory-v8-0918-detached-flags-consume-positional-prompt.md blob ee456a31ff45b8c0056011d5893c2c61e65b35af
- memory/journal/2026/2026-10-02-memory-v8-0918-instruction-loading-evidence.md blob a9807f46ad95ef17c71e9579ed756fdf9db8858a
- memory/journal/2026/2026-10-02-memory-v8-0918-missing-read-index.md blob a1fc6b7cc05ea65779e37f115839974820c55a6a
- memory/journal/2026/2026-10-02-memory-v8-0918-pi-leg-interrupted-credit-depletion.md blob 441192fefbf58b0882465b290bbc5d7efdf5f43d
- memory/journal/2026/2026-10-02-memory-v8-0918-pi-loaded-agents-not-planted-claude-md.md blob 08292a4e078503362f0181ba66d9acbc3201cfd3
- memory/journal/2026/2026-10-02-memory-v8-0918-pi-native-load-delivered-contradictory-note.md blob 4830912d4a2ab6a5c69a0b330aaba32954ad2505
- memory/journal/2026/2026-10-02-memory-v8-0918-post-merge-link-catch.md blob 4f7d8f29660ddf3254a4aac8d60136e4ff17a297
- memory/journal/2026/2026-10-02-memory-v8-0918-smoke-slug-collision.md blob d14f86e2883e4d0841b7500492950f422c346db3
- memory/journal/2026/2026-10-02-memory-v8-0918-withdrawn-claim-local-gate-cause.md blob 18c902a111f67db5d68388df2753a63386f07ddb
- memory/journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md blob 1616e1d4ddf4c350d125265720a30c4f5dae2bf1
- memory/journal/2026/2026-10-02-memory-v8-pilot-established.md blob 795fa66bf1ba14b89da54485b9e907a248a4396f
- memory/journal/2026/2026-10-02-memory-v8-runtimes-verified.md blob df8ca164c6222dc8eca09146c80e4048a6288db3
- memory/journal/2026/2026-10-02-memory-v8-smoke.md blob 2fed7bb0098b94d1fbcabe7acabf142652c2bc10
- memory/journal/2026/2026-10-02-orchestrated-raid-closes-memory-v8-tracker.md blob c24f92fddeaccf3e35c916ae90144d8c008fe5a7
- memory/journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md blob 8e6e73730033d0ee324afc2820a95353cd54c9a3
- memory/journal/2026/2026-10-02-raid-1015-annotation-collision.md blob 43691ed1e9a9ce8aad6a3a05f7dd70d09a7538bb
- memory/journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md blob 0668fc51ac747be559debd87ba63898f35ce98e7
- memory/journal/2026/2026-10-02-retired-read-index-invoked-in-trial.md blob e3c9a9a973d5631d6505892d2d64f6177b7f0ea9
- memory/journal/2026/2026-10-02-reviewer-attribution-design.md blob d1a855d95eb5a2002e4e4f0e6f7b35bd1e5c653d (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-02-session-suite-economics.md blob 50ddecf42de510976d8baea626180944928abf22
- memory/journal/2026/2026-10-02-skills-dream-read-index-not-found.md blob fab60f7cf0d5d6a26bda301bfc7290846c7ed5c0
- memory/journal/2026/2026-10-02-t0918-trial-read-index-helper-absent.md blob a8274f2fdf5ff537fcec704f4d6a45714232b4bf
- memory/journal/2026/2026-10-02-t0918-trial-smoke-slug-collision.md blob 6cfb027978aa8ccd6aa37d6ae76e82c59a8ad8fb
- memory/journal/2026/2026-10-02-t0918-trial-vibe-native-agents-injection.md blob 3a47c2c4d9e07b0d62f9bb72fc003b36ed5f3056
- memory/journal/2026/2026-10-02-trial-clone-carries-prior-session-entries.md blob 1f6dbd5adb819ba06b3d012903f3ae1dfc595f6b
- memory/journal/2026/2026-10-02-untracked-claude-md-contradicts-memory.md blob 624122d83f505db68b6fc27f659d3e4a07d62aa5
- memory/journal/2026/2026-10-02-worktree-guard-guidance-conflict-step6.md blob 3013d6f5d5f9cb1c67d940801143fb33cc608db2
- memory/journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md blob 56c3b9ac4f9a1a68910e0664e9d04b38a42e5e72
- memory/journal/2026/2026-10-03-raid-0902-gaze-risk-band-pr1155.md blob 725c1b38993c04f5f6484fed5aa43e7cc12ca44d
- memory/journal/2026/2026-10-03-raid-0938-profiles-subsystem.md blob 95662f71d0b78714b0068f679ae3c52e93deb533
- memory/journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md blob 74e50714ffad572eb88a8dd8550ad7f1bcf13b52
- memory/journal/2026/2026-10-03-tracker-closure-pass-0205.md blob ae3bbbf65605bb24e3f21dd9c7853c9b905be908
- memory/journal/2026/2026-10-04-review-subagent-switched-primary-checkout-branch.md blob 866ba4c4283d003d72e280166934eb60fa7c350e
- memory/journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md blob c37ed41a2b669ee06a596c36de1c1e693f2af396
- memory/journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md blob f08e2eb42d5c18c9f6e5b5e7fdc40211785b3900
- memory/journal/2026/2026-10-05-brood-adoption-pr1187.md blob 2a67454884e216858b5da69e3842b06f727806b3
- memory/journal/2026/2026-10-05-raid-1005-1023-verification-recovery.md blob 0e556611bdbd22f69ae3deb61932a73ed361a19e (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-05-raid-926-supersession-and-publication.md blob 8cef1af95b09d08ff1ff64ea515c7e790e1301c4
- memory/journal/2026/2026-10-06-0913-dispatch-close-path.md blob ca19e80ca938b78ee454accb2cfc195cff926857
- memory/journal/2026/2026-10-06-leftover-podman-service.md blob c5c9d7cb2e1d5a3648f7b41f1a649bc44af44c71 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-06-local-ci-act-equivalence.md blob 09da99d430684205e374b6ce86102823730d4fd4
- memory/journal/2026/2026-10-06-model-tournament-cycle-2-close.md blob 6fc88c8a5d0e928634c579d3455cff05c2e5f192 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-06-pr1225-author-review.md blob 315ff7492a9c1284f48e49627ef13791396797e6 (revision changed since prior report; not re-read)
- memory/journal/2026/2026-10-06-raid1004-closure-experience.md blob 3310d26a0298c9108292b1ba074400fbe34c3d32 (revision changed since prior report; not re-read)
- memory/journal/2026/2026-10-06-raid-1042-capture-review-repair.md blob e3049dba9791fd8989d5ebb831e41d85499f29da (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md blob 57cdc357a31fa2215d6d8be5d3cef05a783338b1
- memory/journal/2026/2026-10-07-mistral4-pi-context-correction.md blob 695998ad50d31b6d37da48a350f00dd06f727409
- memory/journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md blob 4955a6ec349d09327a53d298dd51a1573f276f52
- memory/journal/2026/2026-10-08-haiku55-arm-n-integration.md blob f40aa455faf5984da3970e781d7b89a10d558433
- memory/journal/2026/2026-10-08-haiku-review-delay.md blob f1deee1259392caf54d49c186041c5bf97edb028
- memory/journal/2026/2026-10-08-llm-routing-plan-and-wave-a1.md blob 979200c75175a322c4ea99b02f828b8352c163f5 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md blob 63950b7af16ca2629376f92cca283b74e7082fc0
- memory/journal/2026/2026-10-08-tournament-publication-wrapup.md blob 5b7773ce476cfd4f0423cfa6e4d10bc1b38be557
- memory/journal/2026/2026-10-09-1071-launch-line-and-adherence-rerun.md blob 31d85b8918caeaf590196a4f7ae30e4b53af6b60 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-09-close-1074-guard-refusals.md blob 6a920661365ba6c48a5420fa06a52c70ae587108
- memory/journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md blob e878b37f9ab396f624870c285ee614ea501fb439
- memory/journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md blob c0552bee9f4b8cbc60931f2e4e2f56bc538c5c13
- memory/journal/2026/2026-10-09-pr1309-gaze-isolation-blocked.md blob 9d469c527f2657be04f959021ae65249c3435dd0 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-09-pr1328-short-close-claims.md blob 98d99ef8b84eb51705f299a03ecf319cc4baa4e9 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md blob ef6b5341e7e5f7b26e44a7a138973c9c7ab43a51
- memory/journal/2026/2026-10-09-raid-1075-roar-rule-conflict.md blob 04a7af1dd0fdfeca26e8d800cdc9d6eeeeda2727 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md blob e05588d0ac6b00e5ffa3262075d2332b1947a39b
- memory/journal/2026/2026-10-09-routing-review-round-two.md blob 994ac71e36912f608f390c12d8857d5b535462ef
- memory/journal/2026/2026-10-09-rtk-git-exclusion.md blob 60de63e9e17e0521694b89a66cebafc9f515b9fb
- memory/journal/2026/2026-10-09-tournament-report-padme-env-float-drift.md blob 37976471b50ffcc43dbaa6bed2d936137b84e558 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-09-worktree-isolation-census.md blob f38dcd74b9bdd92d0db259283a4a5c1ba94f6e75
- memory/journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md blob cc588a3bd38ed1279cb4b9ee7fd498ac30257fb2
- memory/journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md blob 2f36d32d2f1a05ce70104de210f77e09ce1e196c
- memory/journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md blob d9e91fb90a94751a76c10120b27b6c78353a4e70
- memory/journal/2026/2026-10-10-ticket-line-guard-deleted.md blob aa135ff66b647192eefe855791b4f9eb048fca81 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-11-roar-clear-verdict-survey.md blob 2127eb530aa1b20804c4af5b61215aeb13118148
- memory/journal/2026/2026-10-12-cross-repo-session-gaze-forks.md blob 383a346455a557152f2baeac4ab6538a666b5f65
- memory/journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md blob d4b603552442b47a8b03cacdb96695b26e972bd3
- memory/journal/2026/2026-10-12-pr1368-review-evidence.md blob d4478f34d37e4a0f6cfd1c9fe08dad9a69c3dbc8 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-12-pr1372-review-evidence.md blob 868cca157179460454dbf2d26f29cec126e9f8b9 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-12-pr1373-review-evidence.md blob 240b7d7593346ee27cce5f30ab60e8c93eeaf5be (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md blob 8f6d737204fa53c02dff375d223ab7c9e4eb7f06
- memory/journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md blob b8ec6c3ad79a75185a0f6efa13e8e362a31f9de3
- memory/journal/2026/2026-10-12-t1053-arena-git-and-scoped-vram-wait.md blob cd51156887754a38666a3b4b530e8789987c6e38
- memory/journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md blob 2a56ffa7c22084233e0023ed9f8c577afbe3e653
- memory/journal/2026/2026-10-13-arena-separation-and-force-merge.md blob 80e1bd978f66338d625f0f456dd88171935046e0
- memory/journal/2026/2026-10-13-pr1374-attribution-pending.md blob af344fd9e44b6e5995b1531e65f5c54fa14880fd (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md blob d88ff8407aaa1df3d14577b7d518826624bd1c09
- memory/journal/2026/2026-10-13-pr1374-review-evidence blob 7861d64569f84ffd5b94b5f19042f4b975a959d9
- memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md blob ea14e5a4e2cad2416b8555226dadca3051cad2e6
- memory/journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md blob 7932fb33607fe4c08fee6ea9fe09f09241b407d2
- memory/journal/2026/2026-10-14-1095-design-panel-pr1399.md blob 2111a306715c51e43148daa10b5a285816f9552e
- memory/journal/2026/2026-10-14-1096-split-and-session-cleanup.md blob 82a02f8ac08d5f9532eb7202736ccf4029a505df
- memory/journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md blob 09aa7876869d983585a90fca9451f5a7e3bb654f
- memory/journal/2026/2026-10-14-pr1390-review-evidence.md blob 377bc0b8b30e5ebd8623f9eeb6867e5e67155069
- memory/journal/2026/2026-10-14-raids-1080-1089-wrap-up.md blob adc8aa5514c7cdaf3d5867ebf23e588381586954
- memory/journal/2026/2026-10-14-readback-rule-and-1090-merges.md blob 406120b97894726f0a84be03cdaf67f39e20b795 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-14-review-workflow-followup.md blob c46bc7eb4e04e76990b1e063938fa1483df2c7a6 (processed by a prior accepted report; not re-read)
- memory/journal/2026/2026-10-14-roar-exit-check-1098.md blob eba8dc0c02ffdc5cef27029cdf001a101dce0c37
- memory/journal/2026/2026-10-14-roar-remeasure-1090 blob 55503439820465c188cb24ff0f8827c0bbd1fd34
- memory/journal/2026/2026-10-14-roar-remeasure-1090.md blob c9ba8a2e8dbf9fb7808b5264f8e9d5508c42bf5b
- memory/journal/2026/2026-10-14-zotero-local-api-preference.md blob 9092b0a221bca22dd9e960ece0bcc7a1ce4b9b76
- memory/journal/2026/2026-10-15-fourth-hoard-merge-and-maintenance-fixture.md blob 7e42d25f25c77f844883b0d7e6a5f4ea7e4e34f0
- memory/journal/2026/2026-10-15-hoard-path-migration.md blob b688c611b01c02c846aff1d7d2a3f0a21a837fbb
- memory/journal/2026/2026-10-15-molt-zotero-reconcile-removed.md blob adc7fd1d1eb21b2808301a9c803b5237e8d88c0a
- memory/journal/2026/2026-10-15-morning-healthcheck-merges-ticket-revalidation.md blob 5666c684fd9d5d40d9aff83da23b8662c8cdae24
- memory/journal/2026/2026-10-15-raid-1101-1103-1104-integration-pending-attribution.md blob 72151cd01ec6ff2cdee6ef23dcd4321573466a2f
- memory/journal/2026/2026-10-16-zotero-local-only-decisions.md blob 22f3d672a8c813dfc3b949f884f82faff8a6f25d
- memory/journal/2026/2026-10-16-zotero-pyzotero-and-display-leak.md blob 65bfe6876088cb1423230e64b772f064c3a0a3ee
- memory/journal/2026/2026-10-16-zotero-verbs-exact-match.md blob c28f58aec1676b418dfc9fb2e237f58bb192c4a0
- memory/journal/2026/2026-10-19-1095-temporary-lifecycle-integration.md blob 0da313ca01f8b0035150f5934b6e13b7f7f687ea (examined by the orchestrator)
- memory/journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md blob de5fb000dd07a7ad9cf9a9fbcda236b2938d9d0e
- memory/journal/2026/2026-10-19-doc-refresh-final-merge.md blob 9dc5f23c213770b3a678f45c3190450a83a11eec
- memory/journal/2026/2026-10-19-docs-refresh-and-global-claude-retirement.md blob 9e3fc51865cd830cd789425d1660402c5abddd48 (examined by the orchestrator)
- memory/journal/2026/2026-10-19-merge-inspection-1117.md blob 9bf1c713d23a4a3e8fb13569527e6b29d040da37 (examined by the orchestrator)
- memory/journal/2026/2026-10-19-pr1456-review-and-attribution.md blob b1ca018dc5925215b95ff4b782e8c25ab60b235f
- memory/journal/2026/2026-10-19-smart-testing-1466-wrap-up.md blob 5951e0f59ff369cc1e4e631e7d2591a43d92e4a6 (examined by the orchestrator)
- memory/journal/2026/2026-10-19-tmp-report-timeout-diagnosis.md blob 6fefd42321f8a8f003688029c878afb93c7e926e (examined by the orchestrator)
- memory/journal/2026/2026-10-20-raid-1136-1137-1126-and-1100-split.md blob 7bd5d3e5116e89fff7edc50eb455bbe5205b26ed
- memory/journal/2026/2026-10-20-raid-1150-and-1146-integration.md blob 1d53dfec32b966cff7958fba2d77cd425a6740d2
- memory/journal/2026/2026-10-20-raid-skills-audit-1128-1129-1130.md blob b12f03c0b244a3ded034b8c05c389033e17789b1
- memory/journal/2026/2026-10-21-1153-stack-landed.md blob d0aac8057e2669f4c5d7a69cc47ab560ab44a756
- memory/journal/2026/2026-10-21-await-external-probes.md blob fa046f90f7e49bcab64c21a33ec2d297d1e44b2c
- memory/journal/2026/2026-10-21-gate-on-folds-and-wall-down.md blob 1cb53e84eacaf43f2b1bbb4c602773de4cd7c48d
- memory/journal/2026/2026-10-21-gc-liveness-scan-lazy-pr1583.md blob f5c36126760890bfaf4b3a4c7c52d903d28f62e8
- memory/journal/2026/2026-10-21-instruction-contradiction-sweep-pr1622.md blob 42f78d5a03515db1d936d3f7274cdd90cb0f7b2c
- memory/journal/2026/2026-10-21-pulse-gate-wall-time.md blob 138fc53cacaec4ef32a4bb00ba2a6c347c8020cd
- memory/journal/2026/2026-10-21-pulse-testing-expert-1541.md blob c416700dc2fb6cbb5548fcdd760a5ac2ac6bfc52
- memory/journal/2026/2026-10-21-raid-1170-1173-1175.md blob 81e9802221abaeb3a6941529aa86b4600d6e8f00
- memory/journal/2026/2026-10-21-raid-stack-and-merge-helper.md blob 3ae32b94ae02cb4729b99b77149684ec57e757ff
- memory/journal/2026/2026-10-21-stopguard-end-of-turn-hook-design.md blob cf2eff523e8ed53c8ad6a261d324842da4f1571b
- memory/journal/2026/2026-10-21-velocity-raid-1167-1169.md blob 0e2216e1a23cd92a397cd688c774816f1bcc390d
- memory/journal/2026/2026-10-21-velocity-scan-stale-baseline.md blob a20dcb13ef283eb891212b1408fd5172b647e563
- memory/journal/2026/2026-10-23-branch-sweep-1644.md blob 1c91397eb9cbf9047916e004e673e84e715fd3d4
- memory/journal/2026/2026-10-23-model-transmission-authorization.md blob 10055cf25f051fdc31162aebfa9c240888e7eaf0
- memory/journal/2026/2026-10-23-review-merge-1634-1635.md blob 3af36736ec26bf0e3026a715631b926950029dee
- memory/journal/2026/2026-10-23-worktree-gc-ownerless-locks-1638-1640.md blob d46052a77be480dd5e31221c5c9449f57c96cb79
- memory/journal/2026/2026-10-26-evening-review-ceremony.md blob 3295d0eaabb957a77e1bb471a88de488a3c4f4dc
- memory/journal/2026/2026-10-26-pr1633-merge-on-author-authority.md blob 4293f88bf58e86b45229f87a898c022f777dd2f2
- memory/journal/2026/2026-10-26-raid-1212-1211-1221-1219-1220-1215.md blob 86a2b603b5a7bb23f17c1de720e6d6938b2390ea
- memory/journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md blob 84c2cfb2735ce94c15306952368645e10f2ccdac
- memory/journal/2026/2026-10-27-dangling-prune-moves-to-install-pr1701.md blob 884b9d16f4af4a1ec460f0b2747bfb77b92efb7a
- memory/journal/2026/2026-10-27-docs-to-conception-pr1744.md blob f3b6247904c559ddf945770a6ed3a11af3d2f57d
- memory/journal/2026/2026-10-27-doctrine-escalation-pr1778.md blob ba492609cb1c2ef3055f2a51dcbe9568aa2b240d
- memory/journal/2026/2026-10-27-erg-sync-molt-step-1732.md blob 2bae380bc13a9b5eed8c32af3da670b424f89e39
- memory/journal/2026/2026-10-27-harness-doctor-and-project-coherence.md blob 52d6a9cdbd604df8cb40365221065ef304dd0c54
- memory/journal/2026/2026-10-27-harness-doctor-idh-root-paragraph-1240.md blob 21685248d0534afabfe51d17c48c1fc62b29e7b6
- memory/journal/2026/2026-10-27-hunt-phases-1235-override-merge.md blob cc0a254a24cc177daedb84df103dde9f1915dad4
- memory/journal/2026/2026-10-27-pi-skills-standard-root-pr1690.md blob 17316db3c77722b4578cd669c499e96cd71d3a6c
- memory/journal/2026/2026-10-27-raid-1214-1218-waiting-follies.md blob 0118b8b5ac34c82b5a5104e4527517fa902b2564
- memory/journal/2026/2026-10-27-raid-b-followups.md blob 8fbb7cc28bc24b83dcb0ed53106c800c9abd6495
- memory/journal/2026/2026-10-27-raid-forge-less-and-guard.md blob 2d94dedcdf031f1bdae7fda12f7b2442081fd4b1
- memory/journal/2026/2026-10-27-raid-optimistic-merge-afternoon.md blob 12cc149ee7bdc69099cf06dc47f024e8ff26cba8
- memory/journal/2026/2026-10-27-raid-prep-wave0-and-1206-doudou.md blob efd82f39ea8841fc6a3810fea4e4e29589e4f7be
- memory/journal/2026/2026-10-27-raid-sitrep-ticket-1246.md blob 69da9506d0d25b1aabdf39b6bd25a8d1d03adac7
- memory/journal/2026/2026-10-27-review-cost-raid-and-redesign.md blob 8a8aeb83e89ff670dea51285fd50c11e8f57609f
- memory/journal/2026/2026-10-27-roar-1841-watchlist-closures.md blob 4ce8995dc6684138a3977c2f940bbea98c8e2883
- memory/journal/2026/2026-10-27-session-close-held-tickets.md blob cd7d2aecac69cad7954d4257c74f4c755ca607d3
- memory/journal/2026/2026-10-27-test-doctor-rename-1228.md blob 9762652062f9a5bcb0538bbb42b6ec21bdff1670
- memory/journal/2026/2026-10-27-trace-wall-time-pr1722.md blob 4e7aa1bf7a11cdd5d872635446c08fb40350b3a8
- memory/journal/2026/2026-10-27-vibe-headless-seat-1279.md blob b1c8fb4e1c6650e1861f1e949113a9e5013a12d5
- memory/journal/2026/2026-10-27-yawn-to-rest-pr1782-pr1789.md blob b38c9eac09085cb74ae24dd46786601b3a5d26d3
- memory/journal/2026/2026-10-28-after-merge-red-1322-cleared.md blob ba184091d96cab18ed60c3f062452550786901f1
- memory/journal/2026/2026-10-28-catalog-reverse-import-pr1861.md blob 7bf1469904ebfcdc0edb2dcb6d07306acb5bc5c1
- memory/journal/2026/2026-10-28-diminishing-returns-bar.md blob 0690e44cc16b01ff93897732d5ae62a9e3a8db5c
- memory/journal/2026/2026-10-28-doctor-practice-and-catalog-links.md blob 8dd4f6759dc805d3d8d479896cec6c934714e712
- memory/journal/2026/2026-10-28-erg-close-hand-recipe-dropped-ticket.md blob e73881b4e1c73010c8a6c10c3ca763559bdfc358
- memory/journal/2026/2026-10-28-gate-scope-and-doctor-kit.md blob 4f0ef85d00dedfb93a0a1ab1ed7494d93f925ef1
- memory/journal/2026/2026-10-28-pgrep-wrapper-retired-pr1914.md blob 0551f0e2a6e56cb3fac3041c7c8512b72d19cb75
- memory/journal/2026/2026-10-28-pi-openrouter-and-session-close.md blob 5de9b3926e621be846263abe285e1f19dabe3c40
- memory/journal/2026/2026-10-28-pi-padme-albert-route.md blob d0e3ce41587c446cc1898dfa02829a159b9b9be6
- memory/journal/2026/2026-10-28-raid-1298-f1-notes-evidence.md blob 3bad4c60df6726456a00cfb346dced51337b759f
- memory/journal/2026/2026-10-28-raid-1302-1306-wrapup.md blob af4766c8c85b6adcff8de6e8709f4593b62c7217
- memory/journal/2026/2026-10-28-raid-1303-pr1862.md blob 7824d3856b12fe9340baa836f0b6e665eec039c9
- memory/journal/2026/2026-10-28-raid-1307-1308-pr1874-pr1876.md blob b025a89144839f1145c52a39faa3bee29ec37300
- memory/journal/2026/2026-10-28-raid-534413-wait-roster-pr1927.md blob f7a8ecaef22c584d95ec353884081fad38bab262
- memory/journal/2026/2026-10-28-raid-6530fd-runtime-verbs.md blob a727265d27b352aaac480769f9b6292c03fefc01
- memory/journal/2026/2026-10-28-raid-b6aabf-worktree-adoption.md blob 46ff8c1241e51aff1bff569f612ed97efd4a46d5
- memory/journal/2026/2026-10-28-raid-f642df-1326-opt-out-not-refusal.md blob b9049d0860bac35f657ecfeb303baf2e8293f3cb
- memory/journal/2026/2026-10-28-raid-f7fa41-forge-leaks.md blob c3128641b2defca2c0c5d4f10cc9b3f515fad2b7
- memory/journal/2026/2026-10-28-readme-pr1853-f1-notes-gap.md blob 46b80db9a0a7a2f1713b8c104f867a2884e46315
- memory/journal/2026/2026-10-28-review-gate-flows-pr1863.md blob 1a6fa1f1016f65076fc80b0337afdff47e6a90ba
- memory/journal/2026/2026-10-29-doc-propagation-pr1945.md blob 4787e3e61783a31b516fd2ce3e49d0d5cfbd9f32
- memory/journal/2026/2026-10-29-docs-visit-first-global.md blob f8b6c69f31fd5044232daf986afc98e24f288904
- memory/journal/2026/2026-10-29-doifetch-out-of-install.md blob 7bf34ad3e6b57b7856772cd1ac53ea1973c67f1c
- memory/journal/2026/2026-10-29-harness-doctor-triage.md blob a274d26990f7f1250a01f535b91dafbf8336031a
- memory/journal/2026/2026-10-29-memory-redesign-day.md blob fc45bb3b7b29466b34b8e961959c9b0e2f8987b3
- memory/journal/2026/2026-10-29-raid-0a53b8-smelt-census-attribution.md blob a121f541941d3e4f0864be717763450bad850512
- memory/journal/2026/2026-10-29-raid-29bf18-gaze-close-and-deletion-path.md blob d4ccf4b4d25d9901462fd69899d704aa0edc81b7
- memory/journal/2026/2026-10-29-raid-6958fe-resident-budget-composition.md blob d4badd7938c964425884083c89041f1d69c71e7c
- memory/journal/2026/2026-10-29-ready-ticket-review-premise-check.md blob 63eeba57be3ef2d7623441ffc15e29013c13898a
- memory/journal/2026/2026-10-29-test-doctor-gate-contention.md blob d957ef56844100171084103526e47b1eb7c29644
- memory/journal/2026/2026-10-29-tracker-1309-closed.md blob 75b3a207ccce0db31d29bed3053ea918800bbdc3
- memory/journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md blob a287858279ae382c68916384d83a7f63ab0701a6
- memory/journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md blob 205ca0ccb1c481aa883dfbae9fb6f69d1eaaf214
- memory/journal/2026/2026-10-30-python-tool-baseline-github-runner.md blob 6dab6af6c2f5967ac05bb35ee228aee254b58ffe
- memory/journal/2026/2026-10-30-raid-70b3bc-codex-seat-effort-1365.md blob 5867c8b6f1e98863c0323979794c436a8cb20798
- memory/journal/2026/2026-10-30-raid-d2253c-gaze-seat-evidence.md blob f0fc42e20d025b9db66ca929f6f759d4c507c718
- memory/journal/2026/2026-10-30-rulings-and-memory-design-input.md blob 6e0ad2f403891ab6bcf88ceca2b894923754eacd
- memory/journal/2026/2026-10-30-test-doctor-reruns-probe-1367.md blob 5e8b5e0ba170f65170f5d9e6c75cc5b40d3dbf93
- memory/MEMORY.md blob 50c72ceb6e4b0015b0676253055e7d96c2c31e23
- memory/pending-capture-pr1211.md.txt blob 26e01ffb2bd8bd03d3de19392be738abef144587
- memory/reference_branch_cleanup_incidents.md blob 2b86ae5e2a5162b86e71dc5bfce9f7b37c62a791
- memory/reference_git_in_a_worktree_session.md blob 39b9e4da556a772de5b1f4b4d58c836decb48d2d
- memory/reference_zotero.md blob 3d67baefeaf32fd0078eb0223195018ec0f11cbb
- memory/SMELT.md blob aa757aedfcdfe83f02a0c65946e961dec2f406b9
- memory/topics/branch-cleanup-incidents.md blob 49f83c2807b1f4700b0045c6775119f77159d784 (previous page)
- memory/topics/ci-and-test-suite.md blob e3b7b07ea45c995ff91693fe40bf99a43bbab29c (previous page)
- memory/topics/git-worktree-session-guards.md blob bf429318378938e4c0bd2856f520a4878878575a (previous page)
- memory/topics/host-environment.md blob a0412fdf2197b80cf9ef5ec8ab93e44edf9b8d31 (previous page)
- memory/topics/memory-v8-acceptance-trial.md blob d4a52baf25e1eeb6b5a9d4cc64ff81226b8e49dd (previous page)
- memory/topics/memory-v8-governance.md blob 5f88f8fd08fad0732bd52112b6d75009d715e4e3 (previous page)
- memory/topics/raid-review-and-merge.md blob f1a8b60f5f79321b6328bea0c1546172e26b5dab (previous page)
- memory/topics/runtime-observations.md blob fcca87cf6dcc6573824637290c7d54be89d8dc0d (previous page)
- memory/topics/shared-checkout-concurrency.md blob a8dd3e66a9029b55bdd6dd25bf5b3a5aeb284863 (previous page)
- memory/topics/subagent-model-effort-levers.md blob 96ecf6ac8f150df60eb0843f5405a968bcc70468 (previous page)
- memory/topics/zotero-library.md blob 455e0df3e80c7eaa943626720a53559dbe170414 (previous page)
- rules/claude-code.md blob cb3de3b9b1cb1def134a8c20e40783100bf15be3
- rules/coding-bash.md blob 640a08b1f7fffed0d4890f4e7d8b1a8c76f3f823
- rules/coding-python.md blob e4e706abbd92592bfaeb9daba1c14835d831c459
- rules/git.md blob 61feb62736eeaaa3f1b555011648470e6b88cbc1
- rules/guards.md blob 789d82599f6ee2e82d59302e70c1f7d0ff6e46c4
- rules/prose/workpackages.md blob e2584c2b1061e910bb42762fe345be9e0a3373e3
- rules/state.md blob d0c940a9281fff4af0780bcd0d435a2e3a8f7e93
- rules/workflow.md blob 08d94979e1bb95e451ece5c4cd384f27c963499e
- rules/zotero.md blob 52da4fe95b92e8899cac430bdc95e2a5c5ddaa30
- skills/brood/SKILL.md blob f5c1014ca654bebb34c619bd5d02e51be21ff797
- skills/dashboard/SKILL.md blob 7892b01f86ccc9f4cc1606c8f22a13cd6c305011
- skills/gaze/references/panel.md blob 4aef0661eec517d37bd75a5f76b070835434cd27
- skills/hunt/SKILL.md blob 725fbb34cbec6ac19df1e03e7394d7a0ceaff74c
- skills/merge/references/claims.md blob e84abd172cc33ab480c6256b33e74a79050d812a
- skills/merge/SKILL.md blob f92e9c7d6d0a26028d38917980a8ca4c7804ab9e
- skills/raid/references/detached-gaze.md blob dd23ff59ce19c54c3ddc7d5575f00ed3d9859e36
- skills/raid/references/fix-and-regate.md blob 896c289008d2c531a92f4f13733aa524e689d48a
- skills/raid/SKILL.md blob c84892b53d2f24983506e997128410c197cc7e68
- skills/roar/runbooks/capture.md blob e4afee381a141be3c29b1eb39cdc047306d4951b
- skills/roar/SKILL.md blob 37017366ff99ede654ceff41c2e99cbc58e3817a
- skills/route/routes.json blob e4c960a862f863db79574353c495e2f104759859
- skills/route/routes-recommendations-claude-code.md blob 995a9a55ced5fb5e3009ddf9152e7e88720de143
- skills/route/SKILL.md blob 42e38ac198702f412ffbb46e17b71b652f5030b0
- skills/smelt/SKILL.md blob 4d5ea990f450bbd1823114ff75bb81fb5ae05db3
- skills/test-doctor/SKILL.md blob 736b258e0d4f010ac6a582a2bfebf041497e4995
- tickets/1346-*.erg blob origin/main:tickets/1346-*.erg
- tickets/1349-*.erg blob origin/main:tickets/1349-*.erg
- tickets/1349-make-each-hoard-a-rebuild-of-the-topics.erg blob e81d465d412b32a775f5813862d2bdb7a8abe76a
- tickets/1350-*.erg blob origin/main:tickets/1350-*.erg
- tickets/1351-*.erg blob origin/main:tickets/1351-*.erg
- tickets/1351-run-brood-once-on-the-harness-to-test-th.erg blob 6c5fa7d33b3746b10497eaaa7f47b6f2d7f2f27f
- tickets/1354-*.erg blob origin/main:tickets/1354-*.erg
- tickets/1369-cooldown-review-of-the-harness-governmen.erg blob b29ca81d8341a1305f7d8835832f162a213a5e39
- tickets/closed/1242-*.erg blob origin/main:tickets/closed/1242-*.erg
- tickets/closed/1243-*.erg blob origin/main:tickets/closed/1243-*.erg
- tickets/closed/1348-*.erg blob origin/main:tickets/closed/1348-*.erg
- tickets/*.erg blob origin/main:tickets/*.erg
