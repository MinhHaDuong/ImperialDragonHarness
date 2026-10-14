# Red-team review: PR 1389, round 2

**Anchor:** `825b1eda84a5948705ed618101b5a799821618d1` in `/tmp/idh-raid-1080-prep`. All 12 changed paths and the complete diff were supplied.

**Method:** tools were disabled, so every check below reads the supplied text. I did not recompute any SHA-256 values. Retained historical records are kept apart from the accepted run:
- the `4435caf5…` and `e457cd8e…` snapshots;
- the warm outer session `01a13990…`;
- invalid worker `449abcb7…`.

The accepted run is cold outer `01a139bf-563d-71b2-ae0d-153ffda57d84` with worker `3f10718b-2941-4929-9da5-c8c444afce35`.

## Prior concerns, checked against the final source

| Prior concern | Status | Evidence |
|---|---|---|
| `rules/` substring check could not tell old from new contract | **Fixed** | `tests/test_verify_adherence_semantic.py:14` now requires ``Include existing conventional `rules/` ``. The RED output retained in `outer.jsonl` shows the old section text begins "Only runs if any `.claude/rules/*.md`…", which does not contain this phrase. |
| "Fresh/neutral" claimed for a warm outer | **Fixed** | `outer.jsonl` `observed_caller_launch` records `fork_turns: "none"` and the new thread `01a139bf…` (`cold_session_meta`, ordinal 0). The caller's plaintext (`caller_plaintext_annotation`) gives an expected hash, the arguments and evidence instructions, with no defect hint. `docs/2026-10-14-adherence-semantic.md:83-88` now calls the earlier runs warm. |
| Discovery, route load and identity observations missing from the extract | **Fixed** | Cold ordinals 19–29 hold the `rg --files` discovery, the merge-base and full diff, and the loading of `route/SKILL.md`, `grid.json`, `routes.json` and `decorrelation.md`. Ordinal 7 holds `cold_turn_context`. Ordinal 50 records the launch line in `worker.launch.json` before `Popen`, as the contract requires. |
| Caller must not supply missing severity or upgrade findings | **Fixed** | `skills/verify-adherence/SKILL.md:242-244` now says so, and the test includes `"must not create findings"`. The accepted worker emitted `"severity": "blocking"` itself (`worker.jsonl` `accepted_worker_result`). |
| Provenance labelling in `outer.jsonl` | **Fixed** | The annotation kinds (`caller_plaintext_annotation`, `validation_correction`, `development_check_output`, `cold_*`) are distinct, and the doc's provenance section (`:62-81`) names them. |

The frozen `loaded_skill.source` contains the new "must not create findings" clause. By reading, it matches the current `SKILL.md` text; I did not recompute its hash.

## Findings

1. **minor, confidence high — verifiable:** The reproduction recipe does not rebuild the archived fixture.
   - `docs/2026-10-14-adherence-semantic.md:24-29` says to append one line to `rules/worktrees.md`.
   - The fixture file has 5 lines (`tests/fixtures/adherence-semantic/rules/worktrees.md`, hunk `@@ -0,0 +1,5 @@`).
   - The real run's diff (`outer.jsonl` cold ordinal 29, hunk `@@ -3,3 +3,5 @@`) adds a blank line *and* the sentence, which puts the sentence at line 7 (head blob `6b099c4`).
   - Following the recipe as written puts the sentence at line 6 and gives a different blob. That changes the line-number facts the accepted validation depends on: the rejected-evidence reason says "actually line 7".
   - Fix: say "append a blank line and then this line", or quote the expected head blob `6b099c4`.

2. **minor, confidence high — verifiable:** `evidence.json` `accepted_run` is an edited copy of the run's verdict, but the doc presents it as the run's own output.
   - The cold outer's emitted verdict (`outer.jsonl` cold ordinal 71) has the following, all *absent* from that verdict:
     - `completion_evidence` with only `uuid` and `exit_code`, with no `result_uuid` or `exit_status`;
     - `family: "Anthropic (route grid lineage for observed model)"`;
     - no `mechanical_runner` block.
   - `docs/adherence-semantic/evidence.json` adds `result_uuid`, `exit_status` and `mechanical_runner`, and shortens `family` to `"Anthropic"`.
   - `tests/test_verify_adherence_semantic.py:41` asserts against the added `completion_evidence["result_uuid"]` field.
   - The values themselves are supported by raw records: the uuid at ordinal 64 and the runner output at ordinal 36. The issue is labelling: `docs/…:64` says `evidence.json` "holds the final accepted verdict".
   - Fix: keep the emitted verdict verbatim and put the added fields in a labelled annotation, or say in the doc that the verdict was normalized.

3. **minor, confidence medium — consider:** The accepted worker gave no evidence entry for `AGENTS.md`, although `semantic_review.rule_sources` lists it.
   - After the line-5 entry was rejected, nothing addresses the newly added scope sentence either.
   - The validation note says "Remaining evidence covers the sole rule section". That understates the gap: the prompt asks for evidence "for each rule section".
   - The contract only makes full evidence coverage mandatory for a *clean* report (`SKILL.md:239-240`), so this run is not invalid under the current text.
   - The weakness is that a failing report with partial coverage passes validation silently. Consider stating whether evidence coverage is required whenever a report has findings.

4. **nofollow:** The accepted worker prompt record in `worker.jsonl` has no `sha256` field, unlike the other prompt records. Its text is retained verbatim, so nothing depends on the hash.

5. **nofollow:** The cold outer also read harness-level files outside the project. Ordinal 25 includes `/home/haduong/.agents/memory/MEMORY.md` and ordinal 40 two memory topics. None of them carries the 0310 rule or the defect, and the doc already scopes "empty-context" to the absence of forked turns.

No blocker found. All three original exit criteria are met by the accepted cold run:
- rule discovery under `rules/`;
- `semantic_review` status and worker identity recorded from runtime records, not self-report;
- a blocking `scripts/check-tree.sh:3` finding with a non-empty `suggested_test`, mechanical success, and overall `adherence: FAIL`.

verdict: comment