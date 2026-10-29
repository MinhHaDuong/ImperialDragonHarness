# Second dream — operational themes from the 2026-10-02 to 2026-10-07 journal

Date: 2026-10-07. Project: this harness repository (v8 memory).
Prompt revision: v8-r1 (2026-10-02), `memory/DREAM.md`, run per the installed
dream skill (`~/.claude/skills/dream/SKILL.md`).
Runtime: Claude Code, model Opus (claude-opus-5-5), subagent writing pass in
the isolated worktree `explore-dream-20261007`, branch `dream/2026-10-07`.

## Pass 1

### Coverage decision

The accepted prior report is the [first dream](2026-10-02-pilot-first-dream.md).
The three 0918 trial reports (pass 1, pass 2, pass 3-interrupted) were merged
as scenario evidence of the acceptance trial (PR #1142; results document
cells S6.1, S7.1, S10.1). This pass treats them as **trial artifacts, not
accepted processing**: pass 3 states that its sources are unprocessed, and
passes 1-2 ran inside a protocol whose verdict was "No rollout". Every 0918
journal entry was therefore re-examined against the acceptance-trial topic
those passes produced. The topic's claims were confirmed against their
entries, and one refresh was added (below). The six journal entries examined
by the first dream carry unchanged blobs and were not re-imported.

### Sources examined (ledger)

