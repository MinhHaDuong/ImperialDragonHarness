# Red-team review: PR 1389, HEAD 00c5a33352d23d75a08f5d3bf2c50b011be48635

**Perspective:** red team. I tried to break the claim that ticket 1080's exit criteria are met by real execution and not just by wording.

**Inputs:** only the supplied diff, the closed ticket, the profile and rules files, and the full contents of the anchor files. I could not run any command here (no shell), so I recomputed no hash and reran no gate. Every finding below comes from reading the supplied text.

## Exit criteria against evidence

| Criterion | Evidence | Red-team result |
|---|---|---|
| 1. Phase 3 trigger matches the harness `rules/` path; a rules-touching diff always launches a worker or records why not | `skills/verify-adherence/SKILL.md` §3 (diff lines +198–+211): discovery covers `AGENTS.md`/`CLAUDE.md`, `rules/` and `.claude/rules/`; "required whenever the diff touches any discovered rule file"; `status: skipped` must carry a reason | **Met in the contract.** The accepted run does not show discovery being *performed* (F2). |
| 2. Verdict states whether phase 3 ran and which worker served | `SKILL.md` §4 `semantic_review` block (diff lines +254–+266) and the mapping paragraph (+282–+288); `evidence.json` `accepted_run.semantic_review` | **Met.** `worker_id` `0df0c0b2-…` matches `worker.jsonl` `accepted_worker_result.session_id`. The model comes from `modelUsage.canonicalModel`, not from self-report. |
| 3. Fixture with the 0310 rule, violation in the diff, no caller hint, flagged by the semantic path with `file:line` | `worker.jsonl` `accepted_worker_prompt`: the prompt holds only the sources and diff, no defect hint. `accepted_worker_result`: `scripts/check-tree.sh`, line 3, `"severity": "blocking"`, non-empty `suggested_test` | **Met at the worker level.** Whether the outer seat was neutral cannot be checked (F1). |

The verdict mapping holds: mechanical runner exit 0, a blocking semantic finding, and `adherence: FAIL` with `escalation: null` (`evidence.json` `accepted_run`).

## Findings

### F1. The "fresh neutral" accepted run reused an outer session that already knew the defect, and the caller turns are not retained

- **Severity:** nonblocker
- **Confidence:** high
- **Tag:** `verifiable:` `docs/adherence-semantic/outer.jsonl`
  - Line 1 (`session_meta` id `01a13990-…`) and `evidence.json` `outer.worker_id` show one session.
  - Lines 2, 5 and 21 are three `turn_context` records in that session.
  - Ordinals 128 and 196 (`outer_final`) are earlier turns of the same session. They already state the finding `scripts/check-tree.sh:3` with `severity: blocking`.
  - The accepted run follows at ordinals 392–446.

`docs/2026-10-14-adherence-semantic.md:76` calls this "A fresh complete neutral fixture invocation". Only the fixture directory (`/tmp/idh-1080-live-final`) is fresh. The outer seat is the fourth turn of the original session.

Caller messages are not archived: ordinals 25→30, 128→133 and 196→392 are gaps, and the doc says "unrelated runtime instructions … are omitted". So the ticket requirement "Invoke the complete skill with branch/worktree only, without a caller hint" cannot be checked for the outer seat. One trace shows steering: the second-to-third turn transition came right after the outer was told its severity normalization was invalid (`validation_correction`).

Criterion 3 still holds, because the semantic worker's prompt is retained and contains no hint. The doc should drop "fresh … neutral" for the outer, or archive the caller turns.

### F2. The accepted run hard-codes the rule universe; no discovery or route loading appears in the retained trace

- **Severity:** nonblocker
- **Confidence:** medium. The extract is admittedly partial: ordinals skip, and record `6679ea`, cited in `evidence.json` `earlier_valid_run…phase_1_0.discovery_record`, is absent from `outer.jsonl`.
- **Tag:** `verifiable:` `outer.jsonl` ordinals 392–435.

The only tool calls are:
- `cat SKILL.md; sha256sum`
- `make syntax`
- a prompt builder with `for f in ['AGENTS.md','rules/worktrees.md','Makefile','scripts/check-tree.sh']`, which asserts "Complete rule universe is AGENTS.md and rules/worktrees.md; no other instruction or rule files exist."

That list carries over from earlier turns on a different fixture path. The trace shows no listing of `rules/` or `.claude/rules/`, no `CLAUDE.md` probe, and no `git diff --name-status` for renames or deletions. It also shows no read of `skills/route/SKILL.md`, yet `evidence.json` records `route: "loaded route grid economical cluster…"`. The SKILL says "record the launch line before launch", and no such pre-launch record is visible.

The live run therefore demonstrates worker launch, completion and verdict mapping. It does not demonstrate the discovery half of criterion 1, which rests on contract text and `test_semantic_execution_contract` substring checks. Either retain the discovery tool calls or state in the doc that discovery was not part of the retained acceptance.

### F3. The contract lets the outer seat rewrite or upgrade worker findings, and the evidence shows it doing so

- **Severity:** nonblocker
- **Confidence:** high
- **Tag:** `verifiable:` `worker.jsonl` `invalid_worker_result.result` is a prose report with no `severity` field. In the same session, `outer.jsonl` ordinal 128 (`outer_final`) emitted `status: ran` with `severity: blocking` and a paraphrased `suggested_test` that the worker never wrote. Only a later record (`validation_correction`) reclassified it as invalid.

In the accepted run, the outer's emitted YAML (ordinal 446) again paraphrases the worker:
- `concern: script replaces required git rev-parse detection…`
- `suggested_test: initialize an ordinary repository…`

