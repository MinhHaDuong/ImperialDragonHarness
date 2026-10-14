# PR1389 correctness review: ticket 1080 at HEAD 00c5a333

**Seat:** code-reviewer, correctness perspective. The orchestrator records reviewer identity and cost.
**Inputs reviewed:** all twelve changed paths, taken from the diff supplied in the launch prompt. I also checked the stored live evidence (`evidence.json`, `outer.jsonl`, `worker.jsonl`) against the three original exit criteria.

## Exit criteria assessment

| # | Criterion | Assessment |
|---|-----------|------------|
| 1 | Phase 3 trigger matches this harness's `rules/` path. A rules-touching diff always launches the worker or records why it did not. | **Met in contract and in the live run.** The skill no longer hard-codes `.claude/rules/*.md`. Rule locations are discovered from `AGENTS.md` and `CLAUDE.md` plus the `rules/` and `.claude/rules/` trees (`skills/verify-adherence/SKILL.md:198-205`). Phase 3 is required when a rule or instruction file is touched, and a skip needs a recorded reason (`:207-211`). In the live fixture, a change under `rules/` triggered phase 3 (`evidence.json` `accepted_run.semantic_review.reason`). |
| 2 | The verdict states whether phase 3 ran and which worker served. | **Met.** The schema adds a `semantic_review` block with fields for applicability, status, worker id, model, family, effort, route, and launch and completion evidence. A required semantic review with any status other than `ran` must fail (Verdict mapping paragraph after the §4 schema). The accepted run fills these fields from runtime records rather than from the worker's own claims: worker id from `session_id`, model from `modelUsage.canonicalModel`. |
| 3 | A fixture whose rules state the 0310 rule, with the violation in the diff and no caller hint, is flagged by the semantic path with `file:line`. | **Met in substance.** The accepted worker prompt (`worker.jsonl:6`) contains only the sources, the diff and the skill's prompt text, with no hint about the defect. The worker on its own returned `scripts/check-tree.sh:3`, `severity: blocking`, and a non-empty `suggested_test` (`worker.jsonl:7`). The runner passed (`make syntax`, exit 0), and the overall verdict is `adherence: FAIL` with `escalation: null`. The worker session (`0df0c0b2…`) is a different session from the outer one (`01a13990…`). |

The fail-closed paths also behave correctly. The first attempt omitted severity. It was later re-labelled from `ran` to `invalid` + `adherence-infrastructure` (`outer.jsonl:36`, `evidence.json` `prior_attempts[1]`). It was not kept as a pass with severity filled in by the outer seat. That matches the rule "a valid completed worker alone earns `status: ran`" (`SKILL.md:245`).

## Findings

### F1: The retained `make lint` output is from an earlier tree than the final test module. Minor, high confidence.
`verifiable:` The lint record at `outer.jsonl:56` shows `collected 1589 items`. The green `check-fast` record at `outer.jsonl:55` shows `collected 1590 items`, and the RED record at `outer.jsonl:54` also shows 1589. RED ran 7 tests from `test_verify_adherence_semantic.py` (`.FFFFFF`); green ran 8. So `make lint` was captured before `test_frozen_live_acceptance_record` existed. After that come commits `a6a05e41` (the consistency edits to the skill) and `00c5a333`, and no gate output is retained for them. The doc says "`make lint` passed 185 tests" (`docs/2026-10-14-adherence-semantic.md`, Verification). That is accurate for the run it describes, but it does not describe HEAD. CI or the pre-merge gate has to rerun lint and check at HEAD. The retained records cannot vouch for HEAD.

### F2: The "fresh" final invocation was a continuation of the same outer session, and the retained records do not show rule discovery being redone. Minor, medium confidence.
`verifiable:` `evidence.json` `outer.worker_id` = `01a13990-…`, which is the `session_meta` id at `outer.jsonl:1` (ordinal 0). The final run starts at `outer.jsonl:37` (ordinal 392) in that same session, with no new `session_meta`. By then the outer seat had already seen the earlier runs' finding at `check-tree.sh:3`.

The final prompt builder (`outer.jsonl:41`) does three things from memory instead of from evidence in this run:
- It hard-codes the file list `['AGENTS.md','rules/worktrees.md','Makefile','scripts/check-tree.sh']`.
- It tells the worker "no other instruction or rule files exist". That statement was established in `/tmp/idh-1080-live`, not in the final worktree `/tmp/idh-1080-live-final`.
- It reports the runner declaration `AGENTS.md:4`, but no record of reading `AGENTS.md` in the new worktree precedes it.

