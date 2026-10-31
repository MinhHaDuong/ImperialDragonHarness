# Fifth smelt — department returns (appendix)

Date: 2026-10-30. Companion to [the report](2026-10-30-fifth-smelt.md). One section per department page, as returned by the department pass and then reviewed by the orchestrator; orchestrator amendments are listed in the report. Native-note text is in the [annex](2026-10-30-fifth-smelt-native-notes.md).

## Commission

Page bytes (capped measure): 7605 / 4096, OVER. All lines over the cap are pinned rulings (31 pinned lines); nothing was cut. Per SMELT.md this overflow signals rulings waiting for the author to promote (brood, ticket 1351).

### Sources examined
- memory/SMELT.md, .tmp/brief.md, .tmp/assign.txt (commission line)
- memory/topics/memory-v8-governance.md (rulings only)
- memory/topics/raid-review-and-merge.md (rulings only)
- memory/journal/2026/2026-10-30-rulings-and-memory-design-input.md
- memory/journal/2026/2026-10-23-model-transmission-authorization.md
- memory/journal/2026/2026-10-26-pr1633-merge-on-author-authority.md
- memory/journal/2026/2026-10-28-diminishing-returns-bar.md
- memory/journal/2026/2026-10-27-doctrine-escalation-pr1778.md
- memory/journal/2026/2026-10-29-memory-redesign-day.md
- memory/journal/2026/2026-10-27-session-close-held-tickets.md
- memory/journal/2026/2026-10-03-tracker-closure-pass-0205.md (linked ruling, verbatim quote checked)
- memory/journal/2026/2026-10-11-roar-clear-verdict-survey.md (no /compact before roar)
- memory/journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md (guards on guards)
- memory/journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md (remove the guard)
- memory/journal/2026/2026-10-05-brood-adoption-pr1187.md
- tickets/1349-make-each-hoard-a-rebuild-of-the-topics.erg, tickets/1351-run-brood-once-on-the-harness-to-test-th.erg, tickets/1369-cooldown-review-of-the-harness-governmen.erg
- rules/workflow.md, git.md, guards.md, claude-code.md, coding-bash.md, prose/workpackages.md, AGENTS.md; scripts/on-start-context.sh; skills/dashboard/SKILL.md; skills/roar/SKILL.md (grep)
- Native notes, all under /home/haduong/.claude/projects/-home-haduong--agents/memory/ (all 33 read; used ones listed below)