The verbatim worker finding is kept in `evidence.json`, so the archive is honest. But `SKILL.md` §3 (+232–+241) only says to "validate" and "reject". It never says that emitted `semantic_findings` must be the worker's own fields, or that the outer may drop items but must not add severity or invent content.

This is the inline-analysis path the ticket wants closed, coming back through post-processing. Attempt 2 proves the gap is reachable, and it was caught only by after-the-fact review.

Suggested fix: one sentence in §3, "Emit the worker's findings verbatim; the caller may reject a finding, never author or upgrade one."

### F4. `test_frozen_live_acceptance_record` mostly checks the evidence file against itself

- **Severity:** nonblocker
- **Confidence:** high
- **Tag:** `consider:` `tests/test_verify_adherence_semantic.py:26` checks `sha256(evidence["loaded_skill"]["source"]) == evidence["loaded_skill"]["sha256"]`. Both values come from the same JSON. The check is not tied to the committed `SKILL.md` or to the `outer.jsonl` `custom_tool_call_output` at ordinal 395, which prints the hash.

Other weak points:
- Line 43 asserts only that the substrings `"blocking"` and `"suggested_test"` appear somewhere in the raw result. It does not check `severity == "blocking"` on the parsed finding.
- Line 30 (`worker_id != outer.worker_id`) passes for any two distinct strings.

The test does cross-link `session_id` and `uuid` between files, which has value. To tie it to observed output, the test could also assert that `e457cd8e…` appears in the ordinal-395 tool output in `outer.jsonl`, and parse the JSON block in `accepted_worker_result.result`.

I could not check whether the HEAD `SKILL.md` hashes to `e457cd8e…`, because no shell was available. By reading, the `evidence.json` source text matches the diff's new §3 and §4.

### F5. The retained `make lint` output predates the final test tree

- **Severity:** nonblocker
- **Confidence:** medium
- **Tag:** `verifiable:` `outer.jsonl` `development_check_output` records:
  - stage `lint`: "collected 1589 items"
  - stage `green`: "collected 1590 items"
  - stage `red`: 1589, with `test_verify_adherence_semantic.py .FFFFFF`, i.e. 7 tests

The lint run therefore collected the pre-green test count, without `test_frozen_live_acceptance_record`. `docs/2026-10-14-adherence-semantic.md:66–68` presents it as the branch's lint result.

This matters for one reason: `tests/test_worktree_predicate_ratchet.py` is in the lint set, and the PR adds `tests/fixtures/adherence-semantic/scripts/check-tree.sh` containing the forbidden `[ -f .git ]`. From the retained record I cannot tell whether that ratchet saw the fixture. If the ratchet were to fire on the fixture, the branch's own lint gate would fail.

A `make lint` run at HEAD 00c5a33 would settle it.

### F6. The ticket closure timestamp precedes the evidence it cites

- **Severity:** nonblocker
- **Confidence:** high
- **Tag:** `verifiable:`

The closed ticket's log line reads `2026-10-14T08:47Z Minh Ha-Duong closed — implemented`. Its "Implementation evidence" section cites SHA `e457cd8e…`, which first appears at `outer.jsonl` ordinal 395 (`2026-10-14T08:55:31Z`). The accepted run ended at `08:56:57Z` (`evidence.json` `accepted_run.end_utc`).

Either the closure was recorded before acceptance existed, or the log timestamp is wrong. The log also attributes the closure to the author, while an agent did the work. Correct the timestamp; the attribution is the author's call.

### F7. A violation that touches no rule file still skips phase 3

- **Severity:** nonblocker
- **Confidence:** high
- **Tag:** `nofollow:` Under `SKILL.md` §3 (+207–+209), phase 3 is required only when the diff touches a rule or instruction file, "OR architectural concerns remain uncovered". The second clause is a judgment call left to the outer seat.

The fixture had to append `Apply this rule…` to `rules/worktrees.md` to trigger the review. A code-only diff carrying the same `[ -f .git ]`, like the original PR 212 case in the ticket context, can still be recorded as `skipped`. The ticket's criteria scope this to "a rules-touching diff", so this is outside the PR. The `/hunt` label skip (`verify:adherence-passed`) also bypasses phase 3 entirely. I record both for the audit trail.

## What held up under attack

- **Worker distinctness and completion are real.** The launch record (`exec_chunk` `30f9e1`, session 59913) and completion (`bb4003`, exit 0) appear in `outer.jsonl`. The result UUID `a3c3477a-…` and session ID match across `evidence.json` and `worker.jsonl`. The model identity comes from runtime `modelUsage`; the worker's self-report is not used.
- **The invalid attempt was not laundered into acceptance.** It is kept and labelled invalid with `adherence-infrastructure`. The worker that returned `route: null (reviewer ran inline…)` had its self-report ignored, and the outer process records were used instead, as the contract requires.
- **Runner discovery from ticket 0953 is untouched.** The phase 1 text is unchanged.
- **The RED record exists.** The red check record shows 6 contract assertions failing on the old skill before the repair.

## Verdict

**comment**

All three original exit criteria are met by a completed, distinct, routed worker, and the overall result is FAIL. None of the findings invalidates that.

The accepted run's "neutral/fresh" framing (F1) and its unshown rule discovery (F2) are overstated. The contract still lets the outer seat author or upgrade findings, which the evidence shows happening once (F3). The retained lint result predates the final tree (F5), and the closure timestamp precedes its own evidence (F6).

F1, F3 and F5 are worth fixing before merge: either reword the doc or add one sentence to the contract, and rerun `make lint` at HEAD.