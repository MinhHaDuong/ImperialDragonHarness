Project: ImperialDragonHarness (`/home/haduong/.agents`).

# Eighth smelt: proposed consolidation

Date: 2026-11-10. Status: **proposed, awaiting author review**; this report
counts as processing only after acceptance. Branch: `smelt-2026-11-10`.
Start: `f2a221110d938d77d3fc647d87979270b2b06f70` (origin/main). Previous
accepted state: `c5891ad66` (seventh smelt, accepted 2026-11-08, PR #2263).
Skill revision: `571da5a0cac10475f7eeb7081c61dd944ce6e8e7`
(`git log -1 --format=%H -- skills/smelt`); `references/consolidation.md` read.
Runtime: Claude Code, interface session in a fresh `/clear` context, model
claude-opus-5-5 (session system prompt). No subagent, advisor or external
provider was used; this is a single-seat pass.

## Migration and read states

Preflight (`smelt_migrate.py --reference AGENTS.md --dry-run`) and the isolated
apply both answered `0 moves, 0 active reference edits, 0 retired prompts`.
Migration finished before consolidation reading.

Read in full: the eight previous pages, the two case notes, the index, and the
42 journal entries added since the seventh smelt's acceptance (attribution
records excluded). Older journal episodes linked by the pages were not re-read;
their claims were carried from the accepted pages, and corrections were checked
against the new episodes and current files (`tests/test_rules_resident_budget.py`,
`skills/route/ceilings.json`, `Makefile`, `skills/route/references/decorrelation.md`,
`skills/raid/SKILL.md`, `tickets/closed/`). Encrypted entries: 0 found, 0 skipped.
Native store: available, 47 notes, inventoried read-only from the primary key;
10 notes read in full (new, changed or identity-mismatched).

## Ledger

Blob ids at the start ref (topics, index and case notes are the pre-smelt revisions).