Every path below was read at HEAD `ea4136d8`; blob ids come from
`git ls-tree -r HEAD`. The six entries processed by the first dream appear at
the blob ids it recorded. Authority files (AGENTS.md, rules/*,
skills/merge/SKILL.md) were read only. The three tests were read to learn the
index constraints.

- AGENTS.md blob ab7d38c736e14675ba204b55d09193fc1fb0938b
- memory/DREAM.md blob 6087a0b3f641bdc4cbeac595e87d174eb11bcbf5
- memory/MEMORY.md blob 70fcf8bb6289f0614b6571472fc11d80ad897fd8
- memory/dreams/2026-10-02-0918-trial-dream-pass1.md blob cb64a1e271c4e4ff3875d06a97939ff667521c7c
- memory/dreams/2026-10-02-0918-trial-dream-pass2.md blob 5654b1a4375b4bae165029d02192229d412abb73
- memory/dreams/2026-10-02-0918-trial-dream-pass3-interrupted.md blob 9e282de029507020e10b2d9f97c902a7e2824cde
- memory/dreams/2026-10-02-pilot-first-dream.md blob 7a7f486f78535ff8ea048ca3b8980c8f8ed83bbc
- memory/journal/2026/2026-10-01-memory-helper-retirement.md blob 425d8b634b8e6ddaa5fd3804b57bb8fbd1e86316
- memory/journal/2026/2026-10-01-memory-v8-design-and-boundaries.md blob 9dc218a9ba723221b0d8702807ea0439cd9ab10c
- memory/journal/2026/2026-10-01-portable-registration-review.md blob f16cb521f03a2478d1b42880ad7fd01bcb461b4b
- memory/journal/2026/2026-10-02-capture-slug-collision-refused.md blob 35cf7c86f72ef7e9346550b49023a43fd8df1a61
- memory/journal/2026/2026-10-02-first-raid-on-pi-pr1153.md blob a6dee28a3934fbcf5c9401f57b0ae9292fd31da0
- memory/journal/2026/2026-10-02-hunt-0875-runner-nondeterministic-guard.md blob 75c10d8661da275cb4843efe243bc6943c175a03
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
- memory/journal/2026/2026-10-02-memory-v8-smoke.md blob 23835a96e1dba234bacb6cb0e94f89835dd22bcc
- memory/journal/2026/2026-10-02-orchestrated-raid-closes-memory-v8-tracker.md blob c24f92fddeaccf3e35c916ae90144d8c008fe5a7
- memory/journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md blob 8e6e73730033d0ee324afc2820a95353cd54c9a3
- memory/journal/2026/2026-10-02-raid-1015-annotation-collision.md blob 43691ed1e9a9ce8aad6a3a05f7dd70d09a7538bb
- memory/journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md blob 0668fc51ac747be559debd87ba63898f35ce98e7
- memory/journal/2026/2026-10-02-retired-read-index-invoked-in-trial.md blob e3c9a9a973d5631d6505892d2d64f6177b7f0ea9
- memory/journal/2026/2026-10-02-reviewer-attribution-design.md blob d1a855d95eb5a2002e4e4f0e6f7b35bd1e5c653d
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
- memory/journal/2026/2026-10-05-brood-adoption-pr1187.md blob 15a97ca149fa554bd5cbd27a7d220f6482d1bec0
- memory/journal/2026/2026-10-05-raid-1005-1023-verification-recovery.md blob 0e556611bdbd22f69ae3deb61932a73ed361a19e
- memory/journal/2026/2026-10-05-raid-926-supersession-and-publication.md blob 8cef1af95b09d08ff1ff64ea515c7e790e1301c4
- memory/journal/2026/2026-10-05-review-attribution-pr1185.md blob 13f22bffeb15189cc1508fd7308c45d8fe74b81d
- memory/journal/2026/2026-10-05-review-attribution-pr1186.md blob b4ff826b0462fa47561ab13b699506de5e55cf90
- memory/journal/2026/2026-10-05-review-attribution-pr1189.md blob b890ceeee5014ea2e1611b0ccf72f002edd9b653
- memory/journal/2026/2026-10-05-review-attribution-pr1191.md blob 75d4141f556237541eec5c6b3c8b16f7d4731193
- memory/journal/2026/2026-10-05-review-attribution-pr1192.md blob 8cf11dcfc15d86951685d393ffef194bd276c7be
- memory/journal/2026/2026-10-05-review-attribution-pr1193.md blob 11e2f290bf86870d30d79fe532f80251a25c07f5
- memory/journal/2026/2026-10-05-review-attribution-pr1194.md blob 915c04a4778ab3790023b4b45ec1525e7bb982e9
- memory/journal/2026/2026-10-05-review-attribution-pr1195.md blob a03de34ce69abf0414ffb8dbda85ac166eef5489
- memory/journal/2026/2026-10-05-review-attribution-pr1196.md blob f88240fcbaeebb9f0053fe786c79ee756365a34b
- memory/journal/2026/2026-10-05-review-attribution-pr1197.md blob 789b7bfe742cc837272a9e45dd486e483a8fff61
- memory/journal/2026/2026-10-05-review-attribution-pr1198.md blob 26ee5db06a7a171dfcd47edd7f6ec878be3ea127
- memory/journal/2026/2026-10-05-review-attribution-pr1199.md blob aa653c5012778539d579f58815c2f39f31ab8a1b
- memory/journal/2026/2026-10-05-review-attribution-pr1200.md blob e26c833a807a69ec4c39ff033ac14fc52a9b1909
- memory/journal/2026/2026-10-05-review-attribution-pr1201.md blob 63baa26587cbd728efd0cba8bf075842b7a159c4
- memory/journal/2026/2026-10-05-review-attribution-pr1202.md blob aa84a325e313d024f1d44e6d61b1691d6c23182b
- memory/journal/2026/2026-10-05-review-attribution-pr1203.md blob 9865a71fe08fbede28598e32c62f9f09402d0d00
- memory/journal/2026/2026-10-05-review-attribution-pr1205.md blob 64e51f64145b5dab3976a8dae5cafdca773b45b5
- memory/journal/2026/2026-10-05-review-attribution-pr1206.md blob 233aeca0c543cd527d04350010e58d6008c8335b
- memory/journal/2026/2026-10-05-review-attribution-pr1207.md blob 4dd3abb3b607a65755cfdd4069f6df38a9665f4c
- memory/journal/2026/2026-10-06-0913-dispatch-close-path.md blob ca19e80ca938b78ee454accb2cfc195cff926857
- memory/journal/2026/2026-10-06-leftover-podman-service.md blob c5c9d7cb2e1d5a3648f7b41f1a649bc44af44c71
- memory/journal/2026/2026-10-06-local-ci-act-equivalence.md blob 09da99d430684205e374b6ce86102823730d4fd4
- memory/journal/2026/2026-10-06-model-tournament-cycle-2-close.md blob 6fc88c8a5d0e928634c579d3455cff05c2e5f192
- memory/journal/2026/2026-10-06-pr1225-author-review.md blob 71ecb9825b40a7b32b225173e4c905789a6956f3
- memory/journal/2026/2026-10-06-raid-1042-capture-review-repair.md blob e3049dba9791fd8989d5ebb831e41d85499f29da
- memory/journal/2026/2026-10-06-raid1004-closure-experience.md blob 57be329576a8abdd6c7727d919130b3a9955c5cb
- memory/journal/2026/2026-10-06-review-attribution-pr1204.md blob a83dd6771326207c2c1021e2680208dfebf4b176
- memory/journal/2026/2026-10-06-review-attribution-pr1209.md blob 587b1ef04735038ed66e8cdad91cde7161eefe15
- memory/journal/2026/2026-10-06-review-attribution-pr1210.md blob 8dc49381995c3aa6ff61c6e6c539048b0ad036f5
- memory/journal/2026/2026-10-06-review-attribution-pr1211.md blob 4091544d9e840206642c5cb387acbdbba2f0e2a5
- memory/journal/2026/2026-10-06-review-attribution-pr1213.md blob 76c425e005459cf93f8baa41d9beed2e56fa87c0
- memory/journal/2026/2026-10-06-review-attribution-pr1218.md blob 0a9b8bd6c9e39c278b8897bbcb5b68a4764cc8b8
- memory/journal/2026/2026-10-06-review-attribution-pr1220.md blob 8f9024cae1fdba093e1a3047004139b41c6eeb10
- memory/journal/2026/2026-10-06-review-attribution-pr1221.md blob 039b885d22743db6f13fc7adaaa403849a8af21c
- memory/journal/2026/2026-10-06-review-attribution-pr1222.md blob eb294027476eac1dc01dd8c9a21cf6a2309161c0
- memory/journal/2026/2026-10-06-review-attribution-pr1224.md blob 8045e5d66d41a7d10911797199e09621d9cf6a8d
- memory/journal/2026/2026-10-06-review-attribution-pr1227.md blob a78a3650d8262332d8c63aa89730bd1aeb1d0cd6
- memory/journal/2026/2026-10-06-review-attribution-pr1229.md blob 70ec5637187476012f4e1cc1809e91d26af8d3a8
- memory/journal/2026/2026-10-06-review-attribution-pr1234.md blob 416dbc0b49fc5cc6085ca223edcc307d941aa894
- memory/journal/2026/2026-10-06-review-attribution-pr1235.md blob aaf310faba61d43929437a4259e3d898c6a077e3
- memory/journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md blob 57cdc357a31fa2215d6d8be5d3cef05a783338b1
- memory/journal/2026/2026-10-07-mistral4-pi-context-correction.md blob 695998ad50d31b6d37da48a350f00dd06f727409
- memory/journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md blob 4955a6ec349d09327a53d298dd51a1573f276f52
- memory/topics/branch-cleanup-incidents.md blob afeb9493f271fb9e1327b4fbebabef46cbd158dd
- memory/topics/git-worktree-session-guards.md blob b4428fa1c2e040f03bd5dbc9107992df87bec1c1
- memory/topics/memory-v8-acceptance-trial.md blob 4f689019a768684a8e9253787ad7fa63fabf222c
- memory/topics/memory-v8-governance.md blob d95768af290d7bf5f0453405ebba7165d0feddb4
- memory/topics/subagent-model-effort-levers.md blob beb3a1960e146ba6df711820729fc9a986e78c5f
- memory/topics/zotero-library.md blob 21ab3f6cb69bbf7331024fd36e859f07d2e7ce58
- rules/claude-code.md blob 8c242618bff8d4aa11f612de94ade074dd40f884
- rules/git.md blob d9a951ce87d595a780798081ab98464b4bdf1e90
- rules/guards.md blob b707b59084af8fa5426d8285b017bf6b3e1bc129
- rules/workflow.md blob 00caec99295402778a072d04aa6fb7cc67f59315
- skills/merge/SKILL.md blob 918c7ac271569078c86c1627dcef92ce64f4b96f
- tests/test_memory_v8_pilot.py blob fb10959d199f5004772cc9f7a759f3260dfacdd0
- tests/test_on_start_memory_injection.py blob 2a2f18967f1145470ff4fa9dd9fd3aae66d2337d
- tests/test_resident_census.py blob 4344777d049f3bae5bf59d57884944718990dd00
- ~/.claude/projects/-home-haduong--agents/memory/feedback_no_blocking_waits.md blob c6ebb58feb461f8d0eaae1c7c8dde871a5073133 (native note, attributed; text preserved in the annex)

Encrypted entries: no `.age` file exists under `memory/`, and the per-project
key directory `~/.config/keys/memory/` is absent on this host. Skipped: 0.
Unavailable sources: none needed. Not consolidated: `memory/pending-capture-pr1211.md.txt`
and the root `feedback_*.md`/`reference_*.md` notes beyond what the existing
topics already cite. This pass may not edit them (see unresolved questions).

### Editorial changes

New topics (merging). This pass grouped the 87 journal entries that the
accepted report did not cover into four themes. Each theme carries dated
sources, groups positive and negative cases, and has a hypotheses section.

- `topics/shared-checkout-concurrency.md`: nine episodes of sessions or
  subagents acting on one checkout or one live user file. The common factor
  is presented as a connection, not a cause.
- `topics/raid-review-and-merge.md`: what panels and gates caught, how panels
  degraded, the five override cases side by side (1018 force-approve on
  evidence, #1187 waiver, #1157 direct merge, #1235 reduced ceremony, #1245
  force-approve with no reviewer), merge mechanics, the author's 2026-10-03
  tracker statement (recorded as an author statement, not a rule), and an
  aggregate of the 33 review-attribution records. The counts (254 ran,
  3 failed; 108 adopted, 15 not) were derived with `grep` over the records
  and are labelled as derived. This answers the first dream's open question
  about a reviewer theme, because there are now far more than one episode.
- `topics/runtime-observations.md`: pi, Vibe and Codex observations and the
  model-tournament cycle 2. The tournament entry's opening figures and
  conclusions are marked as superseded by the entry's own two corrections
  (142/160 OK, 18 non-OK; seven VOID-EMPTY results reclassified as OpenRouter
  403 key-limit errors). The topic points at the corrected summary and grid
  instead of restating medians.
- `topics/ci-and-test-suite.md`: suite economics, runner nondeterminism,
  local CI parity, forge waits and author decisions.

Refreshing:

- `topics/memory-v8-governance.md`: post-trial blockers cleared (#1147,
  #1150), the 0909, 0913, 0912 and 0919 closures, and Brood adoption (author
  decision, PR #1187) with the limits its evaluation states.
- `topics/memory-v8-acceptance-trial.md`: the Pi miss is now explained (pi
  loads only the first of AGENTS.override.md, AGENTS.md, AGENTS.MD,
  CLAUDE.md), the re-runs passed (#1150) and the codex channel closed
  (#1147). Source: the orchestrated-raid entry. The original observations
  stand unchanged.
- `topics/zotero-library.md`: interface-architecture decisions and the
  per-verb safety-contract asymmetry established by the #1179 review.

Pruning (index): the four "Recent experiences" links to 0918 entries were
removed from `MEMORY.md`, and all four remain linked from the acceptance-trial
topic. Link texts were shortened to keep the index under the 2100-character
hook budget enforced by `tests/test_resident_census.py`: the index is now
1761 characters and 36 lines, against 2068 characters before. The four
reference-note links and the sentinel sentence that tests require are kept.
The Dreams section marks this report "under review". Once it is accepted, the
next dream may drop the first dream's line, as the first dream suggested.

No journal entry was rewritten, moved or deleted. No rule, AGENTS.md, skill
or runbook was edited.

### Coherence

All ten indexed topics were compared with each other and against AGENTS.md,
rules/git.md, rules/workflow.md, rules/claude-code.md, rules/guards.md and
skills/merge/SKILL.md.

- `subagent-model-effort-levers` agrees with rules/claude-code.md
  § Subagent levers (model pinned per launch, effort per definition, per-call
  effort on the workflow path). No change.
- `shared-checkout-concurrency` against rules/workflow.md § Delegation, which
  says to "forbid add/commit/push explicitly": on 2026-10-04 a reviewer
  obeyed a brief forbidding edit, commit and push, yet switched branches.
  This is recorded as an observation outside the rule's wording. Neither
  reading is presented as advice.
- `ci-and-test-suite` points at skills/merge/SKILL.md for the padme rule and
  at ticket 1045. It states no procedure of its own.
- The native note on blocking waits agrees with the PR #1245 entry and with
  the author's request recorded there. It is cited, not promoted.
- Journal statements phrased as lessons ("Tickets age; recount before
  raiding", "Named files only in shared checkouts", the 1015 annotation
  proposal, "gates prove what is tested; panels catch...") are kept as the
  entries' own readings or as hypotheses. None is presented as a rule.
- After the refreshes, no contradiction remains between indexed topics.

## Unresolved questions

1. Two entries were extended in place after their first capture. The
   raid-926 entry has dated sections of 2026-10-06, and the tournament entry
   has two in-entry corrections. DREAM.md says a correction is a new entry
   linking the original. Whether appended, dated sections satisfy the
   append-only rule is for the author to decide. This dream used the
   corrected text and did not edit either entry.
2. Loose files in the `memory/` root, outside this pass's write scope.
   `pending-capture-pr1211.md.txt` is a pending-capture draft that PR #1211's
   attribution record now cites as model evidence
   (`model-state=runtime-masked`). It is open whether it should stay as a
   root file, become a journal entry, or remain a permanent evidence pointer.
   The four `reference_*`/`feedback_*` notes are pilot sources pinned by
   `tests/test_memory_v8_pilot.py`, and
   `feedback_rules_come_from_memory_consolidation.md` stays retired history.
   None was touched.
3. Five own-review classifications (PRs 1214-1217 and 1219) remain UNKNOWN.
   PR #1245 has no attribution record because no reviewer ran. Whether
   attribution coverage should mark such merges is a capture question, not a
   dream one.
4. The 2026-10-02 entry recorded the local-main repair (reset to
   origin/main) as pending the author's call. No later entry records the
   outcome.
5. No source establishes the cause of PR #1245's 1 h 49 min stuck required
   check, or of the personal-data-guard infrastructure failure in the
   local-CI negative controls.
6. The `.age` path is still unexercised on real material (carried over from
   the first dream).

## Pass 2

Same checkout, immediately after pass 1, over the same revision set. The
journal, authority and native blobs are identical to the pass-1 ledger. This
pass re-read the files that pass 1 wrote, at these revisions:

- memory/MEMORY.md blob e8313ac812d73ee76f54a00dfca9e22e777042f3
- memory/topics/branch-cleanup-incidents.md blob afeb9493f271fb9e1327b4fbebabef46cbd158dd (unchanged)
- memory/topics/ci-and-test-suite.md blob 72d1a399e4e04a4d3ee1523c9e167ff6e88016a6
- memory/topics/git-worktree-session-guards.md blob b4428fa1c2e040f03bd5dbc9107992df87bec1c1 (unchanged)
- memory/topics/memory-v8-acceptance-trial.md blob eeaae2f37e86b5a5222565e2d65b437090a8709b
- memory/topics/memory-v8-governance.md blob 2bd91fca7ac7fc782125a718bea671d916e8be77
- memory/topics/raid-review-and-merge.md blob 3fb283c481e94c7c3eb099db1f1b69fa58c25eb2
- memory/topics/runtime-observations.md blob c167eb5f522ecc8e572f5877b680ca8babe78af1
- memory/topics/shared-checkout-concurrency.md blob 255f972a76f455133a0fdec9244766245032a992
- memory/topics/subagent-model-effort-levers.md blob beb3a1960e146ba6df711820729fc9a986e78c5f (unchanged)
- memory/topics/zotero-library.md blob 78fba595c664c0f980eac6e7f254631fea068c55

Imported as new: none.

Corrections re-examined against their sources:

- Attribution aggregate: re-running the `grep` count found **33** records,
  not the 35 that pass 1 first wrote. The topic and this report were
  corrected to 33. The status and adoption counts (254/3, 108/15) reproduced
  unchanged. This was a counting slip in pass 1, caught by the re-check.
- Tournament supersession: the entry's two "Correction (2026-10-06...)"
  paragraphs state 142/160 OK and 18 non-OK, and withdraw the
  silent-abandonment and heavy-ticket conclusions. The topic says exactly
  that. The correction stands.
- Acceptance-trial refresh: the orchestrated-raid entry states the pi loading
  order and the #1147/#1150 outcomes as written. It stands.
- Governance refresh: the Brood entry states the adoption, the unchanged
  Dream/Roar authority and fixture-only evidence. The 0913 entry states the
  PR #1212 closure. Both stand.
- Links: every relative link in the files this pass wrote resolves (checked
  by script). The index is 36 lines and under the 2100-character budget, and
  the memory tests pass. The first test run failed `test_topics_cite_sources_and_provenance` because the four new topics lacked the provenance line; it was added, and the blobs above are post-fix. 19 tests passed (census, v8 pilot, on-start injection, legacy retirement).

## Annex: native note used

Source: Claude Code native auto-memory of the harness project,
`feedback_no_blocking_waits.md`, blob c6ebb58f, modified
2026-10-07T19:42:10Z. Body text, as written:

> Do not launch blocking wait commands (`gh pr checks --watch`, `until … sleep` loops) for CI or merges.
>
> **Why:** 2026-10-07, PR #1245: a `--watch` hung ~2 h behind a stuck `pytest-guard` run; the author found it "long" and asked to stop blocking waits.
>
> **How to apply:** check status once (non-blocking), report, and let the author or a later turn re-check. Detect a stuck job by comparing its start time to its usual duration.
