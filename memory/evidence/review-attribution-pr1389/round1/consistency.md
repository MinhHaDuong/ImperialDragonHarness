# PR1389 review: consistency (ticket 1080) at HEAD 00c5a33352d23d75a08f5d3bf2c50b011be48635

**Seat:** code-reviewer, consistency perspective. Read-only. I judged the twelve changed paths in the supplied diff against the original exit criteria of ticket 1080 and the Raid 1080 additions, and checked the stored live evidence against the prose claims made about it.

## Summary

The skill repair is internally consistent:

- **Rule discovery:** phase 3 now discovers rules from `AGENTS.md`, `CLAUDE.md`, `rules/` and `.claude/rules/` (`skills/verify-adherence/SKILL.md` §3).
- **Verdict mapping:** the phase 3 statuses `ran | skipped | unavailable | invalid` line up with the §4 schema and with the verdict-mapping paragraph.
- **Circuit breakers:** they still agree with the new `invalid` status, which is used for output lacking `file:line` or `suggested_test`.

The stored live evidence mostly matches the prose:

- The final worker session `0df0c0b2…` and result UUID `a3c3477a…` are the same in `evidence.json`, `worker.jsonl` and `outer.jsonl:48`.
- The launch chunk `30f9e1` (`outer.jsonl:42`) and completion chunk `bb4003` (`outer.jsonl:46`, exit 0) are present.
- Durations and costs agree: 16.648 s / $0.00469613 for the final worker, 20.946 s / $0.0143562 for the earlier valid worker, $0.00491546 for the invalid one.
- The worker's model comes from `modelUsage.canonicalModel` rather than from its own self-report.

All three original exit criteria are supported by a live run that used a distinct worker and returned an anchored blocking finding with an overall FAIL. The findings below are drift between artifacts plus one test that checks nothing. None is a blocker.

## Findings

### 1. The `"rules/"` contract parameter passes on the unfixed skill
- **Where:** `tests/test_verify_adherence_semantic.py:13`
- **Severity:** nit. **Confidence:** high.
- **Tag:** verifiable: the retained RED run (`outer.jsonl:54`) shows `tests/test_verify_adherence_semantic.py .FFFFFF`. The first parameter, `rules/`, passed against the old text, because `` `.claude/rules/*.md` `` already contains the substring `rules/`.
- **Effect:** exit criterion 1 is "trigger matches this harness's `rules/` path". This parameter cannot detect a regression back to `.claude/rules/` only. Only the frozen live run supports that criterion.
- **Fix:** assert a token that only the new text has, for example ``Include existing conventional `rules/` and``.

### 2. The `make lint` evidence comes from an earlier tree, not the final branch
- **Where:** `docs/2026-10-14-adherence-semantic.md:~76` ("`make lint` passed 185 tests"), compared with `outer.jsonl:56` and `outer.jsonl:55`.
- **Severity:** nit. **Confidence:** medium.
- **Tag:** verifiable: the lint record collects `1589 items`, the same total as the RED run. The green `check-fast` run (`outer.jsonl:55`) collects `1590`, after `test_frozen_live_acceptance_record` was added. So the lint run predates the final test module and the later evidence edits.
- **Effect:** the reported counts are real, but no retained gate output corresponds to HEAD 00c5a33. The ticket's step 4 also names "the normal pre-PR project gate", and no `make check` output is retained.
- **Fix:** the next gate should re-run on the rebased HEAD and not rely on these records.

### 3. "Fresh" invocation, but the same outer session ran it
- **Where:** `docs/2026-10-14-adherence-semantic.md:~82` ("A fresh complete neutral fixture invocation") and `evidence.json` `outer.worker_id`.
- **Severity:** nit. **Confidence:** high.
- **Tag:** verifiable: `outer.jsonl:1` names session `01a13990…`, and the final run continues that session at ordinals 392–446 (`outer.jsonl:37–51`). That session had already seen the `check-tree.sh:3` finding in earlier turns (`outer.jsonl:34–35`).
- **Effect:** the worker prompt itself contains only sources and the diff, with no defect hint, so the worker stays neutral. The outer seat does not: it already knew the defect. "Fresh" overstates this; "a new turn in the same outer session" is accurate.