- memory/journal/2026/2026-11-08-tmp-guard-arena-misfires-and-panel-purge.md blob 166a73864499f59857dcd60ac4ca063b08559ff3
- memory/journal/2026/2026-11-09-1472-deferred-label-applied-and-reverted.md blob 2c5f6e658dd966d783edda6eae4e3e3a667584fa
- memory/journal/2026/2026-11-09-1478-fanout-claims-rollout.md blob 36de4134339e81cad530fa8bc112d1f24129515f
- memory/journal/2026/2026-11-09-1485-mission-skill-hunt.md blob 88943a60b0d83155c03f0f238fd1adcd521f2954
- memory/journal/2026/2026-11-09-conception-to-design-rename-pr2310.md blob 50cc6fd912e928d3acb75bf3cd6f9a21d9f02780
- memory/journal/2026/2026-11-09-derisk-imagine-tickets-pr2333.md blob 600ce250cedd9dde693fbca5ff07063933fb4b00
- memory/journal/2026/2026-11-09-erg-claims-rollout-session.md blob 15749caa8fb0a993bf9506b001be7ebf1a690ecb
- memory/journal/2026/2026-11-09-native-store-prune-1481.md blob 36df0a9660f15cb8ee1a66cd7de159a370f66e70
- memory/journal/2026/2026-11-09-raid-1479-pin-moved-during-gate.md blob 5c9982da43f15eadb0d5eb380eccdbfd1dcaaeed
- memory/journal/2026/2026-11-09-raid-1483-paper-skill.md blob 7411650c67c45ff895272493c94b08ca9c6c6b0c
- memory/journal/2026/2026-11-09-raid-1488-single-ticket.md blob 853f057a8fe5127181330903c9199d4fdf604d39
- memory/journal/2026/2026-11-09-raid-4afdb3-post-skill-gaze-close.md blob aa7d4771e35deb9b51c852d0604ee6b3129b8b0f
- memory/journal/2026/2026-11-09-raid-632b19-wave2-projects-untrack.md blob 7fe5a083a58f875dd681629f13db87bd24b465c1
- memory/journal/2026/2026-11-09-raid-829e9e-native-store-prune.md blob 37bf78e0925ff8e8f2e76c32f3faf02c3bd7b0e2
- memory/journal/2026/2026-11-09-raid-88e70d-blind-spot-exit-check.md blob 424013251228ccb3c6d6c40b1d33a035bf86bec7
- memory/journal/2026/2026-11-09-roar-1495-gc-reclaim-third-round.md blob 27c5928b5fae2c6c26db78a62740e932185150bc
- memory/journal/2026/2026-11-09-roar-pr2351-government-cooldown-review.md blob 5585018b0ff859158ea583db0f20267d2b99bac7
- memory/journal/2026/2026-11-09-roar-pr2358-interface-context-ceiling.md blob 9d569d38817d7dd8c85d83af322db791367091e7
- memory/journal/2026/2026-11-09-roar-raid-5c2a37-landing-and-doudou-control.md blob 0ffba30e4293c52a67b56b05bd76bf7dd131f88d
- memory/journal/2026/2026-11-09-roar-raid-a8b3e4-gate-cleanup-and-publist.md blob 6d099db89ccadc51043daf854ae09a86c0f40c7a
- memory/journal/2026/2026-11-09-weekly-ticket-audit-and-false-red.md blob e4d781fb842f1f31f94660434311f41f385da5c2
- memory/journal/2026/2026-11-10-pr2442-gate-needs-author-on-conversation-ruling.md blob 706307ad55a20b9c666edf6e87dd7b48319adeae
- memory/journal/2026/2026-11-10-raid-61f50c.md blob c3d2c2f8ff379ab5504d69d4b6fdb052feb70628
- memory/journal/2026/2026-11-10-raid-91a35c.md blob 684e4c75a5375733c3953f0e0d0367545955bd5c
- memory/journal/2026/2026-11-10-raid-f7aac3-staging-recognition-and-receipts.md blob 065889307a29a7b444997f6d15bed4b8198eb92f
- memory/journal/2026/2026-11-10-raid-fc1083-doifetch-pin-v0-3-0.md blob c387dd5f0406775f0029333e2f644e2e4dd8ad02
- memory/journal/2026/2026-11-10-roar-morning-landings-1369-1417-1465-1504-1505-1506.md blob 0e44c4218ba23ca55cfc7a80adbadd1d4ee1f04c
- memory/journal/2026/2026-11-10-roar-pr2362-pr2370-false-red-ended.md blob 483ad81951dd5914406ae11d39f498b91c9e41e4
- memory/journal/2026/2026-11-10-roar-pr2365-context-length-design-note.md blob cd18ee035a207cee9e9ab190c19119b846897576
- memory/journal/2026/2026-11-10-roar-pr2367-housekeeping-notes-pins-removed.md blob 49efaabc6e6673d8d7a428a091e0f064b84a5f88
- memory/journal/2026/2026-11-10-roar-pr2378-reach-tail-raid-6ee79f.md blob 6f289b275612dbfe520a5a0fb61143c6f48f9e12
- memory/journal/2026/2026-11-10-roar-pr2391-context-length-tokens-ticket-1499.md blob 02ff3915bb69e06a616f2a9806d344d81987c6c1
- memory/journal/2026/2026-11-10-roar-pr2397-audit-names-runtimes-read.md blob af5d8e92bc72460e706669e04b7dc102a2e4cd5a
- memory/journal/2026/2026-11-10-roar-pr2402-codex-reader-raid-3429da.md blob 727eec2614c704b63d9ddadb35bfc0d4cfe5879a
- memory/journal/2026/2026-11-10-roar-pr2407-pi-reader-raid-626455.md blob 60d3107a97d96b17ef727a3c22d31569ab3b90c5
- memory/journal/2026/2026-11-10-roar-pr2418-zotero-statements-ticket-1514.md blob 96d8e81f80570c32bbb8fe456c6046a71d24db44
- memory/journal/2026/2026-11-10-roar-raid-075fa8-audit-reads-archive.md blob 84ae20ac87aa7d275ec723b84ce3b229e0f27883
- memory/journal/2026/2026-11-10-roar-raid-075fa8-one-roots-definition.md blob e5549a5a7833b183d3e9d7bb10fa44c5cae1022a
- memory/journal/2026/2026-11-10-roar-raid-13f6d8-zotero-attach-licence-and-embedded-title.md blob cac036d27f5fb503c0508fcbfe86a7a9db79127d
- memory/journal/2026/2026-11-10-roar-raid-45e130-fleet-audit-trace-runtimes.md blob 5f1bc646c7cefe310f1580ccca7cefc1c4ed9366
- memory/journal/2026/2026-11-10-roar-raid-ce1c5a-raid-land-nested-worktree.md blob d1e97730683396efeade4676bf538ebab024cc5e
- memory/journal/2026/2026-11-10-test-doctor-check-fast-workers.md blob a368980a254faf4ea69a71975b9d6fd3c176f207
- memory/MEMORY.md blob 1089c8d8beb21bda4413f3bf72adf4958b7cd108
- memory/topics/ci-and-test-suite.md blob daf4b7dfcf057e134b077cbe9a8211b42305ed71
- memory/topics/git-worktree-session-guards.md blob 83c989b789802c97572723ed4dd239ff03748cf8
- memory/topics/host-environment.md blob c37e3120b526a112f945f7f58bb4170124923cc3
- memory/topics/memory-v8-governance.md blob 4753022ee7403707ac3cea195b804001e68bb5f0
- memory/topics/raid-review-and-merge.md blob 0b90a6757606e81d3cde78f7290f5bff642a33b2
- memory/topics/runtime-observations.md blob 811e3cf56844fc23c48c1e4d248cd722f58fb91e
- memory/topics/skills-docs-and-hooks.md blob b85df5320e65359fedd0294408230b81302a6c32
- memory/topics/user-rulings.md blob 99a465cb1d631fe2fa5f36aa4ecaa6562a3cf51f
- memory/skills/merge.md blob fe25068b72615018085274fb398acb95eccef234
- memory/skills/gaze.md blob a0032d1edfa0cd47a3b8dbc4caa76581f006826a

