# PR 1389 round 2: correctness review

**Seat:** correctness, read-only, tools disabled. Every input came from the supplied prompt.
**Anchor:** `825b1eda84a5948705ed618101b5a799821618d1`, all 12 paths, complete current diff.
**Requested route:** Opus at medium effort. The orchestrator adds the observed identity and cost.

## Prior concerns, checked against the final source

| Round-1 concern | Status | Evidence |
|---|---|---|
| The test matched the bare substring `rules/`, which the old contract also passes | **Fixed** | `tests/test_verify_adherence_semantic.py:14` now requires ``Include existing conventional `rules/` ``. That text is in the phase-3 section of `skills/verify-adherence/SKILL.md`. The old phase 3 (removed lines in the SKILL diff) only says "Only runs if any `.claude/rules/*.md` file changed", so the new assertion catches the old contract. |
| The final run was called fresh, but the outer session was reused (warm) | **Fixed** | A separate outer session `01a139bf-…` was launched with `fork_turns: none` (`outer.jsonl` `observed_caller_launch` and `cold_session_meta`). It loaded SHA `70146986…` at `cold_custom_tool_call` ordinal 10. `docs/2026-10-14-adherence-semantic.md:31-45` now separates this run from the earlier warm runs (`:79-84`). |
| Caller messages and the discovery/route loading were not retained | **Fixed** | The caller's plaintext is kept as a labelled `caller_plaintext_annotation`. It names the branch, worktree and expected hash, and gives no defect hint. The cold sequence keeps discovery (ordinal 19), loading of the route skill, grid and decorrelation files (19/25), the runner (33), a launch line written before launch (50), completion (61) and validation (68). |
| The caller might create findings or fill in missing worker fields | **Fixed** | `SKILL.md:242-244` now says the caller may reject findings but must not create them, upgrade severity, or supply missing fields. `test_verify_adherence_semantic.py:15` checks this. |
| `outer.jsonl` did not label where its records came from | **Fixed** | `doc:67-78` lists native extracts, annotations and check output separately. |

The accepted run meets every original exit criterion:
- the outer read `rules/` and saw the diff touch it;
- `make syntax` passed with exit 0;
- a separate worker ran: Haiku 5.5, session `3f10718b…`, result `260da837…`, `is_error: false`, `terminal_reason: completed`;
- the worker reported the violation itself, with explicit `severity: blocking` at `scripts/check-tree.sh:3` and a nonempty `suggested_test`;
- the final verdict is FAIL with no escalation.

In the stored copy, the finding text and `suggested_test` match the worker's `result` field exactly after both levels of escaping are undone.

## Findings

1. **verifiable:** The "frozen" accepted run is not the outer's verbatim verdict, and the test relies on the fields that were added afterwards. Confidence high; minor.
   - The cold outer's actual verdict (`outer.jsonl`, `cold_custom_tool_call_output` ordinal 71) has `completion_evidence` keys `path, uuid, subtype, terminal_reason, exit_code, validated_report`. It has no `result_uuid` or `exit_status`, and no top-level `mechanical_runner`. Its `family` is `"Anthropic (route grid lineage for observed model)"`.
   - `docs/adherence-semantic/evidence.json` `accepted_run` adds `completion_evidence.result_uuid` and `exit_status` (around lines 89-90) and a `mechanical_runner` block. It also shortens `family` to `"Anthropic"`.
   - `tests/test_verify_adherence_semantic.py:28` (`accepted["mechanical_runner"]["exit_status"]`) and `:41` (`…["completion_evidence"]["result_uuid"]`) therefore check fields the archivist added, not fields the outer emitted.
   - The values are true: the same UUID is under `uuid`, and phase `"1"` has `exit_code: 0`. But `doc:53` ("preserved … verbatim") and `doc:62-63` ("holds the final accepted verdict") overstate how faithful the archive is.
   - Fix: store the outer's `verdict.json` byte-for-byte and point the test at `uuid` and `phases["1"]["exit_code"]`, or label the added fields as derived.

2. **consider:** It is unclear when a bad anchor rejects one entry and when it makes the whole report invalid.
   - `SKILL.md:242` says "Reject … unsupported anchors". `SKILL.md:245-246` says "malformed or unanchored output → `status: invalid`".
   - The final run rejected one evidence entry with a wrong line (`rules/worktrees.md:5`; the sentence is on line 7) and kept the status `ran`. That fits the first sentence, but the contract does not say which rule wins.
   - Suggested clarification: an unsupported anchor on a finding or evidence entry rejects that entry; the report is `invalid` only if a required field is missing or no valid evidence is left. Confidence medium.

3. **consider:** The evidence check says coverage is complete, but the worker gave no evidence for `AGENTS.md`.
   - The validation reason in `evidence.json` (`rejected_worker_evidence[0].reason`) says the remaining evidence "covers the sole rule section". But `rule_sources` lists both `AGENTS.md` and `rules/worktrees.md`, and the phase-3 prompt asks for evidence on *each* rule section.
   - It doesn't change the outcome here, because the report has a blocking finding and is not a clean report. The wording should still say evidence covers the violated rule, not every reviewed section. Confidence medium.

4. **nofollow:** The ticket was closed at 08:47, while the accepted cold run happened at 09:30.
   - The body was later updated to SHA `70146986…`, which matches `evidence.json` and the cold outer's own hash output.
   - This was disposed of in round 1 and nothing new changes it.

No blockers. Nothing I found makes the final source or the accepted cold run incorrect. The finding 1 discrepancy is about whether the archive is verbatim; it does not affect the correctness of the result.

verdict: comment