### 4. No retained record shows the outer model for the final turn
- **Where:** `docs/2026-10-14-adherence-semantic.md:~53–54` ("The outer native session ran Sol 6.1 at medium effort, as observed in the runtime `turn_context`").
- **Severity:** nit. **Confidence:** medium.
- **Tag:** verifiable: `turn_context` records exist only at `outer.jsonl:2`, `:6` and `:22` (ordinals 7, 30, 133). None exists at or after ordinal 392, where the final run (turn `01a1399f…`, `outer.jsonl:53`) took place.
- **Effect:** for the accepted run the doc states the outer identity as observed, but no observed record backs it. Under the skill's own standard, "observed" needs a record.
- **Fix:** add the final turn's `turn_context` to the extract, or qualify the claim.

### 5. The final run's retained trace shows a hard-coded rule list, not rule discovery
- **Where:** `outer.jsonl:41`, the prompt builder with `for f in ['AGENTS.md','rules/worktrees.md','Makefile','scripts/check-tree.sh']` and the assertion "Complete rule universe is AGENTS.md and rules/worktrees.md".
- **Severity:** nit. **Confidence:** medium.
- **Tag:** consider: no discovery command between ordinals 392 and 413 is retained. The earlier run cites a `discovery_record: 6679ea`, but that record is not in `outer.jsonl` either. The extract is sanitized, so discovery may have happened and been omitted.
- **Effect:** `evidence.json` `semantic_review.rule_sources` reads as discovered, but the stored trace does not show discovery taking place. Criterion 1's "discover the harness rules path" is shown as an assertion, not observed.

### 6. Two different texts are called the accepted verdict
- **Where:** `evidence.json` `accepted_run.semantic_findings[0]` (~line 66–74) and `outer.jsonl:51` (`outer_final`).
- **Severity:** nit. **Confidence:** high.
- **Tag:** verifiable:
  - `evidence.json` keeps the raw worker text: `rule_section: "rules/worktrees.md: Worktree identity (0310) — …"`, and a `suggested_test` starting with a grep over `scripts/ rules/`.
  - The outer's emitted verdict at `outer.jsonl:51` normalizes this to `rules/worktrees.md#worktree-identity-0310` and a different `suggested_test` ("initialize an ordinary repository and assert…").
- **Effect:** two texts both present themselves as the accepted verdict. The raw `rule_section` also does not follow the schema's `<project-rule-path#section>` form. The earlier run was ruled `invalid` for one missing schema field (severity), while this deviation passed. The standard is applied unevenly, even though the anchor, severity and test are all present.

### 7. The ticket closes before the run it cites
- **Where:** `tickets/closed/1080-…erg:9` (`2026-10-14T08:47Z … closed — implemented`) and the "Implementation evidence" section (~lines 115–120).
- **Severity:** nit. **Confidence:** high.
- **Tag:** verifiable: the closure cites SHA `e457cd8e…` and the final run. `evidence.json` `accepted_run.start_utc` is `2026-10-14T08:55:31`, eight minutes after the close timestamp.
- **Fix:** bump the log timestamp, or add a log line for the final acceptance.

### 8. Evidence key names differ inside `evidence.json`
- **Where:** `evidence.json` `accepted_run.phase1_0` (~line 26) and `earlier_valid_run.accepted_run.phase_1_0` (~line 112). The accepted run also stores the runner under `mechanical_runner`, while the outer verdict uses `phase_1`.
- **Severity:** nit. **Confidence:** high.
- **Tag:** nofollow: this is cosmetic. The test reads only `mechanical_runner`.

### 9. The stored suggestion for the final run is flawed as written
- **Where:** `evidence.json` `validation.suggestion_limitation`.
- **Severity:** nit. **Confidence:** high.
- **Tag:** nofollow: the PR already discloses that the grep over `rules/` would match the rule's own text, and it names the behavioral test as the usable alternative.
- **Effect:** for the ratchet, the stored suggestion cannot be adopted unchanged; a follow-up needs the behavioral variant.

## Items checked with no finding

- **Skill hash:** the embedded `loaded_skill.source` in `evidence.json` matches HEAD `SKILL.md` on every hunk I compared: "merge request" wording, `project-rule-path` placeholders, the §3 and §4 text. The frozen hash test validates the snapshot only, as the doc says.
- **Fixture reconstruction:** the doc's reconstruction recipe agrees with the final worker prompt's base/head diff. The base script uses `set -euo pipefail` and the rule is the 5-line version plus one appended line.
- **Invalid attempt:** the `invalid` attempt is recorded as `FAIL` with `adherence-infrastructure`, which matches the new contract.
- **Scope:** phase 1 runner discovery (ticket 0953) is unchanged, consistent with the ticket's decision not to reopen it.

**Verdict: comment.** No blocker. Findings 1 and 2 are the ones worth fixing before merge: one test parameter is vacuous, and no retained gate output covers the final tree. The rest is evidence drift worth tidying.