Journal entries examined by the seventh report and unchanged since are processed and were not re-imported.

## Editorial changes

Refreshed (stale claim, current evidence):
- Resident budget 15100 → 15186 (PR 2358, `tests/test_rules_resident_budget.py:67`); the skills page carried the old cap, as roar of PR 2358 noted.
- Government memo: the cooldown ended with the author's triage closing 1369 (2026-11-10); the ruling and the skills page now carry the triage. The ruling was updated in place, not retired: its substance (accepted doctrine, a metaphor to handle with care) still stands.
- `check-fast` runs on workers since PR 2441 (`Makefile:27`); the CI page's old revisit trigger replaced by the 2026-11-10 visit's.
- `conception/` → `design/` is done (PR 2310); the open question became a dated transitional-wording note.
- Raid page: "self-only gaze accepted, panel never required" aligned with `decorrelation.md`, which plans an other-family seat for gate, merge or review machinery; the family stays a preference.
- Memory page: seventh smelt now listed as accepted; 1443 recorded as a parking close.

Added (new episodes): worktree cleanup after 1500/1512 and the author's "clean up after oneself" ruling; preflight `--removal` purges; compound force-push refusals and the bare-push form; "Merge Without Review" landings and the "Land <PR>" pattern; sibling merges voiding a gate; Blind-Spot findings; NEEDS-AUTHOR on a conversation-only ruling; the TMPDIR false red and after-merge triage; Zotero live tests needing a display; context ceilings and the all-runtime context audit; Zotero identity order and DOIfetch pin v0.3.0; native-store prune (1481) and `projects/` untracked (1480); ticket-close link breakage (1506); no Imagine skill; object-skill naming; skills census cap.

