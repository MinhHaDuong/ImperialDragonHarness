# Scope review: ticket 1080 live semantic acceptance (PR1389)

**Reviewed:** HEAD `00c5a33352d23d75a08f5d3bf2c50b011be48635` as named in the launch prompt. I did not verify that SHA, since I had no tools. Review is against the supplied full diff (12 paths) and the original ticket exit criteria.

## 1. Roster and scope

| Path | Status | Ticket roster item / exit criterion |
|---|---|---|
| `skills/verify-adherence/SKILL.md` | modified, body only | Action 2 (EC1, EC2). Frontmatter unchanged, since hunks start at line 26. |
| `tests/test_verify_adherence_semantic.py` | new | Action 1 (supplementary) |
| `tests/fixtures/adherence-semantic/{AGENTS.md,Makefile,rules/worktrees.md,scripts/check-tree.sh}` | new (4) | Action 3 fixture |
| `docs/2026-10-14-adherence-semantic.md` | new | Action 3 record |
| `docs/adherence-semantic/{evidence.json,outer.jsonl,worker.jsonl}` | new (3) | Action 3 evidence |
| `tickets/1080-…erg` | deleted | ticket closure |
| `tickets/closed/1080-…erg` | new | ticket closure |

- The 12 paths match the planned roster exactly. The optional RED-trace path was not added; the RED output went into `outer.jsonl` instead.
- No new dependency, no catalog change, and no change to Phase 1 declaration discovery. Phase 1.0, Phase 1, and the Protocol section are untouched.
- Scope creep is limited to unrelated wording churn (see F5).

**Exit criteria, against the retained evidence**

- **EC1, trigger matches the harness rules path.** Met for one case. The accepted run records `applicable: true`, `rule_sources: [AGENTS.md, rules/worktrees.md]`, and a worker launch. The skip branch and the deleted-rule branch are not exercised live, and the contract tests check only wording.
- **EC2, verdict states phase 3 status and worker.** Met. The `semantic_review` block carries `status`, `worker_id`, `launch_evidence`, and `completion_evidence`.
- **EC3, fixture flagged with file:line and no caller hint.** Met for the retained run, subject to F3. The worker output carries `scripts/check-tree.sh:3`, `severity: blocking`, and a non-empty `suggested_test`. The global verdict is FAIL with no escalation. The rejected earlier attempts are retained and labelled as invalid.

## 2. Findings

**F1. Ticket closure is dated before the evidence it cites, and attributed to a named person on an unmerged PR. Blocking. Confidence: high on the facts.**
- `tickets/closed/1080-…erg:5` reads `Closed: implemented`. Line 9 reads `2026-10-14T08:47Z Minh Ha-Duong closed — implemented`.
- The "Implementation evidence" section cites SHA `e457cd8e…`, the final skill hash. That hash first appears in the retained record at `outer.jsonl`, the record with ordinal 395 (`2026-10-14T08:55:31Z`).
- The final accepted run runs 08:55:31 to 08:56:57. The closure entry predates both.
- The closure is written as a human action, but the PR is not merged and nothing in the record shows the author closing it.
- Fix: either remove the closure log line and `Closed:` field until merge and integration review (`rules/workflow.md` ticket discipline), or have the author confirm the entry and its timestamp.

**F2. Non-native annotations sit inside files described as native execution records. Minor. Confidence: high.**
- The doc calls `outer.jsonl` and `worker.jsonl` "sanitized native execution extracts".
- Native records carry `timestamp` and `ordinal`. Several hand-written records do not, including `validation_correction`, `selfgate_disposition_correction`, the three `development_check_output` records, and both `*_turn_token_usage` records.
- The `validation_correction` record also documents a verdict the outer had earlier accepted without an explicit worker severity.
- `verifiable:` the `outer.jsonl` records named above lack `timestamp`/`ordinal`. Fix: move annotations and check output to a separate file, or label them as annotations in the doc.

**F3. The outer launch prompt is not retained, so "no caller hint" cannot be checked from the artifacts. Minor. Confidence: medium.**
- The ticket requires invoking the complete skill with branch/worktree only.
- `outer.jsonl` starts at `session_meta` and turn context. The user or launch message is absent.
- The outer read `SKILL.md` with `cat` (ordinal 10 and ordinal 395), then performed each phase by hand, including `make syntax`, diff generation, and the worker prompt.
- The record does not show a harness fork or skill-tool invocation. The worker prompt was composed by the outer, including the statement "Complete rule universe is AGENTS.md and rules/worktrees.md."
- `consider:` retain the verbatim outer launch message and state how the skill was invoked. Whether the hand-run sequence counts as "complete skill invocation" is a judgment for the author.

**F4. The frozen test does not tie the evidence finding to the worker's output. Minor. Confidence: high on the test lines.**
- `tests/test_verify_adherence_semantic.py:33–35` checks the finding's severity, file, and line against `evidence.json`, not against the worker's JSON.
- Lines 42–43 check `"blocking" in actual_report` and `"suggested_test" in actual_report`. Both substrings appear in the raw result regardless of the finding.
- An edited `evidence.json` finding at another line would still pass. The test name and docstring overstate what is proven.
- `consider:` parse `completed["result"]` and compare its `semantic_findings[0]` to `accepted["semantic_findings"][0]`.

**F5. Unrelated wording churn in `SKILL.md`. Minor. Confidence: high.**
- The diff renames "PR" to "merge request" at the `Enforce the project's declared rules…` sentence. That is outside the ticket's scope.
- `nofollow:` the churn is harmless. Revert in a later cleanup, or leave it.

**F6. Evidence is larger than the ticket's "compact" requirement. Minor. Confidence: medium.**
- `evidence.json` carries the full `SKILL.md` source in `loaded_skill.source`, and `outer.jsonl` carries the file three times through `cat` outputs.
- `nofollow:` acceptable for an audit trail. The ticket's "compact evidence" wording is not met literally.

**F7. A rule-violating script is committed under `tests/fixtures/`. Minor. Confidence: low.**
- `tests/fixtures/adherence-semantic/scripts/check-tree.sh:3` contains `[ -f .git ]`, the predicate the 0310 rule forbids.
- The retained lint run (185 passed) includes the worktree predicate ratchet, so it apparently excludes fixtures. I did not read the ratchet's scope and did not verify that exclusion.
- `consider:` confirm the ratchet's glob excludes `tests/fixtures/`, so a future cleanup does not flag or remove the fixture.

## 3. Verdict

**request-changes.** The only blocker is F1, the closure entry. It is narrow and cheap to fix. Once it is resolved, the remaining findings are comment-level. The live evidence supports the claimed outcome for this one run: a distinct worker completed, and the verdict is FAIL with a blocking anchored finding.

**Limits:** I read only the supplied diff and anchors. I did not run the test suite or verify the hashes independently. I did not verify the worker's family against my own; the orchestrator should record reviewer identity and family for this seat.