### Editorial changes
- New page; no previous Commission page. Rulings collected from four journal-backed topics/entries and 17 native notes, grouped: memory and rules; review, guards, escalation; work shape; access and authority.
- Rulings already held by a harness rule are pinned briefly with "Now in ...": Trust/Verify/Monitor, diminishing-returns principle, no second-order guards / remove the guard, escalation fork, Ask up first (rules/workflow.md); bounded waits (rules/coding-bash.md § Waiting for a background job); encrypted-in-repo and Brood (AGENTS.md § Project memory boundary); departments/caps/pinned rulings (memory/SMELT.md, not a rule); delta format (skills/dashboard, not a rule); model-service transmission authorization (scripts/on-start-context.sh, not a rule); night mode only partly (rules/workflow.md escalation step 3 "no author in the loop -> the advisor picks").
- Judgment call to review: per-PR waivers/overrides (1018, #1157, #1187, #1235, #1245, #1253, #1374, 1081, PR 1633) are NOT pinned one by one; they are case decisions scoped to their PR. The page carries one non-pinned line pointing to the raid page plus PR 1633. If the orchestrator wants every case decision pinned, they must be added (cost roughly 1.5 KB more).
- Author memory-design statements of 2026-10-30 (journal labels them "not decisions") are filed as "Stated intent, not ruled", unpinned.
- Native-note-only rulings are cited as `native <note>` (no markdown link: a relative link to the native store would fail tests/test_memory_v8_pilot.py's link resolution and is not public). Sources gives the base path. If the annex gets a repo path, these could become links to its anchors.
- Pinned wording: where the source holds a verbatim author quote it is quoted; where the source only states the decision (brood, encryption, departments, option B, 1196 option 1, escalation fork, no /compact, faster orchestrator, Pi) the source's own wording is condensed. The brief said "not paraphrased": these lines are the closest available to source wording; flag for author check.

### Second pass
- No previous commission page. Ruling-bearing caveats from the other two pages, checked:
  - memory-v8-governance: encrypted-in-repo decision (kept, pinned, now in AGENTS.md); "without the key ... never treating it as empty" (left to governance page; in SMELT.md); Brood adoption, Dream/Roar authority unchanged (kept, pinned); "author ruled out /compact before roar" (kept, pinned); "explicit author merge instructions ... do not grant future Smelt merge authority" (kept as Hazard, generalized to all per-PR waivers); RETIRE LEGACY 2026-10-01 (kept as Retired line, as the governance page already treats it).
  - raid-review-and-merge: 0205 tracker statement, "an author statement, not a rule held by memory" (kept, pinned verbatim); "guards on guards; doctrine is to remove" (kept, pinned); per-PR overrides "for that PR only" (kept as case-decision line + Hazard); 1075 rule scoping via PR #1329, "current rule text no longer contains the conflicting wording" (not pinned: now resolved in rules/git.md; left to raid page).
- Re-check of corrections: Ask up first, guards, TVM verified present in rules/workflow.md lines 7-212 by grep; transmission text verified in scripts/on-start-context.sh:18-23; prose contradiction verified at rules/git.md:9 and rules/prose/workpackages.md:14.

### Coherence notes
- Exposed contradiction (not settled): native feedback_prose_edits_are_on_main ("editing prose is on main", harness skills/rules prose) vs rules/git.md:9 ("Main is read-only ... Sole exception: manuscript prose") and rules/prose/workpackages.md:14 ("The harness repo keeps its no-exceptions gate"). The note itself acknowledges the disagreement.
- Cross-store contradiction: "no wait tickets" (native, 2026-10-29) vs "a reminder is an open Blocked-by ticket" (another store, per ticket 1349 probe; I did not locate that note).
- Tension, not contradiction: native feedback_no_blocking_waits accepts "one background command with a hard timeout"; rules/coding-bash.md says "Wait in the foreground with a bound". Both bounded; flag for author.
- Native feedback_dont_idle_on_background says ask Fable before EVERY author decision, including calls by right; rules/workflow.md says "Ask up first" then author for calls by right — consistent.
- Link risk: commission.md links raid-review-and-merge.md, which another agent is rebuilding (it may be renamed). The orchestrator should fix that link if the page moves.

### Unresolved questions; misassignment
- Annex path for native-note texts: unknown to me; pinned lines cite `native <note>` without links.
- Should per-PR case decisions be pinned individually? (see Editorial changes)
- 2026-10-26-pr1633 entry is mostly a review/merge episode; only its "merge" ruling is Commission. Likewise 2026-10-29-memory-redesign-day (audit numbers belong to memory governance) and 2026-10-27-session-close-held-tickets (PAT rotation belongs to Environment). Not misassigned, but other departments should also link them.
- Could not locate the "a reminder is an open Blocked-by ticket" note cited by ticket 1349.

## Site practice: git, worktrees and parallel sessions

Page: memory/topics/git-worktree-session-guards.md, 3936 / 4096 bytes (capped count, memory_sizes.py).
Merged into it: memory/topics/branch-cleanup-incidents.md, memory/topics/shared-checkout-concurrency.md (not deleted), plus legacy notes memory/reference_git_in_a_worktree_session.md and memory/reference_branch_cleanup_incidents.md.

### Sources examined

memory/SMELT.md
memory/topics/git-worktree-session-guards.md (previous revision)
memory/topics/branch-cleanup-incidents.md
memory/topics/shared-checkout-concurrency.md
memory/reference_git_in_a_worktree_session.md
memory/reference_branch_cleanup_incidents.md
memory/journal/2026/2026-10-09-rtk-git-exclusion.md
memory/journal/2026/2026-10-09-worktree-isolation-census.md
memory/journal/2026/2026-10-09-close-1074-guard-refusals.md
memory/journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md
memory/journal/2026/2026-10-08-tournament-publication-wrapup.md (head of each line only)
memory/journal/2026/2026-10-08-haiku-review-delay.md (head of each line only)
memory/journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md
memory/journal/2026/2026-10-14-1096-split-and-session-cleanup.md
memory/journal/2026/2026-10-14-1095-design-panel-pr1399.md
memory/journal/2026/2026-10-14-roar-exit-check-1098.md
memory/journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md
memory/journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md
memory/journal/2026/2026-10-02-local-main-double-carried-open-pr-commits.md
memory/journal/2026/2026-10-02-raid-1015-annotation-collision.md
memory/journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md
memory/journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md
memory/journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md
memory/journal/2026/2026-10-03-raid-0938-profiles-subsystem.md
memory/journal/2026/2026-10-04-review-subagent-switched-primary-checkout-branch.md
memory/journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md
memory/journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md
memory/journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md
memory/journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md
memory/journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md
memory/journal/2026/2026-10-12-t1053-arena-git-and-scoped-vram-wait.md
memory/journal/2026/2026-10-12-cross-repo-session-gaze-forks.md
memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md
New (assign line): 2026-10-23-branch-sweep-1644.md, 2026-10-23-worktree-gc-ownerless-locks-1638-1640.md, 2026-10-21-gc-liveness-scan-lazy-pr1583.md, 2026-10-27-dangling-prune-moves-to-install-pr1701.md, 2026-10-28-raid-b6aabf-worktree-adoption.md, 2026-10-30-push-by-commit-id-exit-code-1366.md, 2026-10-30-gate-record-lost-shared-ref-rewind-1366.md, 2026-10-28-pgrep-wrapper-retired-pr1914.md
Not read in full: 2026-10-13-pr1374-review-evidence/gate-and-author-comments.md (36 KB; relied on the previous page and the 1374 revision entry); 2026-10-14-roar-remeasure-1090.md (only through the previous page and the 1098 entry; its claims are retired to the raid department here).
Native: /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_classifier_blocks_rule_mandated_git.md, feedback_check_exit_codes_not_pipe_tails.md, feedback_sync_local_main_after_merge.md, feedback_vscode_sessions_share_worktree.md, project_main_guard_enforce.md, project_idh_tracked_tmp_leak.md (read, not used)
Rules: rules/git.md, rules/claude-code.md, rules/workflow.md, rules/guards.md, AGENTS.md
Current-state checks (2026-10-30, padme): scripts/worktree-gc.sh (384 lines; WORKTREE_GC_OWNERLESS_IDLE_HOURS default 72; Python cwd read with the uutils comment), skills/hunt/SKILL.md lines 101-112 ($RANDOM redraw, add && lock && echo), scripts/merge-gate.py line 461-466 (per-process ref, push by commit id), scripts/raid_land.py (calls sync-local-main.sh), scripts/claude-allow-check.py (narrow rules listed, update-ref -d left to the classifier on purpose), scripts/guard-destructive-bash.sh (pgrep clause), ~/.config/rtk/config.toml on padme (exclude ^git\b present), `git config idh.mainGuard` = enforce, tickets/closed/1366, tickets/1095 still open, hooks/reference-transaction present.

### Editorial changes

- Merged three pages into one department page; each claim is now present-tense guidance or hazard with scope and a link.
- Pruned as history (sources kept in Sources): the rtk-rewrite refusal catalogue and the `\git` / script-file remedies (legacy note), the 2026-10-09 census counts, the refusal shapes seen under the EnterWorktree guard; reason: rtk excludes git on padme/doudou (1078) and EnterWorktree is retired (1077). The legacy note's own text says it describes rtk-on-git as current; corrected by the 1078 entry.
- Pruned: loop-era cleanup recipes and their guard rationale (legacy reference_branch_cleanup_incidents.md); retired by rules/git.md § Branch cleanup after PR 1374. The incidents stay in the legacy note.
- Pruned: PR 1374 round-by-round defects of the delete-then-restore path (removed by the scope revision); the update-ref -d measurement is kept as a live hazard.
- Moved out (Retired lines name the destination): PR 1374 merge-on-code-review, 1090/1098 turn measurements, WAVE_BASE/annotation collisions -> raid and merge department; crossSessionInbound -> runtime/host.
- Refreshed: worktree GC from the new entries (lazy scan PR 1583, uutils readlink fix, pid-1 locks kept, 72 h owner-less reclaim, accepted dissent); hunt worktree recipe (b6aabf, verified in skills/hunt); push by commit id (1366/2035, verified in merge-gate.py); branch -d vs patch-equivalent branches (1644, 1096).
- Correction: the previous concurrency page's 1096 statement "the {pid} discriminator came from a transient shell" was kept as "a {pid} in a name does not prove liveness"; the hunt suffix is now `$PPID-$RANDOM` (claude-code.md/workflow.md), and $PPID in a subagent is the session's claude process (1077 entry), so the transient-shell detail described the older recipe. Not re-measured.
- Observed discrepancy, not a claim on the page: the 1638/1640 entry reports worktree-gc.sh at 404 lines after 1640; it is 384 now (later commit ca60f28b moved the residue rule into a sourced lib).

### Second pass (caveats of previous pages)

git-worktree-session-guards.md (previous):
- Two distinct guards (rtk rewrite vs containment) — retired: rtk exclusion + EnterWorktree retirement (Retired line 1).
- rtk exclusion scoped to doudou and padme; still applies to other hosts and other commands — kept ("other hosts unverified").
- Census counts are the census's own, not re-measured — retired with the census (Retired line 1).
- Refusals conditional on sessions that activated the runtime guard — retired with the catalogue (Retired line 1).
- EnterWorktree also moves cwd; plain worktree leaves Edit/Write on primary — kept as "a restart resets cwd to the primary; a relative edit hit main".
- Accepted residual risk: restore/checkout aimed at another tree lose their only guard — not on the page by name; covered by the 1077 decision. Flag: this residual is now implicit; orchestrator may wish to restore one clause if bytes allow.
- Gaze/gate seats could not reach review worktrees on several PRs — retired (EnterWorktree retirement; raid department holds the review side).
branch-cleanup-incidents.md:
- The page records evidence, does not restate the rule — kept (scope line).
- Loop incidents stand though the recipes are superseded — retired as practice (Retired line 2); incidents remain in the legacy note linked in Sources.
- update-ref -d bypasses worktree refusal — kept.
- PR 1374 merged on code-review approval, not fresh verify-gate APPROVED — retired here (Retired line 4, raid department).
- Roar preserved a branch held by another session's locked worktree because ownership was not established — implicit in the rule (roar task scope); not restated. retired: rule text covers it (rules/git.md "Worktree removal also requires task ownership").
- 1090: earlier 16 -> 14 comparison does not establish savings; 1098 three-action tail is an estimate — retired here (Retired line 4).
- Dead-pid locks made git refuse branch delete until unlocked (2026-10-12) — retired: superseded by worktree-gc lock handling (page GC bullet); not given its own Retired line — orchestrator note: covered by GC refresh.
- git worktree remove deletes ignored files — kept (hazard).
- PR 1399 records design, not implementation; 1095 deferred — partially kept (1095 cited; ticket still open, verified). Implementation status line dropped for bytes; retired: 1640 implemented the ignored-file check for GC.
shared-checkout-concurrency.md:
- Direct pushes to main declined by ruleset — kept implicitly ("local main carried commits into a peer's PR"); main guard enforce added.
- Shared annotation base: one wave is one positive case, not a measured rate — retired (Retired line 5, raid department).
- Read-only reviewer: brief forbade edit/commit/push, the switch was none of these; whether briefs should name switching is a rule question — kept as hazard wording ("a 'no edit, commit, push' reviewer switched the primary's branch"); rule question not settled here.
- 1015 suggestion is that entry's proposal; 1016 is the decision record — retired with Retired line 5.
- Hypothesis: shared primary checkout as common factor — kept (Open questions).
- Live user files: no work lost, split went to the author — kept in substance (hazard), outcome detail dropped as history.
- Cross-session messages held until crossSessionInbound — retired (Retired line 6).
- PR 1300 branch held -> forge auto-merge — retired (Retired line 7).
- Primary vs clean tree test differences (1091, 2026-09-29) — kept (1091).
- Cross-repo base: forked gaze PR not found — kept.
- 1096: authorized census, not roar scope expanding — kept implicitly (rule); retired as history.

### Coherence notes

- rules/git.md "Verify a forge mutation by reading it back, in the same command" vs the 2035 entry (author merged without read-back and declined to narrow the rule; the entry says "the distinction below is memory, not rule"). Exposed as an open question; the page states the observed git semantics only, not an exemption.
- rules/claude-code.md forbids EnterWorktree: page agrees.
- rules/workflow.md § Delegation ("forbid add/commit/push explicitly") does not name branch switching; the #1183 episode is recorded as a hazard, no rule proposed.
- raid-review-and-merge.md also lists PRs blocked by the EnterWorktree guard (#1309 etc.); left there.
- host-environment.md holds the grep-is-ripgrep fact; not duplicated.

### Unresolved questions

- Forge read-back rule vs commit-id push (above).
- Hosts other than padme for the rtk exclusion and mainGuard: doudou not re-read in this pass.
- Whether the accepted residual of 1077 (restore/checkout aimed at another tree unguarded) should stay explicit on the page; dropped for bytes.

### Entries misassigned to this department

- 2026-10-27-dangling-prune-moves-to-install-pr1701.md: idh install and skill links, plus PATH dotfiles -> architecture/install or Environment.
- 2026-10-28-pgrep-wrapper-retired-pr1914.md: bash guard hook for pgrep/pkill -> Environment or guards/hooks department.
- 2026-10-21-gc-liveness-scan-lazy-pr1583.md: used here for the GC scan; its make-check timing and the missed /pulse skill also belong to the CI and test-suite department.
- 2026-10-28-raid-b6aabf-worktree-adoption.md: worktree part used; the 1309 runtime live-control part belongs to the runtime department.
- 2026-10-30-gate-record-lost-shared-ref-rewind-1366.md: git mechanism used; gaze rounds belong to raid and merge.

## Site practice: raids, review and merging

Page: memory/topics/raid-review-and-merge.md, 3975 / 4096 bytes capped (was 21469 bytes total; previous capped size over 4096).

### Sources examined
- memory/topics/raid-review-and-merge.md (previous page, blob f1a8b60f5f79321b6328bea0c1546172e26b5dab)
- memory/journal/2026/2026-10-14-pr1390-review-evidence.md blob 377bc0b8b30e5ebd8623f9eeb6867e5e67155069
- memory/journal/2026/2026-10-15-morning-healthcheck-merges-ticket-revalidation.md blob 5666c684fd9d5d40d9aff83da23b8662c8cdae24
- memory/journal/2026/2026-10-19-pr1456-review-and-attribution.md blob b1ca018dc5925215b95ff4b782e8c25ab60b235f
- memory/journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md blob de5fb000dd07a7ad9cf9a9fbcda236b2938d9d0e
- memory/journal/2026/2026-10-20-raid-1136-1137-1126-and-1100-split.md blob 7bd5d3e5116e89fff7edc50eb455bbe5205b26ed
- memory/journal/2026/2026-10-20-raid-1150-and-1146-integration.md blob 1d53dfec32b966cff7958fba2d77cd425a6740d2
- memory/journal/2026/2026-10-21-1153-stack-landed.md blob d0aac8057e2669f4c5d7a69cc47ab560ab44a756
- memory/journal/2026/2026-10-21-await-external-probes.md blob fa046f90f7e49bcab64c21a33ec2d297d1e44b2c
- memory/journal/2026/2026-10-21-gate-on-folds-and-wall-down.md blob 1cb53e84eacaf43f2b1bbb4c602773de4cd7c48d
- memory/journal/2026/2026-10-21-raid-1170-1173-1175.md blob 81e9802221abaeb3a6941529aa86b4600d6e8f00
- memory/journal/2026/2026-10-21-raid-stack-and-merge-helper.md blob 3ae32b94ae02cb4729b99b77149684ec57e757ff
- memory/journal/2026/2026-10-21-velocity-raid-1167-1169.md blob 0e2216e1a23cd92a397cd688c774816f1bcc390d
- memory/journal/2026/2026-10-23-review-merge-1634-1635.md blob 3af36736ec26bf0e3026a715631b926950029dee
- memory/journal/2026/2026-10-26-evening-review-ceremony.md blob 3295d0eaabb957a77e1bb471a88de488a3c4f4dc
- memory/journal/2026/2026-10-26-raid-1212-1211-1221-1219-1220-1215.md blob 86a2b603b5a7bb23f17c1de720e6d6938b2390ea
- memory/journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md blob 84c2cfb2735ce94c15306952368645e10f2ccdac
- memory/journal/2026/2026-10-27-erg-sync-molt-step-1732.md blob 2bae380bc13a9b5eed8c32af3da670b424f89e39
- memory/journal/2026/2026-10-27-hunt-phases-1235-override-merge.md blob cc0a254a24cc177daedb84df103dde9f1915dad4
- memory/journal/2026/2026-10-27-raid-1214-1218-waiting-follies.md blob 0118b8b5ac34c82b5a5104e4527517fa902b2564
- memory/journal/2026/2026-10-27-raid-b-followups.md blob 8fbb7cc28bc24b83dcb0ed53106c800c9abd6495
- memory/journal/2026/2026-10-27-raid-optimistic-merge-afternoon.md blob 12cc149ee7bdc69099cf06dc47f024e8ff26cba8
- memory/journal/2026/2026-10-27-raid-sitrep-ticket-1246.md blob 69da9506d0d25b1aabdf39b6bd25a8d1d03adac7
- memory/journal/2026/2026-10-27-review-cost-raid-and-redesign.md blob 8a8aeb83e89ff670dea51285fd50c11e8f57609f
- memory/journal/2026/2026-10-27-roar-1841-watchlist-closures.md blob 4ce8995dc6684138a3977c2f940bbea98c8e2883
- memory/journal/2026/2026-10-28-erg-close-hand-recipe-dropped-ticket.md blob e73881b4e1c73010c8a6c10c3ca763559bdfc358
- memory/journal/2026/2026-10-28-raid-1302-1306-wrapup.md blob af4766c8c85b6adcff8de6e8709f4593b62c7217
- memory/journal/2026/2026-10-28-raid-1303-pr1862.md blob 7824d3856b12fe9340baa836f0b6e665eec039c9
- memory/journal/2026/2026-10-28-raid-1307-1308-pr1874-pr1876.md blob b025a89144839f1145c52a39faa3bee29ec37300
- memory/journal/2026/2026-10-28-raid-534413-wait-roster-pr1927.md blob f7a8ecaef22c584d95ec353884081fad38bab262
- memory/journal/2026/2026-10-28-review-gate-flows-pr1863.md blob 1a6fa1f1016f65076fc80b0337afdff47e6a90ba
- memory/journal/2026/2026-10-29-raid-29bf18-gaze-close-and-deletion-path.md blob d4ccf4b4d25d9901462fd69899d704aa0edc81b7
- memory/journal/2026/2026-10-29-ready-ticket-review-premise-check.md blob 63eeba57be3ef2d7623441ffc15e29013c13898a
- memory/journal/2026/2026-10-29-tracker-1309-closed.md blob 75b3a207ccce0db31d29bed3053ea918800bbdc3
- memory/journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md blob a287858279ae382c68916384d83a7f63ab0701a6
- memory/journal/2026/2026-10-30-raid-d2253c-gaze-seat-evidence.md blob f0fc42e20d025b9db66ca929f6f759d4c507c718
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_review_trust_verify_monitor.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_gate_record_staleness.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_ticketwork_automerge.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_no_blocking_waits.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_dont_idle_on_background.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_peer_relayed_rulings.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_delta_format.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/project_faster_gaze_orchestrator.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/project_attribution_friction.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/project_pulse_gaze_visit_agenda.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_grep_every_site_before_delegating_contract_change.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_sync_local_main_after_merge.md
- /home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_check_exit_codes_not_pipe_tails.md
- skills/merge/SKILL.md, skills/merge/references/claims.md, skills/raid/SKILL.md, skills/raid/references/fix-and-regate.md, skills/raid/references/detached-gaze.md, skills/gaze/references/panel.md, skills/hunt/SKILL.md (current-state checks)
- The ~50 2026-10-02..10-15 episodes linked by the previous page were NOT re-read individually; their claims were judged from the previous page's summary against current skills (see Unresolved).

### Editorial changes

Rebuilt from scratch as a present-tense guide; history condensed hard.

Pruned (journal keeps the episodes):
- Merge-helper mechanics (`erg-pr-merge` short-claim refusals, CI-pending refusal, head-branch rule, auto-merge race, #1533 API arming): the helper was deleted (ticket 1178, PRs 1617-1619; `skills/merge/erg-pr-merge` absent on 2026-10-30). Source: 2026-10-21-gate-on-folds-and-wall-down.md.
- 15-file breaker and the override cases it caused (#1179, #1060, the 1153 stack): wall torn down (PR 1614). Same source; 2026-10-21-1153-stack-landed.md.
- Per-PR catch and degraded-panel lists of 2026-10-02..10-13: history. Their lasting conditions merged into the "Seats" and "Rounds" bullets (self-only and family-mislabelled seats, invented waiver, head moves voiding review).
- Attribution-record counts (33 and 36 records): telemetry; lives in memory/evidence/attribution/.
- 2026-10-13..10-15 integration notes: history.
- Tracker-0205 author statement: belongs to Commission (not copied here; Commission agent should hold it if still wanted).

Merged: optimistic-merge tiers (opt, flows), gate-record staleness (1246, cost, 1720, 1703, native note), seat evidence (1303, roster, 29bf, rb, d225), round limits (cost, vel, 29bf, native notes trust-verify-monitor and grep-every-site).

Refreshed (evidence):
- Tiers, before/after gate and "red reported, never reverted": skills/merge/SKILL.md § Gating tiers (read 2026-10-30).
- Self-only record counts as no record: merge § Gating tiers.
- Ticket-close repair wording: skills/merge/references/claims.md § Repair now stages both sides (the 1316 entry said it was unchanged at the time; it has since been fixed).
- TMPDIR-in-worktree failures: ran `TMPDIR=$W/.tmp/tt pytest tests/test_project_census.py`: 14 passed (with and without). test_project_coherence_prompt.py no longer exists. Hook tests fixed by #1688, harness-doctor test by b066eee6. Retired.

Corrections: none against journal episodes. Note the 1559 "about 8 h" figure comes from the native note trust-verify-monitor, not the journal entry (the entry gives the sequence, not the hours).

Link style: claims cite reference-style tags ([opt], [flows]...) whose definitions sit in Sources. The tags count against the cap; the URLs do not. If the orchestrator reads SMELT "inline source links count" as forbidding this, inlining would add about 1.1 KB and force cuts of conditions: flag for decision.

### Second pass (previous page caveats/conditions)

- "Procedures live in skills; nothing here amends them": kept (opening line).
- Panels caught defects mechanical layers passed (#1179, #1133, #1211, #1180, #1153): retired as history; condition kept generically under Seats/Open questions (catch rate unmeasured).
- Gates caught process defects (0938, raid-1008, 1014 sed): retired, history.
- Red-team alone found blockers (#1354); other-family seats found what same-family missed (#1298, #1303, #1372-1374, #1377); same-family also caught (#1328, #1354): kept as the hypothesis line in Open questions.
- Round-1 fix of narrower guard introduced new drops; author deleted guard (1081): retired, history; the general condition kept as "fresh blockers at round 3 mean redesign".
- Spawn success not reliable; silent child cap; seat never reported: retired, superseded by notes `seats:` evidence and wait-roster deadline (merge § Gating tiers, ticket 1327); the live form (self-only, mislabelled seats) kept.
- Executors without Agent tool degrade; detached headless seats restore; vibe -p blocked: retired, superseded by headless seat door (detached-gaze.md, ticket 1326). Vibe status not re-verified (runtimes dept).
- openrouter-budget seat fails open: retired, not seen after 2026-10-13; unverified (runtimes dept).
- Session isolation guard blocked seats: retired as history (rules/claude-code.md forbids EnterWorktree for that reason; git dept).
- Gates refuse when writer pushes mid-review: kept (moved head voids review).
- Cross-repo gaze resolving PR numbers in another repo: NOT on page (space). Recurred on #1704 (2026-10-27, hunt entry): arena cwd, needed --repo. Flag: orchestrator may add one line "gaze from another repo's cwd needs the worktree path and --repo" if budget allows (about 90 bytes free). Not silently dropped.
- Single-family panels when cross-family unavailable: kept (Seats bullet).
- Shared scratch folders leaked a review prompt (#1288): retired, history; not seen since; unverified.
- Override cases list (both periods): retired (one Retired line).
- Invented waiver by subagent: kept (Hazards).
- Raids skipping Imagine/Plan for single tickets: retired; raids since run Imagine/blind-spot (1303, roster, d225).
- erg-pr-merge refusals, mid-gaze merge follow-up, closing a ticket broke six tests on open-path links: retired with the helper; the open-path-link condition not re-verified.
- Tickets age, premise recount: kept ("Recheck premises before a raid", [vel][prem]: 1166, 1168 of 4 and 1337, 1338 of 5).
- Executor crashes salvaged on the same branch: retired, history (1136 salvage repeats it; worktree-salvage.sh).
- Adjacent Blocked-by edits conflict, no checks on second PR: retired, history.
- PLACEHOLDER prompt / glob paths to delegate: retired into "Invocation" (literal SESSIONID, same class).
- Ticket 1079 short-claim resolution, #1377 hand-normalised body: retired with helper; current canonical-claim requirement kept.
- `Ticket:` statistics over 400 PRs: retired, derived history.
- Auto-merge left PRs open after green (#1324, #1414): kept, merged with #1472 open question.
- Author statement on tracker 0205: moved to Commission.
- Attribution validator requires provider-qualified ids: kept (Invocation: merge-gate needs provider-qualified id).
- Writer/reviewer sharing a provider is not decorrelation: kept implicitly via Seats; rule is in decorrelation.md.
- Hypotheses section (gates vs panels pairing): kept as the Open-question hypothesis.
- Arena force-merge, 1080/1089, 1098 DEGRADED, 1101-1109 trail, #1403 grammar: retired, history.

### Coherence notes

- Raid Phase 7 "revert last merge" contradicted merge step 9; settled by #1863 (author option A). Page states the current rule.
- #2013's third fix round went past the fix-and-regate two-round rule on the author's standing "don't wait": recorded as a departure; the rule stands (fix-and-regate.md, author ruling 2026-10-27). Page says so.
- PR 1725 merged without a record on the author's "Just merge": an author act, not practice; Commission page should carry it.
- Native note gate_record_staleness names `erg-pr-merge` and `/tmp/chain-merge.sh`: stale (helper deleted; raid_land.py replaces it). Its binding-to-candidate core is still true.
- Native note dont_idle_on_background says "ask Fable before EVERY author decision, even ones by right"; rules/workflow.md § Escalation says ask the advisor first, author's calls by right "wait". Compatible (advisor first, author still decides); page states only "advisor before the author".
- Overlap with git dept: 1366 ref rewind (one hazard line, link). With Commission: night mode, Trust-Verify-Monitor, optimistic merge, peer-relayed rulings.
- Old page linked branch-cleanup-incidents.md and runtime-observations.md, zotero-library.md; links dropped with their claims.

### Unresolved; misassignments

- The ~50 older episodes linked by the previous page were not re-read one by one (context budget); claims from them were retired as history against current skills, not corrected against the episodes. A stricter pass could re-read any the orchestrator wants kept.
- One condition carried in Retired for space only (not retired by evidence): gaze from another repo's cwd needs the worktree path and --repo (#1360, #1361, #1704). Orchestrator may promote it if the cap allows.
- 2026-10-14-pr1390-review-evidence.md (48 KB): almost entirely attribution telemetry (seat reports, runtime headers, verdict blocks, identity limitation note). Experience content: identity limitation (bare model ids, runtime-masked) and a recovered gate session. Belongs with memory/evidence/attribution/ under SMELT § Read 1; no claim drawn.
- 2026-10-15-morning-healthcheck: mostly ticket revalidation and hoard/yawn naming rulings (Commission/memory depts); review-transport refusals (unverified remote, private paths in CI comment) could go to the runtimes/hosts dept.
- 2026-10-21-await-external-probes: wait design across runtimes; belongs to runtimes (waits bullet kept here only as practice).
- 2026-10-27-erg-sync-molt-step-1732: skills/molt dept, not review.
- 2026-10-27-capture-pr-and-merge-commit-attribution, 2026-10-19-pr1456: memory/attribution dept.
- 2026-10-29-tracker-1309-closed: mostly runtimes (notify backends); only the ticket-only capture refusal used here.
- 2026-10-30-gate-record-lost-shared-ref-rewind-1366: also on the git line; one hazard here.
- Auto-merge delays (#1472 about 7 min): cause not established; not re-measured.

## Site practice: CI, tests and doctors

### Sources examined
memory/SMELT.md; memory/topics/ci-and-test-suite.md (previous)
The 15 entries of the ci line of .tmp/assign.txt (memory/journal/2026/): 2026-10-21-pulse-gate-wall-time, 2026-10-21-pulse-testing-expert-1541, 2026-10-21-velocity-scan-stale-baseline, 2026-10-27-harness-doctor-and-project-coherence, 2026-10-27-harness-doctor-idh-root-paragraph-1240, 2026-10-27-test-doctor-rename-1228, 2026-10-27-trace-wall-time-pr1722, 2026-10-27-yawn-to-rest-pr1782-pr1789, 2026-10-28-after-merge-red-1322-cleared, 2026-10-28-doctor-practice-and-catalog-links, 2026-10-28-gate-scope-and-doctor-kit, 2026-10-29-harness-doctor-triage, 2026-10-29-test-doctor-gate-contention, 2026-10-30-python-tool-baseline-github-runner, 2026-10-30-test-doctor-reruns-probe-1367
Not re-read (old linked episodes, relied on the previous page's summary): the Oct 2-15 journal entries linked there. Unverified for that reason.
Repo checks: Makefile, scripts/pytest_workers.py (CAP = 24), tickets/closed (1045, 1082, 1088, 1227, 1322, 1329 all closed), skills/hunt/SKILL.md line 14, skills/test-doctor/SKILL.md, scripts/ listing.
Native: six notes listed in the brief, in /home/haduong/.claude/projects/-home-haduong--agents/memory/.

### Editorial changes
- Pruned (superseded): Oct 2 suite economics, test counts 1514-1627, the contradicted "ticket 1045 open" (now closed); erg-pr-merge waits (helper deleted, ticket 1178); runner nondeterminism (fixed); read-back census, 1090 remeasure and raid counts (belong to merge/wrap-up pages; sources still in the journal).
- Merged: the gate measurements of 10-21 and 10-29 into one claim; the doctor rulings into one bullet.
- Refreshed: workers rule (pytest_workers.py, cap 24 verified); the seam F1 finding is fixed in hunt text (line 14 accepts a directory).
- Corrections: none to a source episode.

### Second pass (previous page caveats)
- Suite 81s to 33s, xdist -n 4, lint ~2 s: retired (superseded by 10-21 and 10-29 measurements).
- Hermeticity guard 0940 re-scope: retired (no live consequence; not verified).
- Runner nondeterminism PR 1133, awk/grep/bash versions: retired (fixed).
- act equivalence; -j last wins; .git dropped; socket path over 108 bytes: kept. Commit 715c59d7 counts: retired (stale).
- Ruleset seven of ten checks and no bypass; "I would rather wait than bypass": kept as open question (unverified).
- Leftover podman service 12 h 42 min and "experiential memory, not instruction change": retired (anecdote); not kept as a hazard.
- PR 1245 stuck check 1h49 and no --watch: kept (hazard). Stale rollup twice: kept.
- Single flakes (attribution_query, collision script), exit 77 mapping, SELF_PR_NUMBER trap, padme uv float drift, pdftotext skip: retired (not verified current; low reuse). Could return if the author wants them.
- 1088 local-ci SKIP exit 3: kept. "52-line ticket took 13 min, no per-step timings": retired.
- erg-pr-merge / 1082 / erg-pr-status: retired (helper deleted per 10-21 entry; no script in scripts/).
- Author decisions: no pre-push hook, local merge gate (1045), local CI on padme in merge skill: retired (1045 closed; the merge skill now mentions a local gated merge).
- Read-back census, 1090 remeasure, raids 1080/1089, rename integration: retired from this page (other departments).

### Coherence notes
- workflow.md "Check scope" speaks of .idh-checks.json; it does not exist in this repo (rule untouched, page silent).
- Page claims "no second-order guards" and "no wait tickets" (author rulings, native notes) and agrees with workflow.md Severity floor.
- Possible overlap with the review/merge departments: attribution-capture failures (10-27 entries) not placed here. Merge landing details (gate record staleness, 10-28 doctor-practice) belong to merge dept.

### Unresolved / misassigned
- Ruleset state (seven required checks, no bypass) unverified.
- 10-27 yawn-to-rest, 10-28 gate-scope/doctor-kit and 10-29 triage contain merge/review/attribution material (gaze rounds, verify-gate refusals, attribution capture failures, molt checkout fix 1329, allow rules 1331) that belongs to the merge/review and git-guards pages; only doctor facts were taken here.
- 2026-10-30 python-tool-baseline mixes rule history with a CI fact; kept the CI fact.
- Cap check: ci-and-test-suite.md reported by memory_sizes.py (see final message).

## Environment: hosts, services and external tools

### Sources examined
memory/topics/host-environment.md (old), memory/topics/zotero-library.md, memory/reference_zotero.md
memory/journal/2026/2026-10-16-zotero-local-only-decisions.md
memory/journal/2026/2026-10-16-zotero-pyzotero-and-display-leak.md
memory/journal/2026/2026-10-16-zotero-verbs-exact-match.md
memory/journal/2026/2026-10-29-doifetch-out-of-install.md
memory/journal/2026/2026-10-27-raid-prep-wave0-and-1206-doudou.md
memory/SMELT.md, rules/zotero.md, rules/coding-python.md, tickets/1349-*.erg
Native: reference_padme_cores, reference_padme_home_snapshots, reference_padme_tmp_sweep, reference_doudou_nextcloud_sync, project_agent_pat_rotation, feedback_gh_admin_delegated
Not re-read (trusted from old page, linked episodes unchanged): relocation-lessons, routing-review-round, permissions-allow-all, t1048-cycle3, zotero-local-api-preference, molt-zotero-reconcile-removed, zotero PR1143 and train entries.

### Editorial changes
- Merged zotero-library.md and reference_zotero.md into the page. Dropped Zotero user id/username/collection id (low value; reference_zotero stays in git history). Kept key location, group-download 404 asymmetry.
- Retired: per-skill transport choice (superseded by local-only rulings 2026-10-15/16); delegated GH admin (superseded 2026-10-27 by narrow PAT, ticket 1196); detailed permission/credential incident narrative condensed to guidance.
- Refreshed: scripts/zotero.py exists (2909 lines now), pyzotero in pyproject; doifetch.sh exists; padme CPU via `lscpu`: Threadripper PRO 3975WX, 32 cores, 2 threads, nproc 64. This resolves the 1349 contradiction: 3975WX/32 is correct; "3945WX/12" is wrong (stale native note, not in the notes I read).
- Corrections: old page said "uv rule now agrees"; kept as pointer to rule only.

### Second pass (old host-environment page)
- end-marker loader fix (0987): kept (shortened to "use an end marker")
- ssh bash -s stdin swallow: kept
- grep=ripgrep function, /usr/bin/grep: kept
- bare pytest lacks PyYAML: kept (shortened)
- non-login ssh PATH; doudou lacked only age and act: kept PATH; "age/act" retired: dated, unverified now
- uv clone/copy, 5 MiB vs 626 MB measurement: kept the rule pointer; measurement retired (rule in coding-python.md carries it)
- snapshot exclusions for uv/.venv unexercised: retired (cap; hypothesis line kept in Open questions)
- permissions PR #1344: kept core; drafted deny list audit, `git -C` bypass, idh install union, duplicate rtk hook: retired (cap), episode linked
- credentials: token as allow rule, curl argv `-H @-`: kept `-H @-`; copy-to-disposable-HOME rejection: retired (cap)
- key displayed 2026-10-12: kept as hazard
- hypothesis snapshots pin venv copies: kept
Old zotero-library page:
- group download 404: kept; local API preference: kept; reconcile on demand: kept; #1437 repaired empty reports, 1112/1113 follow-ups: retired (unverified, cap); `attach`/`enrich` version-guard asymmetry (#1179): retired: pre-dates local-only rewrite, not verified; Zotero 10 writable survey: kept brief.

### Coherence notes
- Zotero rulings (local API only, no Web API) fit rules/zotero.md ("created through the local API"); no conflict found.
- 1349 padme CPU contradiction resolved as above; the conflicting native note is not among the six I read.
- project_agent_pat_rotation / gh_admin_delegated agree after supersession.
- reference_padme_home_snapshots says "moves to padme's own host store" (ticket 1350 design): not placed in page.

### Unresolved
- Doudou trash emptying outcome; snapshot-pin hypothesis; `backfill.md` exit-code caveat dropped for cap (minor).
- Misassigned: none. The raid-prep entry is mostly Site practice/queue; only the ssh heredoc near miss used.

## Environment: runtimes, models and routing

### Sources examined
memory/topics/runtime-observations.md
memory/topics/subagent-model-effort-levers.md
memory/feedback_subagent_model_effort_levers.md
memory/SMELT.md
memory/journal/2026/2026-10-27-pi-skills-standard-root-pr1690.md
memory/journal/2026-10-28-pi-openrouter-and-session-close.md (under memory/journal/2026/)
memory/journal/2026/2026-10-28-pi-padme-albert-route.md
memory/journal/2026/2026-10-27-vibe-headless-seat-1279.md
memory/journal/2026/2026-10-28-raid-6530fd-runtime-verbs.md
memory/journal/2026/2026-10-27-raid-forge-less-and-guard.md
skills/route/SKILL.md, skills/route/routes.json (grep), adapters/pi/agents/code-reviewer.md, scripts/ listing
/home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_pi_is_first_class.md
/home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_reload_helpers_in_long_sessions.md
/home/haduong/.claude/projects/-home-haduong--agents/memory/project_faster_gaze_orchestrator.md
Older linked episodes were not re-read this pass; their claims were carried from the previous page text.

### Editorial changes
- Pruned (retained in journal/Arena): tournament cycle 2/3 figures, Mellum, greedy divergence, provider limit list, launch-line counts, wave C advisor test, Haiku arm N cost. Reason: Arena separation (PR #1386) and route grid own them; SMELT: not environment guidance.
- Merged: subagent-model-effort-levers.md and the legacy note into Current guidance (first two bullets). Orchestrator may delete the topic file.
- Refreshed: Pi skills root (PR 1690), Albert/OpenRouter wrappers, Vibe headless (supersedes 2.25.8 finding), runtime.py wake marker, gaze self-only observation.
- Hypotheses labelled in Open questions; 195-minute gaze kept as an open question.
- Not verified: Strata/Flash-Next still production now (routes.json still lists llama-server a/Strata arms as historic config); pi-subagent-link fix state (PR #1390 stated by prior page).

### Second pass (previous page caveats)
- Single-run/named-version scope: kept (header).
- pi no Agent tool, DEGRADED: kept (Hazards). 195-min gaze attribution not a measurement: kept (Open questions).
- AGENTS file precedence: kept. Unknown-model fallback, declare explicitly: kept.
- padme pi auth not_ready for anthropic/openai/openrouter: retired: superseded by the 2026-10-28 wrappers and Albert/OpenRouter routes.
- pi-haiku `</dev/null`: kept. Dangling subagent links repointed to 1.1.0: retired: transient fix.
- pi-subagent-link "nothing to link": kept (fixed by PR #1390). Defaults resolving away: kept.
- Local server superseded default, Strata quirks: kept. Roar repointed six agents: retired: past event.
- Vibe: child sessions not exposing connector: retired (unverified, old); detached seats blocked: retired (superseded by 1279); runtime-masked id: kept.
- Codex: AGENTS.md in CODEX_HOME / rules not instruction-bearing on 0.159.3: retired: stale version, unverified. gpt-6-luna accepted / haiku rejected: retired: version-bound, unverified. Usage-limit seat failure: kept.
- Tournament caveats (corrections, Cycle 3 voids, Mellum, divergence, provider limits, 404 scored OK): retired: Arena owns them. "Babysit your takeoffs" remark: retired: adds no rule here.
- Routing rollout (chooser removal, risk-scaled decorrelation, advisor test, launch-line counts, 98% pinned): retired: route skill owns; counts are history.
- Hypotheses section: kept in Open questions. Arena separation refresh: retired as one line.
- Levers page: session effort/model propagation kept; 2.1.267 caveat on pinned-effort models kept; 404 on tier tokens kept (one version); Codex spawn_agent honouring kept; fork_turns 46/109 retired (honouring unmeasured, no guidance); fable-token gap retired: rules/claude-code.md now lists fable.

### Coherence notes
- rules/claude-code.md lists `fable` among short tokens; the loose note lists `sonnet|opus|haiku` only: the rule governs; the legacy note is merged away.
- Rule says Agent definitions carry no `model:` (consistent with the 404 observation).
- Raid 6530fd journal: rule text was moved to skills/route/routes-recommendations-claude-code.md § Launching; not checked here beyond the journal.
- Possible overlap with Site practice/raid departments on gaze self-only and forge-less raid facts; I kept only runtime-bound facts.

### Unresolved / misassigned
- Entry raid-forge-less-and-guard is mostly Site practice/host (guard enforce, PAT); I used only the self-only gaze fact and cross-family consent. Entry pi-skills-standard-root also touches idh install (Site practice).
- The 2026-10-28 OpenRouter entry's journal file path is under memory/journal/2026/ (typo-free in the page links).

## Architecture: the memory system

Page: memory/topics/memory-v8-governance.md, 4092 / 4096 bytes (capped sections), was 7895.
Merged in: memory/topics/memory-v8-acceptance-trial.md (7806 bytes); orchestrator deletes it and drops its MEMORY.md line.

### Sources examined
memory/SMELT.md
memory/topics/memory-v8-governance.md
memory/topics/memory-v8-acceptance-trial.md
memory/feedback_rules_come_from_memory_consolidation.md
memory/pending-capture-pr1211.md.txt
memory/MEMORY.md
memory/journal/2026/2026-10-02-memory-v8-0918-pi-native-load-delivered-contradictory-note.md
memory/journal/2026/2026-10-15-fourth-hoard-merge-and-maintenance-fixture.md
memory/journal/2026/2026-10-29-memory-redesign-day.md
memory/journal/2026/2026-10-29-raid-0a53b8-smelt-census-attribution.md
memory/journal/2026/2026-10-30-rulings-and-memory-design-input.md
memory/journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md
(previously linked episodes: relied on the previous pages' accepted summaries; not each re-read in full in this pass, see Unresolved)
tickets/1346-*.erg tickets/1349-*.erg tickets/1350-*.erg tickets/1351-*.erg tickets/1354-*.erg
tickets/closed/1348-*.erg tickets/closed/1243-*.erg tickets/closed/1242-*.erg (Closed line)
conception/2026-10-29-memory-system-audit.md (§3.3, §6, §7, Correction)
conception/memory-v8/legacy-retirement.md, conception/memory-v8/pilot.md (grep)
skills/smelt/SKILL.md (grep), skills/roar/SKILL.md (grep), skills/roar/runbooks/capture.md (head), skills/brood/SKILL.md (head)
tests/test_on_start_memory_injection.py, tests/test_resident_census.py (grep), AGENTS.md:70-76
git log (SMELT.md, smelt skill, 1347/1348/1352/1353 tickets, PR #2002, f78334e6)
/home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_rules_are_law_memory_is_decree.md
/home/haduong/.claude/projects/-home-haduong--agents/memory/project_attribution_friction.md
/home/haduong/.claude/projects/-home-haduong--agents/memory/feedback_dragon_skill_names.md
Encrypted entries: 0 `.age` files in memory/ (find, 2026-10-30).

### Editorial changes
- Merged: acceptance-trial page into this page; kept only the trial facts that still guide (native contradictory-note delivery, Codex adoption vs Claude flag, Pi loading order and home-level AGENTS.md). Single-sample label kept.
- Refreshed: pipeline now v8-r4 rebuild (commits 4fd37a28, 4b932bc5; 1349 criterion 1 delivered, criterion 2 = this run); attribution records moved to memory/evidence/attribution/ (PR #2002; 202 files there, 0 left in journal); roar capture is runbooks/capture.md steps 2-3; /clear verdict still in roar step 11; brood still explicit-only, never run on the harness; census numbers from ticket 1346 log (22:20Z padme superseding 20:56Z; 09:02Z doudou) and audit Correction (77 % -> 25 %).
- New: Claude Code read census, index not injected at start, native-store probe (41 % rules in disguise / 52 % unique), inbox drain design (1349 option A, not built), DreamBench hypothesis, 1350/1354 open, capture-pr one call and 1243 closure, attribution capture snags (native note).
- Pruned to Retired (history kept in journal/git): delivery PR list and ticket closures; 1106 path migration; third-consolidation pin removal; backfill counts; producer/recorder attribution detail; trial operational details.
- Corrections: "index hook budget 2100 chars refused a line" withdrawn: index no longer injected (test_on_start_memory_injection.py) and test_resident_census.py no longer contains 2100. AGENTS.md:74 append-only wording question (raid 0a53b8) is resolved: f78334e6 rewrote AGENTS.md and SMELT.md Bounds has the git-mv carve-out.
- Legacy notes: feedback_rules_come_from_memory_consolidation.md and pending-capture-pr1211.md.txt get Retired lines (the first is retired advice; the second resolved by 1038 into memory/evidence/attribution/2026-10-06-review-attribution-pr1211.md). Neither is deleted by me.

### Second pass (caveats of previous pages)
memory-v8-governance.md:
- Uncleared material encrypted in repo, key never tracked: kept.
- Without the key, entry unreadable, skipped and counted, never empty: kept implicitly via SMELT.md; page states 0 .age files (condition lives in SMELT.md § Encrypted entries, which governs). Retired from page text: duplicated by the prompt.
- Private companion clause superseded: retired (line).
- Roar facts / smelt no rule promotion / journal append-only: kept.
- Results/cell verdicts live in conception, not memory: kept via Sources link to results; not restated (cap).
- Brood: evaluation records procedural fixture results only, not field benefit: retired from page text, kept in Sources (brood evaluation link); reason cap + page now states brood never ran on harness, the stronger current fact.
- Brood permits evidence-based edits to consolidated memories, journal append-only, Dream/Roar authority unchanged: partly kept (explicit-only, crystallisation needs request); the edit permission detail retired as restated by skills/brood/SKILL.md (authority).
- Index budget refusal: retired (no longer injected).
- Roar /clear survey numbers (20/64 above 256k etc.): retired as history; the /compact-before-roar exclusion is an author ruling -> Commission (not restated here; link to survey kept).
- Backfill zero events, no inference of historical coordinates: retired (history).
- Explicit author merge instructions do not grant future Smelt merge authority: retired from page; SMELT.md Bounds ("do not merge automatically") is the governing text. Commission may want it as a ruling.
- 1106 historical bytes keep former names; one archival link mapped; migration not consolidation: retired (history).
- Interrupted trial pass 3 not accepted processing: kept (with fifth hoard).
- No managed old-name alias across runtimes: retired (history; skills renamed).
- No model pin reconstructed for #1423/#1425: retired (history, evidence path).
- Historical append-in-place question unresolved: kept (Open questions).
- Legacy feedback is history, never current authority: kept (Retired line).
memory-v8-acceptance-trial.md:
- Single-session samples, not certification: kept ("Single samples, 2026-10-02 versions").
- Link-catch cause and framing corrected by later entries, original unchanged: retired (history; Sources keep the withdrawal and correction links).
- Detached flags consume positional prompt; Codex exception: retired from this page; belongs to runtimes department (version-specific: Claude Code 2.1.286, Vibe 2.25.8).
- Background launch without cwd, nothing written, primary verified untouched: retired (runtimes/concurrency).
- Concurrent detached sessions preserved both captures: retired (concurrency department).
- Claude flagged, Codex adopted contradictory note: kept.
- Vibe attributed correctly after grep; aborted Vibe misattribution corrected: retired from text (Sources keep both).
- Retired helpers fail; capture guard refused slug: kept for helpers; slug-guard retired (history).
- Pi credit depletion external limit: retired (history).
- Pi loading order; codex closed by CODEX_HOME AGENTS.md (PR #1147); pi re-ran on local llama.cpp (PR #1150): loading order kept; PR remediation retired (history).
- Metered Kimi-K2.6 pi leg never re-run: retired (history; not a live question) — flag if the runtimes page wants it.
- Pre-trial smokes excluded from margins: kept in Sources only.
- New 2026-10-02 pi entry: placement intent of home note unverified: kept.

### Coherence notes
- No contradiction with rules found. Page states no rule promotion and points to AGENTS.md § Project memory boundary.
- Native note rules_are_law_memory_is_decree is consistent with AGENTS.md (crystallisation is the author's act); it is an author ruling -> Commission.
- Native note dragon_skill_names (hoard->smelt rename rationale) is an author ruling -> Commission; not restated here.
- Commission: author rulings of 1348 (4 KB, 40 lines, departments, journal as source), 1349 option A, and the 2026-10-30 memory-design input are linked, not restated.
- The 2026-10-30 entry's government memo (cooldown, 1369) is Commission's; nothing here implements it.

### Unresolved; misassigned
- Previously linked journal episodes were not each re-read in this pass (cost); claims carried from them were checked against current tree state instead. A stricter second pass would re-read the trial entries.
- Fifth hoard branch `hoard-2026-10-29` still on the forge: not verified.
- 2026-10-15-fourth-hoard-merge-and-maintenance-fixture.md: mostly CI (postmerge `maintenance.lock` byte-snapshot failure in tests/test_skill_seam.py, fixed by per-invocation maintenance.auto=false / gc.auto=0). Only "fourth report accepted after PR #1438" is memory. Suggest the CI page.
- 2026-10-27-capture-pr-and-merge-commit-attribution.md and attribution friction also bear on the review department.
- 2026-10-30-rulings-and-memory-design-input.md and 2026-10-29-memory-redesign-day.md: rulings go to Commission; I link only.
- Trial launch facts (detached flags, cwd, concurrent sessions) suggested for the runtimes / concurrency pages.

## Architecture: skills, docs and hooks

### Sources examined
All 16 journal files of the `skills` line of .tmp/assign.txt (memory/journal/2026/...), plus:
memory/topics/runtime-observations.md (head), memory/topics/raid-review-and-merge.md (grep only)
memory/topics/git-worktree-session-guards.md (grep only)
AGENTS.md (catalog section), rules/state.md, skills-catalog.md, scripts/gen_skills_catalog.py, tests/test_rules_resident_budget.py, tickets/closed/{1164,1334,1335}*
/home/haduong/.claude/projects/-home-haduong--agents/memory/{feedback_dragon_skill_names,feedback_rules_are_law_memory_is_decree,project_government_memo_cooldown}.md

### Editorial changes
New page, no previous page, no second pass. Pruned (page cap; journal retains): 950/959 temp-scan candidate counts, CI/test counts, merge timings and SHAs, attribution-capture failures (belong to attribution/raid departments), review mechanics of 1298/f642df/f7fa41/readme-pr1853 (gaze/gate/notes: raid-review-and-merge; these four are cited only in Sources, content not carried: misassigned to the raid department), global-CLAUDE.md symlink retirement (historical), dangling-links prune (1128). Refreshed: STATE cap 40 (rules/state.md) not 20; stopguard tracker 1164 is now closed (status unverified); resident budget 18350 verified in test; catalog hint regex verified in generator.
Retired lines: STATE 20 lines; unmerged docs-refresh branch; /pulse; docs/ design history.

### Coherence notes
- 2026-10-19 entry says STATE cap 20; rules/state.md says 40 (rules win).
- docs-visit 2026-10-29 findings A, B, C, G are open rule-vs-rule/doc tensions (workflow.md vs doctor floor wording; claude-code.md skipped by Pi/Codex; git.md restating roar; state.md North star); exposed as open questions, not settled.
- Overlap: runtime-observations.md (adapter instruction loading, AGENTS.md profile doctrine); raid-review-and-merge.md (gaze/gate); git-worktree-session-guards.md mentions hooks/catalog by grep. Hook-denial measurement from 1228 belongs to guards page.

### Unresolved / misassigned
- Misassigned to raid-review-and-merge or attribution: raid-1298-f1-notes-evidence, raid-f642df-1326, raid-f7fa41-forge-leaks, readme-pr1853-f1-notes-gap (and partly 2026-10-21 pr1622 sweep to instruction coherence; kept here).
- Unverified: what the stop-hook ticket 1164 shipped; whether docs-visit proposals A/B/C/G were decided.