Ruling register additions, each from a journal episode: the 1472 "Undo that" ruling; the PR 2367 wording-pin case under the existing ruling; object-skill naming under the dragon-names ruling; the three Zotero identity rulings (new section "On tools and evidence"). Integrated rulings (interface ceilings in `rules/guards.md` and route; no Imagine skill in raid; cleanup prose in hunt/molt) were not added to the register; the topics cite them.

Merged or moved off the page to fit the cap, each kept in its linked episode and listed on the page's Sources: the raid page's seat-parsing, family-row, forged-header, delta-gaze, carry-over, forge-lag and auto-merge-delay details; the host page's backfill counts, compression decision, suite timing and `gaze_seat.py:482`; the runtime page's stale `routes.json:100`; the skills page's sweep lens rates, hook dry run, superseded 18000 cap, prose duties and docs-visit slug. No condition or exception was dropped (second pass below).

No retirement record was appended: no ruling left the register.

## Sizes (measured)

`memory_sizes.py memory/topics --before HEAD` (start ref):

| Page | Before | After | Net |
|---|---:|---:|---:|
| ci-and-test-suite.md | 3535 | 3641 | +106 |
| git-worktree-session-guards.md | 3031 | 4040 | +1009 |
| host-environment.md | 3774 | 3638 | -136 |
| memory-v8-governance.md | 2219 | 3028 | +809 |
| raid-review-and-merge.md | 3398 | 3917 | +519 |
| runtime-observations.md | 3768 | 3826 | +58 |
| skills-docs-and-hooks.md | 3938 | 3853 | -85 |
| user-rulings.md (register, exempt) | 4725 | 6387 | +1662 |
| total | | | +3942 |

Growth reasons: two days held 42 new episodes. The git page took the 1500/1512 cleanup contract, the preflight purge hazard and the classifier push forms. The memory page took the 1481 prune, the 1480 untracking and the 1506 link hazard. The raid page took the landing-permission pattern, sibling-merge voids and NEEDS-AUTHOR. The CI page took the TMPDIR false red. The register took five new rulings. Every department page is under 4096; the register is over its budget and reported, not cut.

## Unresolved questions and contradictions

No contradiction exposed between indexed pages, or between a page and a harness rule; no ticket filed. Checked: interface-session ceilings against the 230K guard (consistent: `rules/guards.md` now delegates to route); gaze family policy against `decorrelation.md` (aligned); worktree cleanup against the native note on raid session trees (consistent: roar deletes).

Noted, not memory contradictions (skill text, below the floor, listed on the skills page as hazards): route SKILL.md lines 67/115 and `routes-recommendations-claude-code.md:24` still call 230K a hard floor; `rules/guards.md` does not define "interface session".

Open for the author: whether an attended raid is an interface session (2365); the history-scrub question for `projects/` (1480); the regrowth review of pruned native stores by 2026-11-23 (1481).

## Native-note triage

Store `/home/haduong/.claude/projects/-home-haduong--agents/memory`, 47 notes. 37 carry the same sha as the seventh report's table and are listed as unchanged without a new proposal. Two of them have gone stale since: `project_government_memo_cooldown` (1369 closed) and `project_main_guard_enforce` (watch ended 2026-11-03); the author may wish to revisit them.