The worker still received no hint about the defect, so criterion 3 stands. But the doc's phrase "A fresh complete neutral fixture invocation validates the resulting skill version" overstates what happened. The outer seat was warm and carried discovery over from earlier turns. Suggested fix: say so in the doc, or redo the run with a cold outer session.

### F3: No retained record shows the `route` skill being loaded. Minor, medium confidence.
`consider:` The new contract requires choosing the route "from the loaded `route` skill" and recording "the launch line before launch" (`SKILL.md:213-217`). The evidence's route field says "loaded route grid economical cluster; Claude detached cross-family transport". No `outer.jsonl` record reads `skills/route/SKILL.md` or the route cache. The launch was a foreground `claude -p` exec followed by polling, not the detached panel transport. The sanitization note leaves out only "unrelated runtime instructions", which should not cover reading the route skill. Either the read happened and was removed by sanitization, or the route field is a claim nothing in the records backs up.

### F4: The contract test's `rules/` case never went RED. Nit, high confidence.
`verifiable:` In the RED output (`outer.jsonl:54`), `test_verify_adherence_semantic.py .FFFFFF` shows that the first parameter, `"rules/"`, passed against the old skill. `"rules/"` is a substring of `.claude/rules/`, which the old phase 3 text already contained (`tests/test_verify_adherence_semantic.py:13`). The case named after the change that matters most for criterion 1 does not catch a return to the `.claude/rules/`-only trigger. The live run is the only real evidence for that change. A sharper assertion would forbid the old trigger, for example `"Only runs if any `.claude/rules/*.md`" not in semantic`, or would check for the discovery sentence.

### F5: The frozen-evidence hash check only proves that `evidence.json` agrees with itself. Nofollow, high confidence.
`nofollow:` `tests/test_verify_adherence_semantic.py:26` hashes `evidence["loaded_skill"]["source"]` and compares the result with the stored sha. Anyone who edits the source text and recomputes the hash passes. The ticket's Test section limits frozen records to "prove this run only", so this is by design. On reading, the stored source matches the HEAD `SKILL.md` text, but I did not hash it.

### F6: The skill does not say whether one rejected finding invalidates the whole worker report. Nit, medium confidence.
`consider:` `SKILL.md:236-245` says "Reject hypotheticals and unsupported anchors" and "malformed or unanchored output → `status: invalid`". The circuit breaker says to "reject the output" when `file:line` or `suggested_test` is missing. In the earlier valid run, the outer seat dropped one worker nit that had an anchor but no support, and kept `status: ran` (`evidence.json` `earlier_valid_run…validation.rejected_finding`). That reading is reasonable, but it is not written down. Another outer seat could treat any rejected finding as `invalid` and fail closed with an infrastructure escalation. One sentence would settle it, for example "drop individual unsupported findings; the report is `invalid` only when it lacks valid evidence for reviewed rules".

### F7: The ticket was closed before the final accepted run and before review. Nofollow, high confidence.
`nofollow:` In `tickets/closed/1080-…erg`, the log shows the ticket closed at `2026-10-14T08:47Z`. The final accepted run was at `08:55–08:56Z`. The "Implementation evidence" section cites that run's hash `e457…`, so the body was edited after the close entry. Action 4 says "Open a PR, then review and verify all original criteria", yet the criteria are already checked `[x]` before this panel reports. This is a process ordering issue only. It does not change the code under review.

## Summary

The skill contract repair is correct and internally consistent. Rule discovery now covers `rules/`, phase 3 has explicit applicability and status, the verdict records the worker's runtime identity, and unavailable or invalid workers fail closed. The live evidence supports all three exit criteria. The semantic worker was a separate completed Claude Haiku session, given no hint about the defect, and it returned a blocking finding at `scripts/check-tree.sh:3`. The overall verdict is `FAIL`.

The weak points are in how the evidence is described, not in the skill:
- The retained gate output predates HEAD (F1).
- The final run is called fresh, but it reused a warm outer session and carried rule discovery over from earlier turns (F2).
- No record shows the route skill being loaded (F3).

None of these makes the acceptance result wrong, so none is a blocker. Before merge, the gate needs a fresh `make lint` / `make check` at HEAD, as F1 says.

**verdict: comment**