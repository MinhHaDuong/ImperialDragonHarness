# Third dream: the 2026-10-08 to 2026-10-13 journal

Date: 2026-10-13. Project: this harness repository (v8 memory), explicitly
assigned by the author for this run.
Prompt revision: v8-r1 (2026-10-02), `memory/DREAM.md`, run per the installed
dream skill (`~/.claude/skills/dream/SKILL.md`).
Runtime: Claude Code 2.1.296, model Opus 5.5 (`claude-opus-5-5`), effort high,
in the isolated worktree `explore-dream-3` on branch
`dream/2026-10-13-third-dream`, base `bc917ab2`. One read-only subagent,
Sonnet (pinned: mechanical counting and extraction, no independence needed),
aggregated the review-attribution and review-evidence records. Its counts for
`status: ran` (140) and `adopted:` (102 yes / 38 no) were reproduced by the
main session with the same `grep`.

## Pass 1

### Coverage decision

The accepted prior report is the [second dream](2026-10-07-second-dream.md).
Its ledger lists every journal blob it processed. All of them are unchanged at
`bc917ab2` (compared blob by blob) and were not re-imported. The 92 journal
files absent from that ledger are new and were all examined: 34 narrative
entries, 36 review-attribution records, and the 22 files of the PR #1374
review-evidence bundle. The topics at HEAD carried exactly the blobs that the
second dream's pass 2 recorded, so no one had edited them between dreams.
`memory/MEMORY.md` had changed: roar runs had added a "Recent experiences"
block.

### Sources examined (ledger)

Authority, index and prompt files, read only, at `bc917ab2`:

- AGENTS.md blob cf2133ba6ff09021657fefef0a328f6658f965d2
- memory/DREAM.md blob 6087a0b3f641bdc4cbeac595e87d174eb11bcbf5
- memory/MEMORY.md blob e4a34b850c6cb59431b78d4128a26e73a1edb784
- memory/dreams/2026-10-07-second-dream.md blob e50de830a1d8100cad1959baeeaaac4f13566725
- rules/claude-code.md blob 901e4f2b3ae7f85b302cc151078a12e9ec21085e
- rules/coding-python.md blob 221e43c6f50d187b2643262ba9e12b1cdc69a23f
- rules/git.md blob 976a429bd6e7937e71f9e475a48f1dc69fc84027
- rules/guards.md blob 789d82599f6ee2e82d59302e70c1f7d0ff6e46c4
- rules/workflow.md blob c4a05a6af08275747c4f46727d64feb5bf431a71
- skills/merge/SKILL.md blob 5011a7777098a8848cfad3af8ad3ebca5982425a
- tests/test_branch_cleanup_recipes.py blob d26c100709d38aa821b959d4dd8c3122ce22157a
- tests/test_memory_v8_pilot.py blob fb10959d199f5004772cc9f7a759f3260dfacdd0
- tests/test_resident_census.py blob e577eb10bdd5ceed22fcaf34f587debc61b0b8a8