| File | Substance | Proposed disposition |
|---|---|---|
| feedback_advisory_question_no_unasked_intervention.md (`4bb0185c`, new) | an advisory question gets an answer and at most an offer; starting a cross-project filing was "goldplating" | **nominate as a rule candidate for Brood**: it reads as a working rule about the scope of an answer |
| feedback_arm_timers_from_session_worktree.md (`87c44433`, new) | timers and landing calls armed in a PR worktree die when `raid_land --cleanup` removes it | **promote to repo memory**, git-worktree-session-guards (an experience) |
| feedback_classifier_blocks_rule_mandated_git.md (`e8df0f3d`, changed from `ff64c363`) | dated classifier refusals and passes; park and hand "Land <PR>" | **nominate as a rule candidate for Brood**: the park-and-"Land" practice reads as a working rule, and the skill's delegated-retry recovery was itself refused; the observations are now on the raid and git pages |
| feedback_no_wording_pin_tests.md (`38c8217a`, new) | source-string assertions are removed before landing | **delete**: in force in the register's "REMOVE WORDING PINS" ruling with the PR 2367 case |
| feedback_raid_session_worktree_left_to_roar.md (`22c7d06c`, new) | "Raid can leave, it is indeed better and roar deletes." | **promote to repo memory**, user-rulings (an author ruling not in the journal) |
| feedback_ticket_close_breaks_memory_links.md (`f4f32bc3`, new) | archiving moves the ticket; grep memory/ and design/ first | **delete**: in force on the memory and raid pages and the merge case note |
| feedback_zotero_identity_rulings.md (`d4f5612c`, new) | several DOIs/ISBNs per work is the norm; weak evidence used with judgement | **delete**: in the register, § On tools and evidence |
| project_hunt_tmpdir_breaks_git_tests.md (`ae2bb16d`, new) | worktree TMPDIR breaks five tests; leaked into the after-merge runner | **delete**: on the CI page; PR 2362 landed |
| reference_zotero_live_tests_need_display.md (`1a1412cb`, new) | live Zotero tests skip in gates; exact `DISPLAY=:0` command | **promote to repo memory**, ci-and-test-suite (the exact command line; the hazard is already there) |
| reference_padme_home_snapshots.md (`d8b5a84b`; seventh table recorded `d5b5a84b`, identity then withheld) | btrfs/snapper state on 2026-10-30 | **delete**: in force on the host page; the note itself says it belongs in padme's host store. The one-digit sha difference is probably a transcription error in the seventh table; not established |

Native notes used as sources in topics: none; every new claim cites a journal episode.

## Case notes

- merge.md: added "Merge Without Review" landings (the case most likely to change a landing decision), the 1506 close link break, and the PR 2402 sibling-merge recovery. Dropped the PR 1725 stale-record case (the skill's record-retry-once recipe covers it), the PR 1924 hand close (`raid_land.py` is the path now), and the PR 2033/2035 push case (its ruling is in the register). Kept PR 2223.
- gaze.md: added the PR 2399 seat that failed to start, and the PR 2423 seat that cited the wrong tree. Dropped PR 2257 (illustrative; its note says no independent catch was observed). Kept PRs 2216 and 2054.
- raid.md (new; raid has recurring observed episodes): Blind-Spot catches (88e70d, 632b19), skipped `writer:` lines (2292, 2436), a coder skipping its worktree (1511), a shared annotation commit splitting the wave (2423/2424).

## Second pass

Over the same revision set: nothing imported as new beyond the 42 ledgered entries. Each correction was re-checked against its source: 15186 at `tests/test_rules_resident_budget.py:67`; `skills/route/ceilings.json` holds 230K/450K/550K; `Makefile:27` routes check-fast through `pytest_workers.py`; 1369, 1415, 1417, 1477, 1480, 1481, 1499, 1500, 1506 sit in `tickets/closed/`; `decorrelation.md:21` plans an other-family seat for gate, merge or review machinery. Each previous page was compared with its rebuild. On the first draft of the git, raid, CI, host and runtime pages, these caveats were missing and were restored: GC liveness dissent, `-D` authority, the ref-name push exit-0 hazard, private skill links, installed-primary edits, the forked gaze base repo, the main guard, stranded/split branches, the forced notes rewind, foreign-cwd PR resolution, unexplained full-suite failures, the `close-and-clean.sh:67` consider, the run_pool race, "writes only as reports", Zotero 9.x, batch `.txt`, the dotfile end marker, strata, the Codex usage limit, `runtime.py wake`, Pi DEGRADED, `pi-haiku`, the FOREIGN file. The remaining off-page items are historical detail listed on each page's Sources with their episode. No retirement record exists to duplicate.
