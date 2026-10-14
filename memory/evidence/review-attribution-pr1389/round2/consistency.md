# PR 1389 round 2: consistency seat report

**Seat:** code-reviewer, consistency perspective. **Anchor:** `825b1eda84a5948705ed618101b5a799821618d1`, as supplied. Tools were disabled, so every finding below comes from the supplied ticket, contracts and complete 12-path diff. I could not re-check the anchor myself, and I ran no commands. The orchestrator records my runtime identity.

## Prior concerns, checked against the current source

| Round-1 concern | Status | Evidence |
|---|---|---|
| The `rules/` substring assertion did not discriminate | **Fixed** | `tests/test_verify_adherence_semantic.py:14` now asserts ``Include existing conventional `rules/` ``. That clause is absent from the legacy text ("Only runs if any `.claude/rules/*.md`…"), so the test can tell the two contracts apart. |
| The outer seat called "fresh" was actually warm | **Fixed** | The accepted run is outer `01a139bf…`. `outer.jsonl` has `observed_caller_launch` with `fork_turns: "none"` and `cold_session_meta` ordinal 0. The doc (`docs/2026-10-14-adherence-semantic.md:85-90`) labels the earlier runs as warm. |
| Caller message, discovery and route-load records were missing | **Fixed** | `outer.jsonl` now has a labelled `caller_plaintext_annotation`, the `rg --files` discovery (cold ordinal 19) and `cat …/skills/route/SKILL.md` (ordinal 19/23). The caller text carries the expected hash but no description of the defect. |
| The caller could supply missing severity | **Fixed** | `skills/verify-adherence/SKILL.md:242-244` now forbids it, and `tests/test_verify_adherence_semantic.py:15` asserts `"must not create findings"`. The accepted worker returned `severity: blocking` itself (`worker.jsonl`, `accepted_worker_result`). |
| The provenance of `outer.jsonl` was unclear | **Fixed** | The "Evidence provenance and limits" section lists native extracts, annotations and check output separately. |
| Ticket closure chronology (nofollow) | Unchanged | The ticket log still shows closure at `08:47Z`, before the cold run at `09:30Z`. The "Implementation evidence" section quotes the final hash `70146986…`, which matches `evidence.json`. |

## New findings

1. **Minor, confidence high.** verifiable: `evidence.json` presents its `accepted_run` as the final verdict, but it is a reshaped version of what the outer seat emitted, not a verbatim copy.
   - **What the outer emitted** (`outer.jsonl`, cold ordinal 71, the verdict printout):
     - `completion_evidence` has `uuid` and `exit_code` only.
     - `family` is `"Anthropic (route grid lineage for observed model)"`.
     - There is no `mechanical_runner` block.
   - **What `evidence.json` contains instead:**
     - `completion_evidence` adds `result_uuid` and `exit_status`, duplicating `uuid` and `exit_code`.
     - `family` is shortened to `"Anthropic"`.
     - It adds a top-level `mechanical_runner` block.
   - **Why it matters:** the test reads exactly those added keys (`tests/test_verify_adherence_semantic.py:27,41`). The values can be traced to observed records, and the finding text itself is verbatim. But the doc says `evidence.json` "holds the final accepted verdict", and it does not say these fields were added afterwards to fit the test schema.
   - **Fix:** either label the normalization in the doc, or store the outer's `verdict.json` verbatim and point the test at its native keys.

2. **Minor, confidence high.** verifiable: the reproduction recipe and the retained diff disagree about the appended text.
   - The doc says to "append the following line" (`docs/2026-10-14-adherence-semantic.md:24-28`).
   - The retained diff (`outer.jsonl`, cold ordinal 29: `@@ -3,3 +3,5 @@`, `+` empty line, `+Apply this rule…`) adds a blank line before the sentence.
   - That blank line is what puts the sentence on line 7. Line 7 is the basis for rejecting the worker's `rules/worktrees.md:5` evidence anchor (`evidence.json`, `rejected_worker_evidence`).
   - Following the recipe literally puts the sentence on line 6 and changes the blob away from `6b099c4`.

3. **Minor, confidence medium.** consider: the doc credits more to `turn_context` than it shows.
   - The doc (`docs/2026-10-14-adherence-semantic.md:43-44`) says "Its model and effort are observed in `turn_context`: Sol 6.1, medium, OpenAI family."
   - `turn_context` records model and effort only (`cold_turn_context`). The family comes from the route grid, as `evidence.json` `outer.identity_source` correctly says.
   - Suggested wording: "…medium; OpenAI family from the route grid."

4. **Minor, confidence medium.** consider: the accepted worker artifacts lack the hashes the cold outer computed for earlier runs.
   - The `worker.jsonl` record `accepted_worker_prompt` has no `sha256`. The invalid and earlier worker prompt records both have one.
   - `accepted_worker_result.raw_stdout_sha256` (`ca7bcb35…`) does not appear in any retained cold-outer tool output, unlike the earlier runs, whose hashes came from in-trace `sha256sum` calls.
   - Either record where that hash came from, or say that the accepted artifacts were hashed after the run.

5. **nofollow:** the retained `development_check_output` red, green and lint records come from the earlier test parametrization (7 parameters; green shows 8 tests in the module). The current module has 9 tests. The doc frames these records as historical, which is accurate. They do not cover HEAD; only a fresh gate run on the anchor does.

## Consistency of the contract with the accepted run

The accepted run follows every Phase 3 instruction I checked:
- **Rule discovery:** `AGENTS.md` and `rules/` were both found.
- **Base:** `main` was used because the fixture has no remote.
- **Launch line:** written to `worker.launch.json` before `Popen`.
- **Worker prompt:** contains the skill's prompt text verbatim, plus base/head identifiers, full sources and the full base rule.
- **Identity:** taken from the `init` record and `modelUsage`, not from self-report.
- **Effort:** recorded as unavailable.
- **Rejection:** the outer rejected one unsupported anchor and did not supply any missing fields.
- **Verdict mapping:** a blocking finding produced `FAIL` with `escalation: null`.

The schema placeholders `<project-rule-path#section>` match the `rules/` discovery. Ticket, doc and evidence agree on the hash `70146986…`. All three original exit criteria are met by the cold run.

verdict: comment