Topics before this pass (blobs identical to the second dream's pass 2):

- memory/topics/branch-cleanup-incidents.md blob afeb9493f271fb9e1327b4fbebabef46cbd158dd
- memory/topics/ci-and-test-suite.md blob 72d1a399e4e04a4d3ee1523c9e167ff6e88016a6
- memory/topics/git-worktree-session-guards.md blob b4428fa1c2e040f03bd5dbc9107992df87bec1c1
- memory/topics/memory-v8-acceptance-trial.md blob eeaae2f37e86b5a5222565e2d65b437090a8709b
- memory/topics/memory-v8-governance.md blob 2bd91fca7ac7fc782125a718bea671d916e8be77
- memory/topics/raid-review-and-merge.md blob 3fb283c481e94c7c3eb099db1f1b69fa58c25eb2
- memory/topics/runtime-observations.md blob c167eb5f522ecc8e572f5877b680ca8babe78af1
- memory/topics/shared-checkout-concurrency.md blob 255f972a76f455133a0fdec9244766245032a992
- memory/topics/subagent-model-effort-levers.md blob beb3a1960e146ba6df711820729fc9a986e78c5f
- memory/topics/zotero-library.md blob 78fba595c664c0f980eac6e7f254631fea068c55

Native notes (Claude Code auto-memory of this project, attributed, text in the
annex). Blob ids are from `git hash-object`:

- ~/.claude/projects/-home-haduong--agents/memory/feedback_babysit_takeoffs.md blob 7e3119fe08d505636bc522af7abc9607ba412c7a (used)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_delta_format.md blob 4332fcd417647d8b36d31b0ae8ba9050e5021ead (examined, not consolidated: a display preference that `skills/dashboard/SKILL.md` already encodes)
- ~/.claude/projects/-home-haduong--agents/memory/feedback_no_blocking_waits.md blob c6ebb58feb461f8d0eaae1c7c8dde871a5073133 (processed by the second dream, unchanged)

Host state read to refresh claims: `~/.config/rtk/config.toml` on doudou
(line 48, `exclude_commands`), `adapters/pi/agents/code-reviewer.md` line 5,
`skills/merge/erg-pr-merge` lines 147-153, and `tickets/` statuses for 1045,
1074, 1076, 1077, 1079, 1081-1083, 1087-1090.

Encrypted entries: no `.age` file exists under `memory/`, and
`~/.config/keys/memory/` is absent on doudou. Skipped: 0. Unavailable sources:
none needed.

New journal files (92):

- memory/journal/2026/2026-10-08-haiku55-arm-n-integration.md blob f40aa455faf5984da3970e781d7b89a10d558433
- memory/journal/2026/2026-10-08-haiku-review-delay.md blob f1deee1259392caf54d49c186041c5bf97edb028
- memory/journal/2026/2026-10-08-llm-routing-plan-and-wave-a1.md blob 979200c75175a322c4ea99b02f828b8352c163f5
- memory/journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md blob 63950b7af16ca2629376f92cca283b74e7082fc0
- memory/journal/2026/2026-10-08-review-attribution-pr1253.md blob 2345c6c6108dad7d50c79c910e957d8a419c57fa
- memory/journal/2026/2026-10-08-review-attribution-pr1260.md blob f98c400d14e00eac045ab762b208cda2f86e3593
- memory/journal/2026/2026-10-08-review-attribution-pr1272.md blob 4faf1978b45daf9eb6f6a63982f235328eb351bb
- memory/journal/2026/2026-10-08-tournament-publication-wrapup.md blob 5b7773ce476cfd4f0423cfa6e4d10bc1b38be557
- memory/journal/2026/2026-10-09-1071-launch-line-and-adherence-rerun.md blob 31d85b8918caeaf590196a4f7ae30e4b53af6b60
- memory/journal/2026/2026-10-09-close-1074-guard-refusals.md blob 6a920661365ba6c48a5420fa06a52c70ae587108
- memory/journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md blob 8be3e00c741a2196dae694ead143b9d77de7e601
- memory/journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md blob c0552bee9f4b8cbc60931f2e4e2f56bc538c5c13
- memory/journal/2026/2026-10-09-pr1309-gaze-isolation-blocked.md blob 9d469c527f2657be04f959021ae65249c3435dd0
- memory/journal/2026/2026-10-09-pr1328-short-close-claims.md blob 98d99ef8b84eb51705f299a03ecf319cc4baa4e9
- memory/journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md blob ef6b5341e7e5f7b26e44a7a138973c9c7ab43a51
- memory/journal/2026/2026-10-09-raid-1075-roar-rule-conflict.md blob 04a7af1dd0fdfeca26e8d800cdc9d6eeeeda2727
- memory/journal/2026/2026-10-09-review-attribution-pr1269.md blob 2d856a8f62ccc82b8fe2cd1be89829f12ee983c5
- memory/journal/2026/2026-10-09-review-attribution-pr1278.md blob 7d9eb87d3e8a564165b2f97c3a8ff908abd16112
- memory/journal/2026/2026-10-09-review-attribution-pr1288.md blob d8669b1f459ce0deb6c78c4945b7254697ed6834
- memory/journal/2026/2026-10-09-review-attribution-pr1289.md blob 95654ebd477a1e408b6f321f9da1a1e9864629c4
- memory/journal/2026/2026-10-09-review-attribution-pr1290.md blob d32beb66ff59a6e90cda64d76439af844d61b8fb
- memory/journal/2026/2026-10-09-review-attribution-pr1291.md blob 013ea6ce0b737c853c21a6bbfa0759dc36516a2b
- memory/journal/2026/2026-10-09-review-attribution-pr1297.md blob 53bdb755d1b7761038c4b1b406a2960bd805fd21
- memory/journal/2026/2026-10-09-review-attribution-pr1298.md blob a04567b9c6ad34e6dfd63d558a175dc39d6192e7
- memory/journal/2026/2026-10-09-review-attribution-pr1299.md blob 6f7375ffaa99b59812c4b3aa047f4f81ec84d0a7
- memory/journal/2026/2026-10-09-review-attribution-pr1300.md blob 35519aafb52579b5203c8c813f3b880b488c65f8
- memory/journal/2026/2026-10-09-review-attribution-pr1301.md blob 055be6e90cf7bc6dc2df601993ed54f0d7a6be8f
- memory/journal/2026/2026-10-09-review-attribution-pr1302.md blob edefa1e72e9fa3bd32d82298006022d68abec372
- memory/journal/2026/2026-10-09-review-attribution-pr1303.md blob c270fbbe60afecdca361c6c64da1bac46a8ef597
- memory/journal/2026/2026-10-09-review-attribution-pr1305.md blob 310fc26dd074e40147c79177089401644bba39a6
- memory/journal/2026/2026-10-09-review-attribution-pr1307.md blob 012235babc563429b95081197f0c5eb950627264
- memory/journal/2026/2026-10-09-review-attribution-pr1313.md blob 70ca7f9e1d21cd1f2aaacad48fefbe2cb67774c9
- memory/journal/2026/2026-10-09-review-attribution-pr1319.md blob d9385baeeecbce9037a7c54b2726b363822450f5
- memory/journal/2026/2026-10-09-review-attribution-pr1326.md blob 4ce9b71fd8c197241e9d488c4f2c9665095cb959
- memory/journal/2026/2026-10-09-review-attribution-pr1328.md blob d8b05b8089638260397ee8359a19c13ee6385985
- memory/journal/2026/2026-10-09-review-attribution-pr1329.md blob 2c8ca2e43e9397722a63221145147ca8ce26fef3
- memory/journal/2026/2026-10-09-review-attribution-pr1331.md blob ecc2e2ed84f6766272feb90e50051203a2f4fe24
- memory/journal/2026/2026-10-09-review-attribution-pr1334.md blob d920d1c38dd6a7ed38a7dfef81f1e1e4782b2fc3
- memory/journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md blob e05588d0ac6b00e5ffa3262075d2332b1947a39b
- memory/journal/2026/2026-10-09-routing-review-round-two.md blob 994ac71e36912f608f390c12d8857d5b535462ef
- memory/journal/2026/2026-10-09-rtk-git-exclusion.md blob 60de63e9e17e0521694b89a66cebafc9f515b9fb
- memory/journal/2026/2026-10-09-tournament-report-padme-env-float-drift.md blob 37976471b50ffcc43dbaa6bed2d936137b84e558
- memory/journal/2026/2026-10-09-worktree-isolation-census.md blob f38dcd74b9bdd92d0db259283a4a5c1ba94f6e75
- memory/journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md blob cc588a3bd38ed1279cb4b9ee7fd498ac30257fb2
- memory/journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md blob 2f36d32d2f1a05ce70104de210f77e09ce1e196c
- memory/journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md blob d9e91fb90a94751a76c10120b27b6c78353a4e70
- memory/journal/2026/2026-10-10-review-attribution-pr1348.md blob 99a5af34ea3adc828f6edee3586cc38c29c8fbc7
- memory/journal/2026/2026-10-10-ticket-line-guard-deleted.md blob aa135ff66b647192eefe855791b4f9eb048fca81
- memory/journal/2026/2026-10-11-review-attribution-pr1354.md blob 8408b3b5c27a9b928a9bfb55e69529b423ce8732
- memory/journal/2026/2026-10-11-roar-clear-verdict-survey.md blob 2127eb530aa1b20804c4af5b61215aeb13118148
- memory/journal/2026/2026-10-12-cross-repo-session-gaze-forks.md blob 383a346455a557152f2baeac4ab6538a666b5f65
- memory/journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md blob d4b603552442b47a8b03cacdb96695b26e972bd3
- memory/journal/2026/2026-10-12-pr1368-review-evidence.md blob d4478f34d37e4a0f6cfd1c9fe08dad9a69c3dbc8
- memory/journal/2026/2026-10-12-pr1372-review-evidence.md blob 868cca157179460454dbf2d26f29cec126e9f8b9
- memory/journal/2026/2026-10-12-pr1373-review-evidence.md blob 240b7d7593346ee27cce5f30ab60e8c93eeaf5be
- memory/journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md blob 8f6d737204fa53c02dff375d223ab7c9e4eb7f06
- memory/journal/2026/2026-10-12-review-attribution-pr1360.md blob 6e776dc6e51c5e4a76ba76e03d289fee6cdbf349
- memory/journal/2026/2026-10-12-review-attribution-pr1361.md blob 432fd80badc5c4ead25c68d88e08f5200a4f39aa
- memory/journal/2026/2026-10-12-review-attribution-pr1364.md blob 5d74591e4a68e78df3aa90bb7e70f8c2a7a5eeac
- memory/journal/2026/2026-10-12-review-attribution-pr1366.md blob b83dac6d44af7eac80cc54a4dcd213edb8e8eb4d
- memory/journal/2026/2026-10-12-review-attribution-pr1368.md blob 409cf79ff1d39a776918f09d09aa760737d1d652
- memory/journal/2026/2026-10-12-review-attribution-pr1372.md blob d557a21ca11bef463cae25be82974f869382a365
- memory/journal/2026/2026-10-12-review-attribution-pr1373.md blob 054d6dbe2f275e1b1e6d8a1e5addc97338d48230
- memory/journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md blob b8ec6c3ad79a75185a0f6efa13e8e362a31f9de3
- memory/journal/2026/2026-10-12-t1053-arena-git-and-scoped-vram-wait.md blob cd51156887754a38666a3b4b530e8789987c6e38
- memory/journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md blob 2a56ffa7c22084233e0023ed9f8c577afbe3e653
- memory/journal/2026/2026-10-13-pr1374-attribution-pending.md blob af344fd9e44b6e5995b1531e65f5c54fa14880fd
- memory/journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md blob d88ff8407aaa1df3d14577b7d518826624bd1c09
- memory/journal/2026/2026-10-13-pr1374-review-evidence/gate-and-author-comments.md blob cbad2331346e880b256d8310447124e86539f7ff
- memory/journal/2026/2026-10-13-pr1374-review-evidence/identity.md blob fc73c829279f409085b89922b157ed5ec03b27a4
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round1-forge.md blob 571a9811c24cb8ad43e88926c5114a7e8c6187b5
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round2-forge.md blob 56ba0654f05ae9754877bd2e63338304261ad5f8
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round3-forge.md blob 50b8c1833cd59128d1afe4d510cd9cbc8da84c1f
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round4-forge.md blob d0fed53e54332bb6fcec2f649430064d9734f3d5
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round5-forge.md blob 194b26e363c06e92eba604a353f464a942a5a958
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round6-consistency.md blob 27e137de98f02a36128e3c5cf42a9ae8db5c16fe
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round6-correctness.md blob a1cdcb999a37ad19a413e707819e4f1b130c7972
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round6-doc-propagation.md blob 842ad756bff2fbeb999f56dd86ce2f8e02a77c0c
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round6-forge.md blob 7359dd1d998fae6d8d2f28844c430b2a1e1a3107
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round6-red-team.md blob 750c5a4cebccd52d5f75aae4eaa45e01d2922cf8
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round6-scope.md blob 714344bcccd9974c60dd18839c3f5bea78a0b962
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round7-consistency.md blob 35aa6957ea2d228fd3fd6d88a865d950047c1c8e
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round7-correctness.md blob 75be01aa03da78b97d6a432bf3cdb3e88eefccb3
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round7-forge.md blob 8c44be6c48c519a28b195669d5f9d6c0a296fb88
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round7-red-team.md blob b66c7687f60c509b8901ac24658d00e1775fb11d
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round7-regression.md blob 3afcd7e1853d5ea86c74fd17480b3040204ff166
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round8-forge.md blob 72765686592baca40229bb3cccbae78c9ef06b21
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round8-red-team.md blob a6a8096e47b0ffeefc982c1483c602194115cc76
- memory/journal/2026/2026-10-13-pr1374-review-evidence/round8-regression.md blob bfd8b0141781b25b9f107d1098a018959d25b741
- memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md blob ea14e5a4e2cad2416b8555226dadca3051cad2e6
- memory/journal/2026/2026-10-13-review-attribution-pr1377.md blob 4824a5d7a379051b4d75683ee4ad915b1c86f9a2
- memory/journal/2026/2026-10-13-review-attribution-pr1378.md blob 67da11b0d840e0a357ca7594377bd21cc6eb78c9

### Editorial changes

New topic (merging): `topics/host-environment.md`, "Hosts, shells and
credentials". It gathers the 2026-09-29 relocation facts, which the 2026-10-09
import entry explicitly left for the next dream to fold in (the rest of that
import went to the concurrency and raid topics), together with the
2026-10-09 uv and snapshot episode, the 2026-10-10 permissions rewrite and two
credential episodes.

Refreshing:

- `git-worktree-session-guards`: since 2026-10-09 the rtk rewrite no longer
  touches git on doudou or padme (`exclude_commands`; re-read on doudou today).
  The note's first guard is now marked host-conditional. The isolation-guard
  census (9,537 refusals, three clear true catches), the refused command shapes
  and the 1074/1076/1077 decisions were added.
- `branch-cleanup-incidents`: corrected. The scope claimed `rules/git.md`
  carried cleanup loops whose `-D` use the topic explained. The current rule
  (§ Branch cleanup) inlines no loop, keeps `-d` refusal and never forces. The
  loop-era description is relabelled as history, and the PR #1374 episode
  (update-ref deletion, delete-then-restore defects, author scope revision) was
  added. Authority: `rules/git.md` blob 976a429b and
  `tests/test_branch_cleanup_recipes.py`. The source note is unchanged.
- `runtime-observations`, retitled "Runtimes, models and routing": the pi
  default `qwen3.8-27b` is pruned as current and marked superseded by the
  2026-10-12 Flash-Next switch (verified in the pi adapter file). Added: pi
  auth and link observations, Codex 0.161.0, Strata quirks, the Haiku arm N,
  cycle 3, and the routing rollout (tracker 1052) with its launch-line counts.
  The routing material was merged here rather than given its own topic, to
  stay within the index budget.
- `subagent-model-effort-levers`: the A0 measurement (definition tier token
  gives 404, per-launch pin overrides it, unpinned launch inherits) and the
  Codex `spawn_agent` observations. Both agree with `rules/claude-code.md`.
- `shared-checkout-concurrency`: the 2026-10-08 to 2026-10-13 episodes
  (Codex and Claude ownership split, the shared arena checkout, held
  cross-session messages, branch occupancy, the overlay-symlink census
  divergence, the cross-repo base).
- `ci-and-test-suite`: flakes with causes not established, the 1088 local-CI
  skip, the author's "2 hours" question and "I want SCIENCE" request (recorded
  as an author request, not a commissioned task), forge waits and 1082.
- `raid-review-and-merge`: catches, degraded panels (the isolation guard is
  the most frequent degrader), overrides and deviations side by side
  (#1253 gate override, the invented waiver, the 1075 rule conflict, #1372,
  #1374, #1348, PRs without gaze), merge mechanics, and an aggregate of the
  36 new attribution records (derived counts: 154 reviewer lines; 140 ran, 8
  failed, 6 skipped; 102 adopted, 38 not).
- `memory-v8-governance`: the legacy-notes import, the index budget refusal,
  the 1083 roar reorder and the attribution backfill unresolved counts
  (34, 65, 69).

Pruning (index):

- The "Recent experiences" links to the 2026-10-07 to 2026-10-09 entries were
  removed. Each remains linked from a topic: PR 1245 from ci and raid, Mistral
  from runtimes, the routing entries from runtimes and raid, the Haiku review
  from raid and shared-checkout.
- Two current entries replace them.
- The first dream's line was dropped, as that dream itself suggested once a
  successor was accepted. It stays linked from the governance topic.
- Topic hooks were shortened to fit the 2100-character hook budget.

No journal entry was rewritten, moved or deleted. No rule, AGENTS.md, skill,
runbook, test or root note was edited.

### Coherence

All eleven indexed topics were compared with each other and with AGENTS.md,
`rules/git.md`, `rules/workflow.md`, `rules/claude-code.md`, `rules/guards.md`,
`rules/coding-python.md` and `skills/merge/SKILL.md`.

- Corrected: the branch-cleanup topic presented retired loop practice as the
  current content of `rules/git.md` (see above).
- `rules/git.md` (§ Reading state) still describes rtk rewriting git and
  `/usr/bin/git` as the escape hatch. The guards topic records that git is
  excluded on two hosts. The rule tells the reader to ask `rtk hook check`,
  so a host-specific exclusion does not contradict it. No change.
- The host topic's 2026-10-12 credential display is an occurrence of what
  `rules/guards.md` forbids. It is recorded as an episode, with the key not
  reproduced, and nothing in memory presents it as acceptable.
- The uv measurements agree with `rules/coding-python.md`, and the
  decorrelation feedback of 2026-10-08 agrees with `rules/workflow.md`
  § Delegation ("Reviewers scale to the risk"). Memory restates neither.
- Statements that read like rules are kept as author statements or episodes:
  "guards on guards; doctrine is to remove" (raid 1072), "Babysit your
  takeoffs", "I want SCIENCE". None is presented as a rule.
- The raid topic notes that the `rules/git.md` wording behind the raid-1075
  conflict no longer exists in the current rule text (grep found neither
  "auto-run" nor "raid Phase 8" in `rules/`).
- After the edits no contradiction remains between indexed topics. The
  runtime topic's pi default and the subagent topic agree with the adapter
  file and the rule respectively.

## Unresolved questions

1. In-place appends continue: #1272's attribution record has an appended
   retro section, and the raid-1091/1092 entry announced and carried an
   appended "outcomes" section. The second dream's question to the author
   (whether dated appended sections satisfy append-only) is still open.
2. PR #1377: ticket 1079 should resolve a lone `Ticket: NNNN`, yet the
   2026-10-13 entry says its short Ticket field "was not recognised". The
   entry does not quote the body, so whether this is a helper defect or a
   format outside 1079's grammar is not established.
3. PR #1374's evidence names the producer as Anthropic in rounds 3-5 and as
   OpenAI `gpt-6.1-sol` in rounds 6-8, and its writer is runtime-masked. No
   source reconciles the two.
4. Attribution records for #1309, #1337, #1338 and #1352 were never written
   (reviewer ids not exposed), and #1374 remains a pending candidate. As in
   the second dream, whether coverage should mark such merges is a capture
   question.
5. The root notes `reference_git_in_a_worktree_session.md` and
   `reference_branch_cleanup_incidents.md` now contain stale current-tense
   claims (rtk on git; loop recipes). They are pilot sources pinned by
   `tests/test_memory_v8_pilot.py` and outside dream's write scope; the
   topics flag the staleness. `pending-capture-pr1211.md.txt` remains as
   before.
6. Causes not established: the CI flakes on #1263 and #1270, #1324's
   auto-merge stall, the earlier #1245 stuck check, and the local-main repair
   of 2026-10-02 (still no recorded outcome).
7. The `.age` path is still unexercised on real material.

## Pass 2

Same checkout, immediately after pass 1, over the same revision set. The
journal, authority and native blobs are identical to the pass-1 ledger. This
pass re-read the files that pass 1 wrote, at these revisions:

- memory/MEMORY.md blob fa1d347fd055d098de85091ca060653a2ac2a6a5
- memory/topics/branch-cleanup-incidents.md blob 7af5274534bad7bebc88096d15ebe0f1e89bd457
- memory/topics/ci-and-test-suite.md blob 40911837edea6df080d790c0113e08ddd921b95a
- memory/topics/git-worktree-session-guards.md blob ab4194b0c10436981e7be9123ca219b705ef7924
- memory/topics/host-environment.md blob da738af44b63841ee7e3c0795569ce695a15f20a (new)
- memory/topics/memory-v8-acceptance-trial.md blob eeaae2f37e86b5a5222565e2d65b437090a8709b (unchanged)
- memory/topics/memory-v8-governance.md blob 31ca838683067e6e050178c69cbe4e20c8e882bd
- memory/topics/raid-review-and-merge.md blob f256ff75968923cfdfe6bcfa566973e4c9a11095
- memory/topics/runtime-observations.md blob 22f0276b4202fe790ee83a7e0469448b4ade658b
- memory/topics/shared-checkout-concurrency.md blob fe91c8672bbff4b7878d0af25b2cd998cfc64cca
- memory/topics/subagent-model-effort-levers.md blob 62b32c63f303651817b6ef40fc87f8be4b3f98b4
- memory/topics/zotero-library.md blob 78fba595c664c0f980eac6e7f254631fea068c55 (unchanged; no new Zotero source)

Imported as new: none.

Corrections re-examined against their sources:

- Suite count: pass 1 first wrote that `make check` counts "on main" rose to
  1606. The 2026-10-13 entry measures 1606 on the tested union commit of 1091
  and 1092 (`7e1f77b1`, then the synthetic `876056f5`), not on main, and 1514
  was a local run in wave A1. The topic now says so.
- Coverage of the 2026-09-29 import: pass 1 said its content was consolidated
  under hosts only. On re-reading, three of its nine facts (gaze escalating
  from background agents, adjacent `Blocked-by` lines, literal paths for
  delegates) were in no topic. They were added to the raid topic, the
  hermetic-test fact had gone to concurrency, and the governance pointer now
  names all three topics.
- Attribution aggregate: the main session re-counted 140 `status: ran` and
  102/38 `adopted:` with the subagent's `grep`, and both matched. The failed
  (8) and skipped (6) counts rest on the subagent's commands, shown in its
  output, and were not re-run separately.
- Branch-cleanup correction: `rules/git.md` § Branch cleanup (blob 976a429b)
  states the explicit-target, `-d`-retaining practice, and
  `tests/test_branch_cleanup_recipes.py` asserts no inline loop and no
  `git branch -D` in the helper. The correction stands.
- pi default refresh: `adapters/pi/agents/code-reviewer.md:5` names
  `padme/qwen3.8-flash-next-iq3_s`. It stands.
- rtk refresh: `~/.config/rtk/config.toml:48` on doudou carries the git
  exclusion. Padme was not re-read today, so the topic attributes the padme
  state to the 2026-10-09 entry.
- Links: every relative link in the index, the topics and this report resolves
  (checked by script). The index is 37 lines and 1675 characters, under the
  100-line limit and the 2100-character hook budget. The memory tests passed:
  20 across `test_memory_v8_pilot.py`, `test_resident_census.py` and
  `test_on_start_memory_injection.py`, run through the project's uv
  environment because the system Python lacks PyYAML.

## Annex: native note used

Source: Claude Code native auto-memory of the harness project,
`feedback_babysit_takeoffs.md`, blob 7e3119fe, modified
2026-10-12T08:01:05Z. Body text, as written:

> After launching a long run (arena driver, batch, pipeline), stay on it until the first real unit of work has actually completed and recorded, then announce. Do not announce "running" from process lists or a started log line.
>
> **Why:** cycle 3 of the model tournament (ticket 1048, 2026-10-12) was announced as flying twice while the local lane was failing: Strata listened on the wrong port, then the launch script refused the arm's own server; four attempts voided. The author noticed from the silence of the fans and said "Babysit your takeoffs".
>
> **How to apply:** after a launch, check the first leg's record (verdict, duration, tokens, plausibility against a known reference) before the announcement; check GPU utilization/power when local compute is expected. Keep checking at short intervals during the first legs, not only via a long background watch. Related: [[no-blocking-waits]] still holds — poll with bounded checks, not --watch loops.
