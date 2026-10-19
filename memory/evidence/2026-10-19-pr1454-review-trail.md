# PR 1454 review trail

Audience: public. Public repository, public PR sources/reviews and non-secret runtime identity facts only.

Merged PR: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1454
Merge: 3cf4e52bb60e272c775177d14e51da439472ce99; final reviewed code: c952ed92b6058bb0e2f23ad24baac03bda8bfeab; close-only head: bc8a72bf8801b232cf891837532750f020be94a4.

OpenAI identities below were read from session_meta.model_provider and turn_context.model/effort, not self-reports or launch aliases. Anthropic identities were read from actual result.modelUsage canonicalModel/provider; observed effort and a separate model revision were not exposed. Requested effort was medium.

The five round-one E2BIG dispatch failures never started a reviewer process or model context. Their actual model identity therefore does not exist; these are dispatch events, not invented reviewer contexts. All five failed dispatches are retained below. Permission review rejected two launches over a private-export premise; repository private:false/public evidence allowed approved retries; rejected launches did not execute.

- Observed Codex context root: session 01a152e8-f4a9-7480-88c1-189ccc6b4d51; provider `openai`; model `gpt-6.1-sol`; effort `low`.
- Observed Codex context /root/imagine1117: session 01a152e9-cfe2-7180-b28e-f911f052b0df; provider `openai`; model `gpt-6-luna`; effort `medium`.
- Observed Codex context /root/blind1117: session 01a152ea-58bc-7800-8f95-fa6dfadcdc06; provider `openai`; model `gpt-6-luna`; effort `medium`.
- Observed Codex context /root/plan1117: session 01a152eb-507f-74e2-9804-f05e359e71b1; provider `openai`; model `gpt-6-luna`; effort `medium`.
- Observed Codex context /root/feasible1117: session 01a152ec-5e55-7f43-b396-dc582e9b4863; provider `openai`; model `gpt-6-luna`; effort `medium`.
- Observed Codex context /root/execute1117: session 01a152ed-d256-7850-a8f0-03ad1199888f; provider `openai`; model `gpt-6.1-sol`; effort `medium`.
- Observed Codex context /root/execute1117/adherence1117: session 01a152f0-02e4-7d51-9454-896cf235cac9; provider `openai`; model `gpt-6.1-sol`; effort `medium`.
- Observed Codex context /root/gaze_review1454: session 01a15309-2cd2-7980-8e51-29c2c83f7eb2; provider `openai`; model `gpt-6.1-sol`; effort `low`.
- Observed Codex context /root/gaze_adherence1454: session 01a15309-4765-73c1-b5d3-e97f60e9f27b; provider `openai`; model `gpt-6-luna`; effort `medium`.
- Observed Codex context /root/gaze_pr1454: session 01a15309-6eb7-7f13-b08e-81bd02348648; provider `openai`; model `gpt-6.1-sol`; effort `low`.
- Observed Codex context /root/gaze_adherence1454/adherence_semantic1454: session 01a1530b-d8a3-7863-b115-74e3b82a1dc6; provider `openai`; model `gpt-6-luna`; effort `medium`.
- Observed Codex context /root/simplify1454: session 01a1530f-0451-7e02-914f-0dcdf004c499; provider `openai`; model `gpt-6.1-sol`; effort `low`.
- Observed Codex context /root/gate1454: session 01a15310-2784-7502-b05c-accd3bdd6579; provider `openai`; model `gpt-6.1-sol`; effort `medium`.
- Observed Codex context /root/integration1117: session 01a15312-72bf-73c0-9199-6fdac336a1c2; provider `openai`; model `gpt-6-luna`; effort `medium`.

## Failed dispatch events

- consistency.failed: `[Errno 7] Argument list too long: 'claude'`; no process/model started.
- correctness.failed: `[Errno 7] Argument list too long: 'claude'`; no process/model started.
- doc-propagation.failed: `[Errno 7] Argument list too long: 'claude'`; no process/model started.
- red-team.failed: `[Errno 7] Argument list too long: 'claude'`; no process/model started.
- scope.failed: `[Errno 7] Argument list too long: 'claude'`; no process/model started.

## Native review runtime header

```text
OpenAI Codex v0.163.0
--------
workdir: /home/haduong/.agents/.claude/worktrees/review-1454
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: low
reasoning summaries: none
session id: 01a15309-7ecf-7092-92b3-df3503b4b40e
--------
user
```

## round1/correctness

Runtime identity:
```json
{
  "head": "51407e128dbab759cd53f2a666d69a9522e72a48",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "c166355c-db14-4343-ba4c-ab047d27ebfd",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 12994,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 83721,
      "webSearchRequests": 0,
      "costUSD": 0.1187542,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 11299,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1187542,
  "elapsed_seconds": 63.7,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

I can't write `/home/haduong/.agents/.claude/worktrees/raid-1117/.panel/1454/correctness.md` from this seat: I have no file or shell tools, so the report below is my output. The seat process needs to transport it. I did not run the suite. I used only the supplied diff, the full sources, and the author's reported checks (fast967, lint186, full1702passed3skipped, shell matrix green), which I have not verified.

## Correctness review: PR #1454 (ticket 1117)

**Scope:** `skills/merge/erg-pr-merge` (`no_checks_required`), `skills/merge/SKILL.md`, `tests/test_erg_pr_merge.sh` (stub and 1117 loop), ticket 1117.

**Outcome matrix, checked by reading the code:**

| Branch endpoint | Rules endpoint | Result | Evidence |
|---|---|---|---|
| 200 valid, empty | 200 valid, empty | direct merge (unchanged) | `erg-pr-merge:445-463`, `:465-478` |
| 403 | 200 valid, empty | ordinary merge | `:457-459` sets `inspection_denied=1`, rules still inspected |
| 200 valid, empty | 403 | ordinary merge | `:472-474` |
| 403 | 200 with required check | refuse | `:465-471` runs regardless of branch denial; covered by `denied-required-rule`, `tests/test_erg_pr_merge.sh:677` |
| 200 with required | any | refuse | `:446-456` dies before rules is read |
| 403 | malformed | refuse | covered by `denied-malformed-rule`, `:678` |
| 500 / 404 / 401 | any | refuse | `:460-463`, `:475-478`; covered by `legacy500`, `rule500`, `legacy404`, `rule401` |
| 403 | 403 | ordinary merge, no `--admin` | `:479-483`; `both` case plus `--admin` assertion at `tests/test_erg_pr_merge.sh:691` |

The null-rollup and failing/pending-check controls run before this function, so they are unchanged. A null rollup still dies at `erg-pr-merge:442-443`.

**Refusal recovery:** The ticket close is pushed before the direct merge, and the retry path skips the close when the ticket is already archived with a `Closed:` header (`erg-pr-merge:338-341`). The retry test asserts only that no second close commit is added (`tests/test_erg_pr_merge.sh:698-702`).

**Findings**

1. **consider:** `erg-pr-merge:445` and `:465` capture `gh api ... 2>&1`, so any stderr on a successful call is merged into the JSON that `jq` parses. Before this change, stderr went to the terminal. A warning on a successful response now produces "returned invalid protection data" and a false refusal. This fails closed, so it is not a safety issue. The stubs print nothing on stderr for successful calls, so the suite cannot catch it. Hypothesis, not reproduced. Confidence: medium. Suggested check: a stub that writes a warning to stderr with exit 0 on the branch endpoint, expecting a direct merge.

2. **consider:** `erg-pr-merge:457` and `:472` treat any error containing `(HTTP 403)` as a permission or plan denial. A secondary rate-limit 403 from `gh` would also take this path. The forge still enforces requirements on the ordinary merge, so the risk is low, but the SKILL wording "permission or plan restriction" is narrower than the matching. Confidence: medium.

3. **consider:** The refusal-recovery assertion is weak. The retry at `tests/test_erg_pr_merge.sh:698-699` runs with `STUB_DIRECT_REFUSED` unset, so the stub would merge, but the test never checks the retry's exit or merge attempt. It proves only "no second close commit", not "retryable to merge". Confidence: high that the assertion is weak; the behaviour itself is not shown wrong.

4. **nofollow:** The success-path assertions (`tests/test_erg_pr_merge.sh:693-694`) do not check that the "Branch-rule inspection denied" diagnostic was printed. Audit only.

5. **nofollow:** Ticket 1117 ticks the exit criterion "regression tests and ticket-only PR gate pass" before merge. These are the author's claims, which I have not verified.

**Verdict: comment.** I found no blocker. Every outcome combination I traced fails closed or delegates only the unknown requirements to the forge. Finding 1 is the one to check before merge, since it could cause false refusals on a successful response.

**Reviewer record:** correctness perspective, read-only. Model: Claude Haiku 5.5 (`claude-haiku-5-5`). The decorrelation and family question belongs to the router (`skills/route/references/decorrelation.md`). I have not checked that. No tools were used, and no unavailable evidence beyond the points above.

## round1/consistency

Runtime identity:
```json
{
  "head": "51407e128dbab759cd53f2a666d69a9522e72a48",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "077609ee-cdd3-491b-b629-798c0134e464",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 7216,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 83708,
      "webSearchRequests": 0,
      "costUSD": 0.1042962,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 5519,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1042962,
  "elapsed_seconds": 39.0,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

I could not write `/home/haduong/.agents/.claude/worktrees/raid-1117/.panel/1454/consistency.md`. This session has no file-write tool, and the seat process must do the atomic `.part`-then-rename transport. The report follows inline so the seat process can carry it.

# Consistency review: PR #1454 (base 37dda89d, head 51407e12)

Read-only. No tools, no commits, no forge posts. Evidence is limited to the supplied diff and full sources.

## Findings

**F1. consider, medium confidence.** `tests/test_erg_pr_merge.sh:697-702`, the "closed ticket remains retryable" PASS.
The retry runs without `STUB_DIRECT_REFUSED`, so the stub forge accepts that merge. The only assertion is that the commit count is unchanged, and the ticket is already closed, so that holds whatever the retry does. The retry's merge outcome is never checked, so the label overclaims retryability. Suggested fix: set `STUB_DIRECT_REFUSED=1` on the retry and assert the refusal text and the unchanged commit count.

**F2. consider, medium confidence; outside my consistency perspective.** `skills/merge/erg-pr-merge:445` and `:465`.
Both inspections capture `2>&1`, so any stderr that `gh` writes on a successful call is concatenated into the JSON that `jq` parses at `:446` and `:466`. That would turn a successful read into "invalid protection data" and a refusal. The stubs never write stderr on success, so the suite cannot see this. A verifiable test would have the success stub print a warning to stderr and expect a clean merge. Confirm the `gh` behaviour before acting; I could not check it here.

**F3. nofollow, high confidence.** `skills/merge/SKILL.md:140-141`.
"(legacy protection and rulesets both inspected)" is no longer true when an endpoint is denied. The next sentence amends it, so this is a wording drift only. Suggested fix: "(legacy protection and rulesets inspected; a denied endpoint is delegated, see below)".

**F4. nofollow, medium confidence.** `skills/merge/erg-pr-merge:480`.
The message "Branch-rule inspection denied (HTTP 403)" also fires when the legacy branch-protection endpoint is the one denied. In the script, "branch-rule" otherwise means the rulesets endpoint (`:465`, and the "effective branch rules" wording at `:433`). Suggested fix: "Branch-protection or branch-rule inspection denied".

## Clean checks (with evidence)

- **Naming.** `STUB_LEGACY_HTTP`/`STUB_RULE_HTTP` follow the existing `STUB_LEGACY_*`/`STUB_RULE_*` pattern (`tests/test_erg_pr_merge.sh:138-151`). All are forwarded through `run_merge` (`:269-271`).
- **Error-string contract.** The script matches `*"(HTTP 403)"*` (`erg-pr-merge:457`, `:472`), and the stub emits the same token (`test:139`, `:151`). Real `gh` output is unverified here.
- **Doc ↔ code, refusal side.** SKILL.md:143-147 ("other inspection errors and malformed successful data still refuse") matches the die paths at `erg-pr-merge:456`, `:462`, `:471`, `:477`.
- **Doc ↔ code, delegation side.** SKILL.md:143-146 matches the `inspection_denied` branch at `:479-483`. The fallback comment at `:486-492` matches it too.
- **Ticket ↔ tests.** Each ticket exit criterion has a matching scenario in the loop at `test:662-707`. The "refused" scenario covers the forge-refusal criterion.
- **Ticket checkboxes.** The `[x]` marks in `tickets/1117-…erg:51-68` are consistent with the diff. The Raid sections match the implemented scope (4 planned paths).
- **Test style.** The unnumbered `Ticket 1117` loop is consistent with the unnumbered 1082/0872-series blocks.

## API outcomes and refusal recovery

- **API outcomes covered:** both-403, each endpoint alone, 500, 404, 401, mixed denied with known-required or malformed data (`test:662-680`).
- **Refusal recovery:** covered by the `refused` scenario, but the retry assertion is weak (F1).

## Unavailable evidence

- I did not run the test suite, `erg check`, or the lint/full gates. I rely on the author's reported counts (fast967, lint186, full1702 passed 3 skipped) without verifying them.
- I could not check how real `gh` formats a 403 error or whether it writes to stderr on success (F2).
- No live forge behaviour was observed.

## Verdict

**comment.** No consistency blockers. F1 and F2 are worth resolving before merge; F3 and F4 are wording-only.

## round1/scope

Runtime identity:
```json
{
  "head": "51407e128dbab759cd53f2a666d69a9522e72a48",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "4a6326db-9486-4978-8953-667eb4765b46",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 10165,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 83709,
      "webSearchRequests": 0,
      "costUSD": 0.11166970000000001,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 8466,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.11166970000000001,
  "elapsed_seconds": 50.6,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Review report: PR #1454, ticket 1117 (read-only code-reviewer seat)

**Scope:** ticket intent only. I reviewed the supplied diff and full sources as given. I ran no tools and made no writes. The report is output only; the seat process handles transport to `.panel/1454/scope.md`.

**Unavailable evidence:** I did not execute the test suite, shell matrix, or lint. The author's counts (fast 967, lint 186, full 1702 passed / 3 skipped, shell matrix green) are taken as reported, not verified. I have no live `gh` output, so the `(HTTP 403)` string format is checked only against the stub, which the diff itself authored.

## Findings

**F1. Retry assertion cannot distinguish a working retry from an aborted one.** (confidence: high that the assertion is weak; medium that it matters)
- `tests/test_erg_pr_merge.sh:697-703`: the retry runs with `|| true`, and the only assertion is that the commit count is unchanged.
- If the retry died at the branch guard, or at the close step, the count would still be unchanged and the test would print PASS.
- The retry also does not set `STUB_DIRECT_REFUSED`, so it should succeed through the direct merge. The test never checks that, so it does not prove the "remains retryable" invariant (ticket lines 60 and 67–68).
- Suggested fix, in the same test: assert the retry exits 0, its log contains a `--merge` attempt, and the ticket stays closed. Use a positive control to show the assertion can fail.
- Tag: `consider:`. The current code appears correct by reading (HEAD stays on the PR branch because `die` at `erg-pr-merge:563` precedes Step 4), so this is a test-strength gap, not a shown failure.

**F2. The 403 match also catches rate-limit and abuse-limit 403s.** (confidence: medium)
- `skills/merge/erg-pr-merge:457` and `:472` treat any error text containing `(HTTP 403)` as a permission or plan denial.
- A secondary rate limit also returns 403. The script would then proceed to an ordinary merge with the base's requirements unknown.
- Mitigation: the forge still enforces required checks on the ordinary merge, so this is not a bypass. The concern is fidelity to the ticket's "recognize HTTP 403 specifically" intent.
- Tag: `consider:`.

**F3. `2>&1` folds stderr into the success payload.** (confidence: medium)
- `erg-pr-merge:445` and `:465` capture stdout and stderr together. On success, any stderr warning makes the following `jq -e` fail, and the script refuses with "invalid protection data".
- Before this diff, stderr went to the terminal and did not affect the parse.
- This fails closed, so it is safe, but it is a new refusal path on a successful inspection. Capturing stderr separately would avoid it.
- Tag: `consider:`.

**F4. Wording and comment drift.** (confidence: high)
- The "Branch-rule inspection denied" message at `erg-pr-merge:480` also covers legacy branch protection, which the endpoint at `:445` inspects.
- The comment block at `erg-pr-merge:431-435` wraps awkwardly, with the new sentence running into the old one.
- Tag: `nofollow:`.

## Checks I could confirm by reading

- **Denied and non-403 paths are separated correctly.** Success is validated first. A 403 sets `inspection_denied=1`. Any other failure dies. `erg-pr-merge:445-478`.
- **Known requirements and malformed data still refuse.** Mixed scenarios are covered: denied-required-rule, denied-required-legacy, denied-malformed-rule, denied-malformed-legacy. Their stub inputs fail the `jq` predicates at `:446-456` and `:466-471`. Test rows at `tests/test_erg_pr_merge.sh:677-680`.
- **No admin bypass.** The diff adds no `--admin`. The test loop asserts its absence in every scenario (`test:691-692`).
- **Failing, pending, and null-rollup controls remain.** These are unchanged. Tests at `:786-812` and the pending cases at `:1282-1312` still exercise them.
- **Refusal recovery.** The forge refusal path dies at `erg-pr-merge:563` with the ticket close already pushed, so the close remains retryable. The strength of the retry check is the F1 issue above.
- **Documentation matches code.** `skills/merge/SKILL.md:140-147` describes the 403 delegation, malformed-data refusal, and the retryable close. The ticket's Exit criteria map to the scenarios above.

## Verdict

**comment**

The core change matches the ticket intent. Non-403 errors, malformed data, known required checks, and failing or pending checks still refuse. There is no admin path. F1 is the test I would tighten before merge. F2 and F3 are robustness questions for the author. None of them is a blocker on my reading.

## round1/red-team

Runtime identity:
```json
{
  "head": "51407e128dbab759cd53f2a666d69a9522e72a48",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "127a1d44-5183-4747-9394-47e3b3028d08",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 20013,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 83722,
      "webSearchRequests": 0,
      "costUSD": 0.1363027,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 17780,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1363027,
  "elapsed_seconds": 100.8,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Red-team report: PR #1454 (ticket 1117)

**Scope:** public exact material only (diff, `erg-pr-merge` at head 51407e12, `tests/test_erg_pr_merge.sh`, SKILL.md, ticket 1117). No tools were run, so nothing below was executed. Findings are from reading the code and stubs. I have not written the artifact file; the seat process transports this text.

## Findings

### B1 (blocker, confidence: medium): a 403-marked inspection can hide known required rules

- **Evidence:** `skills/merge/erg-pr-merge:465` captures the rules call as one string with `--paginate 2>&1`. Stdout (page JSON) and stderr (the error text) are merged. `:472` then matches `(HTTP 403)` anywhere in that string and sets `inspection_denied=1` without parsing the captured JSON. `:479-483` proceed to the ordinary merge.
- **Why it matters:** The feasibility note (ticket 1117, "Raid Feasibility") requires that "one denied endpoint cannot hide known required checks … from the other." This path violates that by construction. If `gh api --paginate` emits a page of `required_status_checks` rules on stdout and then fails on a later page with a 403, the known requirement is discarded. The same applies to the branches call at `:445` with the legacy `required_status_checks` payload.
- **Reproduction (predicted, not run):** Legacy endpoint returns 200 with no required checks. The rules stub prints `[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"required"}]}}]` to stdout, prints `gh: … (HTTP 403)` to stderr, and exits 1. Predicted result: the merge is issued. Required result: refusal.
- **Test gap:** The stubs at `tests/test_erg_pr_merge.sh:149-152` and `:138-140` never emit partial JSON together with a 403. The matrix at `:662-707` has no such row.
- **Fix direction:** Keep stdout and stderr separate. Validate any captured payload before honouring a 403, and add the partial-payload row to the matrix.
- **Reachability:** Depends on `gh` streaming page output before a page error. The code path itself is certain. Verdict-relevant because it breaks the stated invariant.

### C1 (consider, confidence: medium): the 403 detector conflates rate limits with permission or plan denial

- **Evidence:** `skills/merge/erg-pr-merge:457` and `:472` match any 403. GitHub secondary rate limits can also return 403. `:480` and `skills/merge/SKILL.md:143` describe the case as "permission or plan restriction."
- **Impact:** Bounded, because the forge still enforces its requirements. The message is wrong, and a transient failure now merges where it used to refuse.

### C2 (consider, confidence: medium-low): detection depends on one gh error-text format

- **Evidence:** `:457` and `:472` match the literal `(HTTP 403)`. The stubs at `tests/test_erg_pr_merge.sh:139` and `:151` emit only that format.
- **Impact:** If gh prints `HTTP 403:` instead, the denial is treated as an unknown error and the script dies. That is fail-closed, but the test would not catch the drift.

### C3 (consider, confidence: low): success path now captures stderr

- **Evidence:** `:445` and `:465` use `2>&1` on calls whose success output is parsed as JSON. Any stderr noise on success makes `jq -e` fail, which turns a success into a refusal at `:456` or `:471`.
- **Impact:** Fail-closed regression risk only. Separating the streams would remove it.

### C4 (consider, confidence: medium): the "retryable" test does not test a retry that merges

- **Evidence:** `tests/test_erg_pr_merge.sh:697-702`. The retry runs without `STUB_DIRECT_REFUSED`, so the refusal is not reproduced. Its merge log goes to `/dev/null` and its exit is discarded (`|| true`). The only assertion is that the commit count is unchanged.
- **Impact:** The PASS message "closed ticket remains retryable" overstates what is checked. The test shows only that a re-run is idempotent. Note that the idempotency check passes trivially for any script that skips already-archived tickets.

### C5 (consider, confidence: medium): claim that GitHub enforces unseen requirements is unverified

- **Evidence:** `skills/merge/SKILL.md:145-146` ("GitHub enforces any unseen requirements"). No live forge evidence is in scope. A bypass-listed actor's ordinary merge may skip rulesets; the script cannot observe that either way.
- **Impact:** The trust boundary now rests on forge behaviour that is neither tested nor observable here.

### N1 (nofollow): the invariant holds on the non-403 and pending paths

- `merge_directly_or_die` returns to `no_checks_required` only when the rollup is empty (`:499-500`). Failing and pending checks die before that (`:504`, `:506-508`). Null rollups are refused at `:443`.
- No `--admin` flag is introduced. The merge invocations at `:561-567` are unchanged.

### N2 (nofollow): exit criteria ticked on stub evidence only

- `tickets/1117-…erg:51-54` and `:64-68` are marked `[x]`. The exit criterion "a normal, non-admin merge when the forge accepts it" is supported only by stubs. No live forge run is in evidence.

### N3 (nofollow): refusal message does not say retry is safe

- `:563` and `:566` die with "merge failed and PR is not merged." SKILL.md:146-147 says the close "remains retryable," but the message does not say so.

## Refusal recovery

- The close is pushed at `:376`, before the merge attempt. A forge refusal therefore leaves the ticket closed on the branch and the PR unmerged.
- A retry takes the already-archived path (`:335-341`) and adds no commit. This is idempotent, but see C4 for what is not shown.

## Author checks

fast967, lint186, and full1702 passed / 3 skipped, plus the shell matrix, are author-reported. I did not reproduce them. Evidence unavailable: any execution, live GitHub responses, and gh's actual error formats.

## Verdict

**request-changes**, on B1. The fix is small: keep stdout and stderr apart, validate any captured payload before a 403 is honoured, and add the partial-payload row to the matrix.

## round1/doc-propagation

Runtime identity:
```json
{
  "head": "51407e128dbab759cd53f2a666d69a9522e72a48",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "947cb3a8-8684-4e33-ae5e-70227538c43c",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 8836,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 83716,
      "webSearchRequests": 0,
      "costUSD": 0.1083542,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 7083,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1083542,
  "elapsed_seconds": 62.2,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Doc-propagation review: PR #1454 (ticket 1117 fallback)

**Seat:** code-reviewer, doc-propagation perspective. Read-only, no tools used. I did not write the file. Transport to `/home/haduong/.agents/.claude/worktrees/raid-1117/.panel/1454/doc-propagation.md` is for the seat process.

**Scope:** `skills/merge/SKILL.md`, the `erg-pr-merge` comments and `no_checks_required` / `merge_directly_or_die`, `tests/test_erg_pr_merge.sh` cases 1117 and 14b/875, and ticket 1117. Base `37dda89d`, head `51407e12`, all from the supplied public diff.

**Not verified:** I ran no tests, no `gh` calls, and no lint or gate. The author's counts (fast967, lint186, full1702passed3skipped, shell matrix green) are unconfirmed here. No live forge run exists in the evidence, so the claim that GitHub refuses or accepts the ordinary merge as described is untested.

## Findings

**1. `consider:` (confidence medium).** `SKILL.md:140-141` still says "with required checks configured it refuses instead." The new text at `SKILL.md:143-147` and the code say "known" requirements. With one endpoint denied and the other silent, an unseen legacy requirement is not refused by the script. The direct attempt goes to the forge, which refuses it. The adjacent sentence is therefore incomplete. Suggest "known required checks" to match `erg-pr-merge:431-435`.

**2. `consider:` (confidence high that the coverage is partial).** `SKILL.md:145-146` says "a forge refusal is reported and the pushed ticket close remains retryable." The test at `tests/test_erg_pr_merge.sh:696-702` checks only that the commit count is unchanged after the retry. The retry at `:698-699` omits `STUB_DIRECT_REFUSED`, and its output and exit are discarded (`|| true`, `>/dev/null`). So the test does not show that a retry reaches the merge or reports a result. The doc claim is supported only for "no duplicate close commit."

**3. `consider:` (confidence medium).** `SKILL.md:135-139` says that after a `close: no ticket found` retry, "do not re-run it … finish with a direct forge merge." `SKILL.md:143-146` now says a refusal is retryable by re-running. Readers could take the older bullet as a route after a 403 refusal, which bypasses the script. `SKILL.md:123-125` forbids that blanket fallback. A cross-reference would remove the ambiguity. The two symptoms differ, so this is not a contradiction.

**4. `consider:` (confidence medium).** The matcher at `erg-pr-merge:457` and `:472` depends on the literal `(HTTP 403)` in `gh` stderr. The stub at `tests/test_erg_pr_merge.sh:138-139` and `:150-151` emits the same literal, so the tests are self-consistent but do not use real `gh` output. `SKILL.md:143` describes the behavior accurately relative to the matcher. Capturing one real `gh` 403 transcript would settle whether the match holds.

**5. `nofollow:`** The ticket title "handle unavailable branch-rule inspection" covers both endpoints, which the implementation handles. Ticket `tickets/1117-...erg:51-68` ticks its Verification and Exit-criteria boxes, including "ticket-only PR gate pass." I cannot confirm that gate result. The 4-path count at ticket line 95-96 matches the diff.

**6. `nofollow:`** The header of `erg-pr-merge:15-26` says "merge directly only when the one-shot rollup read shows every check done." That is still true for the rollup. The new 403 decision is a branch-rule decision and does not need to appear there.

## Checked and consistent

- `SKILL.md:143-147` matches the code. A 403 on one endpoint validates the other (`erg-pr-merge:445-478`). Non-403 errors and malformed successful data die (`:461-463`, `:477`).
- Both-denied, legacy-only, rule-only, forge-refused, 500, 404, 401, and mixed required or malformed cases are all in the matrix (`tests/test_erg_pr_merge.sh:662-707`). Their expected results match the doc.
- The no-admin invariant holds. `--admin` appears nowhere in the change, and the test asserts it at `:691-692`.
- Failing-check, pending-check, and null-rollup refusals are retained (`:800-812`, `:786-798`, and case 14/31).
- Ticket close stays recoverable, matching the ticket invariant.

## Unavailable evidence

- No live GitHub or `gh` run. The 403 behavior and "GitHub enforces unseen requirements" (`SKILL.md:146`) rest on the stubs and the author's report in the ticket context.
- No reproduction of the author's check counts or the shell matrix.

## Verdict

**comment.** No blocking documentation defect. Findings 1–4 are wording or coverage gaps that the author may dismiss.

## Round 1 synthesis and dispositions

Review-pr round 1 — head 51407e128dbab759cd53f2a666d69a9522e72a48

Panel: 185 changed lines, 4 files, skills/merge pipeline paths; high-risk merge gate, all five perspectives. All five completed through real Claude headless sessions. Runtime canonical model claude-haiku-5-5, firstParty, Anthropic family; producer OpenAI. Effort requested medium, observed effort unavailable. Read-only supplied source review; no live forge merges. PANEL-INTEGRITY: COMPLETE; dissent: red-team requests changes.

Blocker [red-team]: skills/merge/erg-pr-merge:465–474 discards partial successful rules pages when a later page returns 403. Confirmed by invoking the actual no_checks_required function with a partial required-rule JSON page followed by HTTP 403: it returned 0 and permitted ordinary merge. This violates the requirement to preserve known checks. Fix by separating streams and refusing partial non-error payloads on denied inspection.

consider: [correctness, consistency, scope] skills/merge/erg-pr-merge:445,465 combines stderr with successful JSON; warnings can trigger false refusal. Add a success-warning regression and separate stderr.
consider: [all perspectives] tests/test_erg_pr_merge.sh:697–703 ignores retry exit and merge attempt. Assert actual successful retry plus no extra close commit.
consider: [doc-propagation, consistency] skills/merge/SKILL.md:140–147 should distinguish known requirements, describe HTTP403 generally, and clarify symptom-specific recovery. Match log wording to both endpoint types.
consider: [red-team, doc-propagation] exact gh error formatting and live forge behavior are not independently tested. The ticket's HTTP403 policy deliberately delegates configured requirements to the ordinary forge operation; no admin flag is added.

Validation on this head: full make check 1702 passed, 3 skipped in54.72s; fast967, lint186; merge shell suite passes; all ten forge checks pass. Raw seat reports and runtime identity records retained locally for the orchestration gate.

Verdict roster:
correctness: comment
consistency: comment
scope: comment
red-team: request-changes
doc-propagation: comment

Panel API spend: $0.579377 (runtime-reported list basis).


## round2/correctness

Runtime identity:
```json
{
  "head": "42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "1ce8de86-a182-4ddc-930c-45238c41fc07",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 23299,
      "cacheReadInputTokens": 649,
      "cacheCreationInputTokens": 87990,
      "webSearchRequests": 0,
      "costUSD": 0.02925419,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 21612,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.02925419,
  "elapsed_seconds": 111.9,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Correctness review: PR #1454 (erg-pr-merge inspection denial), round 2

**Seat:** correctness (read-only). **Scope:** supplied diff, supplied full sources, and the ticket text. I did not run the suite, query the forge, or read any file outside that material. Author-reported counts (fast 967, lint 186, full 1702 passed / 3 skipped, shell matrix green) are unverified here.

## Verdict: comment

No blockers. Under my seat charter I do not approve or gate; approval belongs to other seats.

## Checked and found correct

- **Stream separation.** Both inspections capture stderr to a temp file and read stdout alone (`erg-pr-merge:446-451`, `481-486`). Success warnings therefore cannot corrupt the JSON that `jq -e` / `jq -se` reads. The warning scenario (`test_erg_pr_merge.sh:138`, `152`; loop at `680`) would fail if stderr leaked into stdout.
- **API outcome matrix.** Success is validated as before. A 403 is accepted only with an empty body or one ordinary error object (`erg-pr-merge:468-476`, `498-506`). Any other failure dies (`477-478`, `507-508`). I traced `jq` precedence in the `keys - [...] | length == 0` expression; it parses as intended.
- **Partial paginated pages.** A successful page followed by a 403 yields two slurped elements, so `length == 1` fails and the run refuses (`erg-pr-merge:498-504`). The `partial` scenario (`test:679`, `705-719` path) exercises this and would fail if the check were removed.
- **Known requirements under denial.** A denied endpoint cannot hide a configured requirement on the other endpoint: the `denied-required-*` and `denied-malformed-*` scenarios (`686-689`) die as expected.
- **No bypass.** No `--admin` appears in the script; the loop asserts absence (`test:700-701`).
- **Refusal recovery.** The stub's direct-merge refusal is verified via `test:705-714`. The retry adds no commit and merges. Ticket close is archived on the first run and the second run takes the "already closed" path (`erg-pr-merge:333-341`), so the retry is idempotent.

## Findings

**F1: consider** (confidence high that the gap exists; risk medium)
Ticket invariant "failing and pending checks still prevent direct merge" is not tested in combination with an inspection denial. Non-empty rollups route to `merge_directly_or_die`'s failing and pending branches before `no_checks_required` is reached (`erg-pr-merge:530-539`), so the code is correct by structure. But no scenario in `test_erg_pr_merge.sh:669-690` sets `STUB_ROLLUP` to a failing or pending value while a 403 is injected. A single case would pin this.

**F2: consider** (confidence high on the gap)
The empty-body 403 branch is not exercised. `erg-pr-merge:468` skips validation when `branch_now` is empty, but every stub 403 emits a JSON body (`test_erg_pr_merge.sh:140`, `155`). An empty-stdout case would cover that branch.

**F3: consider** (confidence low; live forge not exercised)
A real plan-gate 403 body carrying an extra key (for example `errors`) fails `keys - [message, documentation_url, status] | length == 0` (`erg-pr-merge:472-473`, `501-503`). That would refuse, failing closed, on exactly the case the ticket targets. I cannot confirm the real GitHub body shape without a live forge, which was not requested.

**F4: nofollow**
The `legacy500` and `rule500` stubs still print the 403 JSON body and then report "HTTP 500" on stderr (`test_erg_pr_merge.sh:139-141`, `153-156`). The classifier keys only on stderr (`erg-pr-merge:464`, `494`), so the mismatch is harmless. Recorded for the audit trail.

**F5: nofollow**
Wording in `skills/merge/SKILL.md`:
- Lines 146-150: "This retry applies to a forge refusal after the close was pushed" is ambiguous about which retry is meant.
- Lines 143-144: a sentence breaks mid-clause ("it" ends a line, "validates…" starts the next).

## Not flagged

Treating any HTTP 403 as a delegation trigger, including rate-limit 403s, is the author's documented intent per the ticket. I did not raise it.

## Unavailable evidence (stated plainly)

- I did not run `tests/test_erg_pr_merge.sh`, lint, or the full gate. The pass counts are the author's.
- I did not verify the real `gh` stderr format or the real 403 body shape (F3). The `(HTTP 403)` substring match is fail-closed if the format changes, but I could not observe that.
- I did not verify the forge's behaviour on a direct merge that races the close-commit push.

## round2/consistency

Runtime identity:
```json
{
  "head": "42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "d8040f1e-264d-4ca1-bb46-34519907e949",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 28751,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 86637,
      "webSearchRequests": 0,
      "costUSD": 0.1610627,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 26423,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1610627,
  "elapsed_seconds": 129.8,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Consistency review: PR #1454 (ticket 1117), read-only seat

I have no write tool, so this report is my output for the seat process to transport to `.panel/1454/consistency.md`. I reviewed only the supplied diff and FULL SOURCE blocks at the head commit `42200d45`. I ran nothing and did not re-raise the round-1 findings, which the current code resolves.

## Findings

**F1: consider.** Confidence high. `skills/merge/erg-pr-merge:465-467` says "A failed paginated call can already have emitted successful pages." The branch-protection call at `:448` has no `--paginate`, so that rationale is false there. The comment was copied from the rules branch at `:495-497`, where it is true.

**F2: consider.** Confidence high. `tests/test_erg_pr_merge.sh:139-141` and `:153-156` print a JSON body with `"status":"403"` on stdout for every `STUB_*_HTTP` value. So the non-403 scenarios `legacy500`, `rule500`, `legacy404`, and `rule401` (`:682-685`) get a body that claims 403 while stderr reports 500, 404, or 401. The script still refuses correctly because it keys on stderr `(HTTP 403)` at `erg-pr-merge:464` and `:494`. A body-keyed regression would be caught, but the fixture misrepresents those cases. Emit the body only when the stub HTTP code is 403.

**F3: consider.** Confidence medium. `skills/merge/SKILL.md:149-150` says "This retry applies to a forge refusal after the close was pushed." The script does not retry. The caller re-runs it, as the test at `:705-714` does. The sentence also sits under `:132`, which says "Do not re-run it" for the other symptom. Name the action explicitly: re-run the script, the archived ticket is skipped, and no second close commit is added (see `erg-pr-merge:335-343`).

**F4: consider.** Confidence medium. `no_checks_required` (`erg-pr-merge:436`, called at `:531`) now returns success when a requirement check was denied and is unknown. The name, and the comment at `:431-435`, still say "no checks required." Rename it, or state in the comment that a denied inspection is included.

**F5: consider.** Confidence high. The empty-body guards at `erg-pr-merge:468` and `:498` have no scenario. Every 403 stub prints a body (`tests/test_erg_pr_merge.sh:139-141`, `:153-156`), so an inspection denial with empty stdout is untested. Add a stub option that prints no body on 403.

**F6: nofollow.** Confidence high. The two 403 blocks at `erg-pr-merge:446-479` and `:481-515` are near-identical, with about 35 duplicated lines each, including the comment. A small helper taking the endpoint and output variable would remove the duplication.

**F7: nofollow.** Confidence high. The final PASS summary at `tests/test_erg_pr_merge.sh:1343` lists each feature the file covers and does not mention denial delegation.

**F8: nofollow.** Confidence medium. The ticket's planned-paths line (`tickets/1117-…erg:95-96`) counts "this ticket" as one of "4 paths." Line `:102` then calls them "four planned content-bearing paths." The diff touches four files including the ticket, so the wording is inconsistent.

**F9: nofollow.** Confidence high. The terms drift: "direct merge" in `erg-pr-merge:432` and `:591` and in test names `:716`, versus "ordinary merge" or "ordinary, non-admin merge" in `SKILL.md:145`, the message at `erg-pr-merge:511`, and the ticket. Pick one.

**F10: nofollow.** Confidence high. `SKILL.md:143-144` hard-wraps mid-clause, leaving "restrictions), it" on a short line. Reflow it with the paragraph.

**F11: nofollow.** Confidence high. The ticket citation at `erg-pr-merge:435` reads "(tickets 0200/0871)" but omits 1117, although the rule changed. The 1082 citation at `:518` shows the file's convention.

## Checked and clean

- **jq predicates** (`erg-pr-merge:469-473`, `:499-503`): the parenthesisation is correct. The `keys - [...]` subset check, the `tostring` on `.status`, and the `length == 1` slurp all behave as intended.
- **set -e safety:** every new gh call sits in `||` or an `if` (`:448`, `:483`), and the `(( … ))` tests are inside `if` conditions. `tests/test_erg_pr_merge.sh` uses the same rule. No `((x++))` was added, per `rules/coding-bash.md`.
- **Stream separation:** stderr is captured separately and forwarded on success (`:446-451`). The `warning` scenario (`:680`, stub at `:138`, `:152`) runs the success path with stderr noise.
- **Temp files:** each capture is removed before the jq checks (`:450`, `:485`), so no `die` path leaks one.
- **No bypass:** no `--admin` appears in the script or the diff. The test at `:700-701` asserts its absence.
- **Refusal recovery:** the `refused` scenario (`:681`) and the retry at `:705-714` assert exit 0 and an unchanged commit count. The retry's second close is skipped by `erg-pr-merge:335-343`.
- **Stub env allowlist:** `run_merge` (`:274-279`) passes every new `STUB_*` variable.
- **Conventions:** the test follows the file's `fail=1` and `PASS:`/`FAIL:` idiom and its table-loop style. `STUB_LEGACY_HTTP` and `STUB_RULE_HTTP` match the existing `STUB_LEGACY_*` and `STUB_RULE_*` naming.
- **Ticket and matrix:** the checkboxes (`tickets/1117-…erg:51-68`) match the test coverage. Raid Plan item 3 (`:90-91`) maps to the scenario table (`tests/test_erg_pr_merge.sh:669-690`).

## Unavailable evidence

- I did not execute the suites or the lint. The counts you supplied (fast 967, lint 186, full 1702 passed and 3 skipped, shell matrix green) are unverified by me.
- I did not check the live `gh` stdout and stderr shape for a 403. That was out of scope, and the ticket's fail-closed stance covers it.
- I did not check docs outside the supplied material, so stale references elsewhere are unverified.

## Verdict

**comment.** There are no blockers. The findings are documentation accuracy (F1, F3, F4), fixture fidelity (F2), and one coverage gap (F5). The rest are style nits.

## round2/scope

Runtime identity:
```json
{
  "head": "42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "5f4bfd5f-ef7a-4bea-bc62-751ea9c988e6",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 22943,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 86638,
      "webSearchRequests": 0,
      "costUSD": 0.1465437,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 20828,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1465437,
  "elapsed_seconds": 108.2,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Code-review seat report: PR #1454, ticket 1117 (round 2)

**Scope:** ticket intent only. Read-only review of the supplied diff and full source. I ran no tests and no shell commands, and I did not write any file. Transport to `.panel/1454/scope.md` is the seat process's job.
**Reviewer identity:** code-reviewer seat, Claude Haiku 5.5 (self-reported). I cannot confirm the author's model family, so I do not claim independence.

## Checked and holding

- **Stream separation.** Stdout and stderr are captured separately (`skills/merge/erg-pr-merge:446-451`, `483-486`). Success-path warnings no longer reach the JSON parser.
- **Partial pages on 403.** The rules endpoint runs with `--paginate`. A required-check page followed by a 403 yields two JSON values, so `length == 1` fails and the script dies (`erg-pr-merge:498-505`). The `partial` scenario covers this (`tests/test_erg_pr_merge.sh:679`).
- **Cross-endpoint hiding.** A denied endpoint cannot mask required checks or malformed data from the other. The `denied-required-*` and `denied-malformed-*` scenarios cover both directions (`tests/test_erg_pr_merge.sh:686-689`).
- **No `--admin`.** The merge commands carry no admin flag. The loop asserts this for every scenario (`tests/test_erg_pr_merge.sh:700-701`).
- **Non-403 errors refuse.** 500, 404 and 401 die before any merge (`tests/test_erg_pr_merge.sh:682-685`).
- **Refusal recovery.** After a forge refusal, the retry merges, and the branch commit count is unchanged, so no second close commit is added (`tests/test_erg_pr_merge.sh:705-714`). The retry path is genuinely taken: the archived ticket with its `Closed:` header is skipped at `erg-pr-merge:338-341`.
- **Scope.** The diff touches exactly the four planned paths in the ticket.

## Findings

**1. consider (confidence: medium). Residual bypass when inspection is denied.**
When both endpoints return 403, the script cannot see `enforce_admins` or ruleset bypass actors (`erg-pr-merge:448-479`, message at `:510-511`). An ordinary `gh pr merge --merge` by an actor the forge lets bypass will merge with no checks. The old code refused here. The ticket's invariant says "no bypass of the forge's configured merge requirements," which holds only if a forge-configured bypass counts as forge enforcement. That is the author's call. I am recalling GitHub's bypass behaviour from memory and have not verified it here. Suggest the author state the residual in `SKILL.md`.

**2. consider (confidence: high). The empty-stdout 403 path is untested.**
The `if [[ -n "$branch_now" ]]` and `if [[ -n "$rules_now" ]]` skips (`erg-pr-merge:468`, `:498`) have no scenario. The stub always prints an error body on 403 (`tests/test_erg_pr_merge.sh:139-141`, `:153-156`). Real `gh` may print nothing on stdout for a 403, so this is the more likely live shape. Add a scenario with empty stdout.

**3. consider (confidence: medium). Classification keys on the gh stderr suffix.**
`(HTTP 403)` is matched as text (`erg-pr-merge:464`, `:494`). If gh changes that text, 403s become refusals. That fails closed, so it is a rot risk, not a safety hole.

**4. consider (confidence: high). The forge-enforcement claim is modelled, not tested.**
`STUB_DIRECT_REFUSED` (`tests/test_erg_pr_merge.sh:114-116`) is a flag. It does not consult the configured requirements. The suite proves refusal propagation and the absence of `--admin`. It does not prove that GitHub enforces unseen requirements. The live forge was not exercised, as the author noted.

**5. consider (confidence: low). One coverage gap.**
No scenario combines a 403 on one endpoint with a non-403 error on the other, such as legacy 403 with rules 500 (`tests/test_erg_pr_merge.sh:669`).

**6. nofollow. Stub fidelity and warning guard.**
The stub prints a status-403 body for every HTTP code (`tests/test_erg_pr_merge.sh:139-141`, `:153-156`). Classification is stderr-based, so the 500/404/401 cases still discriminate. The warning scenario (`:138`, `:152`) guards against a future stream merge. It does not discriminate the current code.

**7. nofollow. Wording in `skills/merge/SKILL.md`.**
- Lines 143-145 break mid-sentence ("it" / "validates").
- Line 145 "non-admin" can be read as "the user is not an admin". "Without `--admin`" is what is meant.
- Line 140 bullet title "Empty rollup on a repo with no checks" now also covers the denied-inspection case.
- Lines 135-139 say "Do not re-run it", while lines 147-150 say the close stays retryable. The retry test (`:705-714`) shows re-running works for this case, so the older bullet should be scoped to its own symptom.

**8. nofollow. Duplication.**
The two 403-validation blocks (`erg-pr-merge:464-476`, `:494-506`) are near-identical. A helper would be a refactor, not a requirement. The charter asks me to avoid overengineering, so I do not recommend one.

## Verdict

**comment.** No blockers. I found no path where a required check, malformed successful data, or a partial page lets the merge through without the forge enforcing it. Finding 1 is the item the author should decide on explicitly.

## Unavailable evidence

- No test run. The author's counts (fast967, lint186, full 1702 passed / 3 skipped, shell matrix) and the ticket's `[x]` boxes are unverified here.
- No real gh 403 transcript, so the stdout and stderr shapes are assumed from the stub.
- No live forge exercise, which was not requested.

## round2/red-team

Runtime identity:
```json
{
  "head": "42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "f77806f3-2d79-4291-952f-44b9bb0c15dd",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 25217,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 86651,
      "webSearchRequests": 0,
      "costUSD": 0.1522417,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 23263,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1522417,
  "elapsed_seconds": 122.7,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

I could not write `/home/haduong/.agents/.claude/worktrees/raid-1117/.panel/1454/red-team.md`: this session has no file-write tool, and the seat process must transport the artifact. The report follows verbatim so the seat process can capture it.

---

# Red-team report: PR #1454 (ticket 1117), round 2

Scope: supplied diff and full source for `skills/merge/erg-pr-merge`, `skills/merge/SKILL.md`, `tests/test_erg_pr_merge.sh`, and ticket 1117. Read-only. No tests run, no live forge, no `gh` version check.

## Clean areas (evidence from supplied source)

- **Partial-page rejection.** Both 403 paths use `jq -se` with `length == 1` (`erg-pr-merge:469-473`, `:498-503`). Any successful page printed before a denial makes the slurp length 2 or more, so the script dies. A truncated page fails the jq parse and also dies.
- **Stream separation.** Stderr goes to a temp file (`:448`, `:483`). The success path is keyed on `api_status` (`:452`, `:487`), not on stderr content. The `warning` scenario covers this (test `:138`, `:152`, `:702-703`).
- **Non-403 failures and malformed success data still refuse.** `:477-478` and `:507-508` die on any other nonzero status. Malformed success data dies at `:453-463` and `:488-493`.
- **No bypass.** No `--admin` appears anywhere in the script. Test `:700-701` asserts this for every scenario.
- **Pending and failing checks are untouched.** `merge_directly_or_die` reads the rollup and refuses on failing or pending checks before `no_checks_required` is reached (`:530-535`).
- **Refusal recovery.** The close commit is pushed before the merge is attempted (`:351-376`, `:575`). On retry the archived ticket with a `Closed:` header takes the no-op branch (`:338-341`), so no second close commit is created. Test `:705-714` asserts the commit count is unchanged and that the retry merge is issued.
- **Bash invariants.** `set -euo pipefail` is unchanged (`:29`). `|| api_status=$?` is safe under `set -e`. Locals are declared. `[[ -z ]] || printf` is a safe `||` list.

## Findings

**F1. consider (medium).** The denial path hands the decision to the forge for every requirement it cannot see. `erg-pr-merge:510-514` and the `:452` comment say GitHub enforces unseen requirements. Forge bypass for bypass-capable actors (classic `enforce_admins` off, or ruleset bypass lists) can let a plain `gh pr merge --merge` succeed where a fully inspected path would refuse. Nothing in the suite models this, and the stubs cannot. The author's premise (no protection, Pro account) is unverified here. Hypothesis, not demonstrated.

**F2. consider (high confidence in the code path, low impact).** Any HTTP 403 is treated as "inspection denied" (`:464`, `:494`). That includes secondary rate-limit 403s, which are transient and not a permission signal. The message at `:511` ("inspection denied") would then mislabel the cause. The outcome stays safe, since the forge still enforces and a rate-limited merge will likely fail anyway.

**F3. consider (medium).** Negative controls assert only exit status and whether a direct merge was attempted (`test:715-717`, and the `:704-718` branch). They do not assert the refusal reason. A refusal from an unrelated crash would pass. Permissive mutations are caught, because positive scenarios and the `result`/`direct` checks fail. Adding reason assertions such as `*"partial or invalid"*` or `*"required"*` would close the gap.

**F4. consider (medium).** Matrix gap. There is no case for a denial on one endpoint combined with a non-403 failure on the other (for example legacy 403 plus rules 500). Reading `:494-509` and `:477-478`, that combination refuses, but no test pins it. Malformed 403 bodies with extra keys are also untested (`:470-473`).

**F5. nofollow.** `SKILL.md:140-142` still says the script merges "when the base has no required checks", which is now only true for the non-denied path. Lines `:143-144` have a stray line break. The sentence at `:147-150` ("This retry applies to a forge refusal after the close was pushed, rather than the separate ... symptom") is ambiguous. The ticket marks its own exit criteria `[x]` before merge (`tickets/1117:51-68`); that is self-certification, not evidence.

**F6. nofollow.** Detection depends on gh's literal `(HTTP 403)` stderr format and the error-body shape. A format change fails closed, because the code dies at `:477-478` and `:507-508`. The author has already accepted this.

## Verdict

**comment**

No blockers found in the supplied code. The API-outcome handling, partial-page rejection, and refusal recovery match the ticket's stated invariants as far as the source shows. F1 is the substantive question for the author to answer: whether forge bypass for bypass-capable actors is acceptable under the "no bypass" invariant.

## Unavailable evidence

- No live forge run and no `gh` output samples, so the stderr and body format assumptions are unverified against the real CLI.
- I did not run `tests/test_erg_pr_merge.sh`. The author's counts (fast967, lint186, full1702 passed, 3 skipped, shell matrix green) are not reproduced.
- I could not inspect the actual git diff, only the supplied text.
- I could not write the report file; the seat process must transport this text to the `.panel/1454/red-team.md` path.

## round2/doc-propagation

Runtime identity:
```json
{
  "head": "42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "921ba075-bfcb-4478-8544-804aff1740e3",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 14019,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 86645,
      "webSearchRequests": 0,
      "costUSD": 0.12424070000000001,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 12030,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.12424070000000001,
  "elapsed_seconds": 70.6,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Doc-propagation review: PR #1454 (ticket 1117)

**Scope:** Downstream fallback documentation accuracy against the supplied code, tests, and ticket at head `42200d45`. Read-only, from the supplied material only. I had no tools, so nothing was executed and no repository was read beyond what was pasted. The author-reported results (fast967, lint186, full 1702 passed 3 skipped, shell matrix green) are not independently verified.

I have no file-write tool in this session, so this report is my output for the seat process to transport to `.panel/1454/doc-propagation.md`.

## Findings

**F1. Retry guidance contradicts itself on the refusal-recovery path.** Confidence: high that the text conflicts; medium that it misleads in practice. Tag: `consider:`
- `skills/merge/SKILL.md:130-134` says the script "is *not* idempotent past that step" and "Do not re-run it". This is the `close: no ticket found` bullet.
- `skills/merge/SKILL.md:148-150` says a forge refusal after the close was pushed leaves the close "retryable". It never says what the retry action is.
- The code now takes an already-closed-and-archived fast path (`skills/merge/erg-pr-merge:335-341`, the `Closed:` header check). The new retry test asserts that a re-run exits 0 and adds no commit (`tests/test_erg_pr_merge.sh:706-713`).
- So the "not idempotent" statement is stale for the archived case, and the new bullet gives no command for the retry. A reader would be told both not to re-run and that a re-run is available.
- Suggested fix: scope the "do not re-run" bullet to the missing-ticket-file symptom, and name the retry command (`erg-pr-merge N`) in the new bullet.

**F2. A 403 with an unexpected body shape refuses, and the doc does not say so.** Confidence: medium (read from the predicate, not executed). Tag: `consider:`
- The 403 delegation is accepted only when the body is empty or exactly one object whose keys are a subset of `message`, `documentation_url`, `status` (`skills/merge/erg-pr-merge:468-475` and `:494-505`).
- A 403 body with any extra key, such as `errors`, falls through to `partial or invalid inspection response` and dies.
- `skills/merge/SKILL.md:143-150` says every 403 is delegated, and lists partial pages, other errors and malformed successful data as refusals. It does not list a 403 with an extra field.
- No test scenario covers this (scenario list at `tests/test_erg_pr_merge.sh:669`).
- This fails closed, so it is not a safety defect. It is an undocumented refusal class, and a downstream reader would expect delegation.

**F3. "GitHub enforces any unseen requirements" rests on forge behavior this review cannot evidence.** Confidence: medium. Tag: `consider:`
- `skills/merge/SKILL.md:145-146` states the forge enforces unseen required checks on an ordinary merge.
- The tests only stub a refusal (`tests/test_erg_pr_merge.sh:114`, the `refused` scenario). No live forge was exercised, and the request did not ask for one.
- The doc should either cite the GitHub behavior it relies on or mark it as the assumption the 403 path depends on.

**F4. The erg-pr-merge header does not mention the denied-inspection path.** Confidence: high. Tag: `nofollow:`
- `skills/merge/erg-pr-merge:25-26` says direct merge happens "only when the one-shot rollup read shows every check done". That is still true for an empty rollup, read vacuously, so this is a documentation omission and not a contradiction.

**F5. The success message is not documented where an operator would look.** Confidence: high. Tag: `nofollow:`
- The script prints "Base-branch requirement inspection denied (HTTP 403); ordinary merge will enforce configured requirements." (`skills/merge/erg-pr-merge:511`).
- `skills/merge/SKILL.md` does not quote it, so an operator who sees it cannot look up its meaning.

## Checked and consistent

- Both endpoints are inspected regardless of the first result (`erg-pr-merge:452` and `:487`), so "validates the other endpoint" in `SKILL.md:143-146` matches the code.
- Non-403 errors die on both endpoints (`erg-pr-merge:477-478` and `:507-508`), matching "other inspection errors still refuse".
- Known required checks on either endpoint refuse (`erg-pr-merge:453-463` and `:488-493`), matching "with known required checks it refuses instead".
- No `--admin` appears anywhere in the merge paths, and the test asserts its absence (`tests/test_erg_pr_merge.sh:700-701`), matching "ordinary, non-admin merge".
- A forge refusal exits through `die` after the close is pushed (`erg-pr-merge:593-597`), and the close commit is pushed before merge (`erg-pr-merge:376`), matching the recovery claim in `SKILL.md:148-150`.

## Unavailable evidence

- No tests or lint were run. Results are as reported by the author.
- No other repository docs were supplied: the roar and raid skills, README, `rules/git.md`, and `erg-pr-status` may describe the old "no checks, direct merge" behaviour. I could not check them, so the propagation claim is limited to the four supplied files.
- gh's literal `(HTTP 403)` error format and live GitHub enforcement for non-admin merges were not checked. The author notes that format changes fail closed.

## Verdict

**comment**

No blockers. F1 is the one to fix before merge, because it sits on the refusal-recovery path the author asked about. F2 and F3 are documentation completeness, and F4 and F5 are audit notes.

## Round 2 synthesis and dispositions

Review-pr round 2 — head 42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9

All five previously unresolved perspectives ran again as actual read-only Claude headless sessions. Runtime canonical model claude-haiku-5-5, firstParty, Anthropic; producer OpenAI. Effort requested medium, observed unavailable. PANEL-INTEGRITY: COMPLETE; dissent: none on blockers. Raw reports retain each consideration.

All five confirm round-1 blocker and prior functional findings are resolved: partial pages are rejected, stderr is separate, successful retry is asserted, no admin bypass, known/malformed/non403/failing/pending cases still refuse. No blockers remain.

consider: [all] Empty-stdout403 lacks an explicit regression; add it.
consider: [red-team, scope] Add mixed403/non403 failures and refusal-reason assertions to strengthen negative controls.
consider: [consistency] Non403 fixture bodies should carry the actual status; branch endpoint comment should not call it paginated.
consider: [doc-propagation] Explain caller rerun and scope the older missing-ticket warning; document that unknown403 bodies also refuse.

Disposition of remaining hypotheses: ordinary forge enforcement is the ticket's explicit trust boundary; configured actor permissions remain forge configuration. The helper introduces no admin or alternative bypass. Live forge changes/merges are not needed for this stubbed regression ticket. Literal gh error-format drift fails closed. Same behavior on a nonempty rollup bypasses inspection entirely, as existing failing/pending controls verify. Preserve the local function name and symmetric inline handling instead of unrelated refactoring. Markdown wrapping and direct/ordinary wording do not change behavior. No-follow audit notes require no action.

Validation: full1702 passed,3 skipped58.32s; fast967; focused merge shell suite green; all ten forge checks green on this head. Planned final cycle addresses the concrete fixture/documentation/test points above.

Verdict roster:
correctness: comment
consistency: comment
scope: comment
red-team: comment
doc-propagation: comment

Panel API spend: $0.613343 (runtime list basis).


## round3/correctness

Runtime identity:
```json
{
  "head": "c952ed92b6058bb0e2f23ad24baac03bda8bfeab",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "067b3eba-fc7e-41e7-8744-8d66eae4e6da",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 19927,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 88912,
      "webSearchRequests": 0,
      "costUSD": 0.1412777,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 17767,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1412777,
  "elapsed_seconds": 96.5,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

I have no file-write or shell tools in this seat, so the report below is the full output for the seat process to transport to `correctness.md`. I read the supplied source and diff only. I did not run `tests/test_erg_pr_merge.sh`, `gh`, or any live forge call. The stubs were traced by reading.

# Correctness review: PR #1454 (ticket 1117), head c952ed92

## Scope checked

- **Fallback control flow**, `skills/merge/erg-pr-merge:436-540`: `merge_directly_or_die` → `no_checks_required` → caller's direct `gh pr merge --merge`.
- **Branch-protection inspection** (legacy endpoint): `:448-479`. Success path `:452-462`, HTTP 403 path `:464-476`, other errors `:477-478`.
- **Rules inspection** (paginated endpoint): `:481-509`. Success path `:487-493`, HTTP 403 path `:494-506`, other errors `:507-508`.
- **Refusal and recovery**: the close commit is pushed at `:369-376` before any merge. The direct-merge `|| merge_took_effect || die` is at `:593-597`.
- **Test matrix**: `tests/test_erg_pr_merge.sh:137-167` (stubs), `:265-291` (env pass-through), `:675-731` (scenario loop), `:716-726` (refusal retry).
- **Docs**: `skills/merge/SKILL.md:65`, `:130-149`.

## Findings

No blocking defects found.

I traced each scenario against the code:

- **Both endpoints 403, bodies present or empty** (`both`, `empty`): the bodies pass the single-error-object validator or are empty, `inspection_denied=1`, and the ordinary merge runs. Evidence: `:468-475`, `:498-505`.
- **One endpoint 403, the other 200 with known required checks** (`denied-required-legacy`, `denied-required-rule`): the 200 payload hits the `die` at `:463` or `:493`, so the run refuses. Known requirements are not hidden by a denial.
- **Malformed successful payloads** (`denied-malformed-*`): the `jq` validators at `:453-462` and `:488-493` refuse them.
- **Non-403 errors, including mixed cases** (`legacy500`, `rule500`, `mixed-*500`, `legacy404`, `rule401`): both `elif` branches check for `(HTTP 403)` specifically, so these reach the `die` at `:477-478` or `:507-508`.
- **Partial pages and extra keys** (`partial`, `extra`): `:468-474` and `:498-504` require exactly one ordinary error object. Page-one array data gives `.[0]` of type array, which fails the check.
- **Forge refusal after a 403 denial** (`refused`): `:593-597` dies with the forge's stderr, and the stub's `STUB_DIRECT_REFUSED` path at `tests/test_erg_pr_merge.sh:114-116` exercises that. The retry block at `:716-726` asserts the second run adds zero commits (`rev-list --count` unchanged) and merges. Retry is clean because `:333-343` skips an archived ticket that carries a `Closed:` header.
- **No bypass**: no `--admin` is emitted on any path. The loop checks `grep -- '--admin'` at `tests/test_erg_pr_merge.sh:712`.
- **Failing and pending checks**: `merge_directly_or_die` still checks them at `:534-539` before `no_checks_required` runs. Unchanged.

### Consider

1. **Confidence: medium.** `skills/merge/erg-pr-merge:510-514` and `SKILL.md:143-144`: a plain `gh pr merge --merge` by an actor with a ruleset bypass permission can merge even when a required check is configured but unseen. Before this change, a readable required check always refused. The ticket invariant (line 58) says "no bypass of the forge's configured merge requirements". The doc's phrase "including its configured actor permissions" discloses this. Whether it counts as a violation depends on how the invariant is read. Unavailable evidence: no live forge test, and no ruleset bypass fixture in the stub.
2. **Confidence: medium.** `:464-476` and `:494-506` accept only the keys `message`, `documentation_url`, and `status`. A legitimate GitHub 403 that adds a field such as `errors` would be refused. That fails closed, so it is a usability limitation, not a correctness defect. The live 403 body shape was not supplied.
3. **Confidence: high.** `SKILL.md:65` still says "merges directly only if every check is done", and the header at `skills/merge/erg-pr-merge:25-26` still describes the old rollup-only rule. Neither mentions the 403 delegation. Doc drift only.
4. **Confidence: medium.** `SKILL.md:130-133` quotes `close: no ticket found`, but this script's Step 1.5 (`:297-318`) dies with "absent from tickets/ at the branch tip" instead. The erg binary is not in the supplied source, so I cannot say whether erg emits that string.

### Nofollow

- The rules endpoint has no `extra`-key control (`tests/test_erg_pr_merge.sh:686` covers only the legacy side). The code at `:498-504` is symmetric with `:468-474`.
- The success scenarios do not assert the denial message. `merge_directly_or_die` still prints the success line for them.
- The loop's `grep -v ... | grep -q` pipelines run under `pipefail`. The pattern predates this PR. The payloads are small, so early-exit SIGPIPE is unlikely.

## Verdict

**approve.** I found no introduced defect within the stated scope. Items 1 and 2 are design limitations the ticket already accepts, and items 3 and 4 are documentation drift. Nothing here blocks merge.

## Unavailable evidence

- Shell execution: I could not run the suite, so the author's counts (fast967, lint186, full 1702 passed / 3 skipped, shell matrix green) are cited, not reproduced.
- Live forge: no gh calls, so the real 403 body shape and the stderr format `(HTTP 403)` are unverified against GitHub. The tests use stubs that emit that format.
- Erg source: not supplied, so item 4 is unresolved.

## round3/consistency

Runtime identity:
```json
{
  "head": "c952ed92b6058bb0e2f23ad24baac03bda8bfeab",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "c6a14524-4d8a-4c9d-8aac-ea97c9c74511",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 18257,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 88899,
      "webSearchRequests": 0,
      "costUSD": 0.1370897,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 16505,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1370897,
  "elapsed_seconds": 85.8,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Consistency review: PR #1454 (head c952ed92, base 37dda89d)

**Seat:** code-reviewer, consistency perspective (style, naming, docs, stale references)
**Scope:** the supplied diff and FULL SOURCE excerpts only. No tools, live forge, or test execution.

## Findings

### 1. Direct-merge criterion in the script header and SKILL.md omits the 403 path (consider, medium confidence)

- `skills/merge/erg-pr-merge:24-25` says the direct merge happens "only when the one-shot rollup read shows every check done."
- `skills/merge/SKILL.md:65` says the script "merges directly only if every check is done."
- The new behaviour also merges when both requirement reads return HTTP 403 (`erg-pr-merge:510-514`, with the message at `:511`). Requirements are then unknown, and the forge's ordinary enforcement decides.
- The header's "every check done" criterion was already incomplete before this PR, because the empty-rollup no-checks path (`erg-pr-merge:436-444`, covered by test case 14b) also merges directly. This PR widens the gap.
- Suggested wording: name the 403-denial case alongside the empty-rollup case in both places.
- Tag: `consider:`. No failing assertion; this is a documentation accuracy point.

### 2. Test comment says "after ONE read" for a path that now makes three forge reads (nofollow, high confidence)

- `tests/test_erg_pr_merge.sh:656-657`. The no-checks path now performs `pr view`, then the branch read, then the rules read (`erg-pr-merge:439`, `:446-483`).
- `merge_directly_or_die` (`erg-pr-merge:542-544`) uses "ONE read" correctly for the rollup, so the test comment is the imprecise one.
- Tag: `nofollow:`. No action expected.

### 3. Strict key set in the 403 body validator may refuse a real plan-gate body (consider, low confidence)

- `erg-pr-merge:473` and `:503` accept a denial body only if its keys are a subset of `message`, `documentation_url`, `status`.
- If GitHub adds any other key to a plan-gate 403, the script refuses. That is fail-closed, not a permissive defect.
- Live response shapes were not available, so I cannot say whether this happens. The author accepted fail-closed behaviour for literal-format changes, so this is only a note.
- Tag: `consider:`.

### 4. Temp-file cleanup is not trapped (nofollow, high confidence)

- `erg-pr-merge:446-450` and `:481-485` create a temp file and remove it on the next line. An interrupt between those lines leaves it behind.
- The script has no `trap` for this, and the file holds only stderr from `gh`.
- Tag: `nofollow:`.

## Checked and consistent

- **Success path, stderr:** captured stderr is re-emitted to stderr only (`erg-pr-merge:449-451`), so stdout stays clean for the `jq` parse.
- **Both API outcomes:** branch and rules each have success, 403 with empty body, 403 with valid denial body, 403 with extra or partial data, and non-403 failure. These are the scenarios at `tests/test_erg_pr_merge.sh:677-731`, and each expected reason matches a die string in the script (`legacy500`→"could not inspect", `extra`/`partial`→"partial or invalid", `denied-required-*`→"check", `denied-malformed-*`→"invalid").
- **Refusal recovery:** the `refused` scenario asserts the forge error is printed, the PR stays unmerged, the close commit count is unchanged, and a retry merges without a second close (`:716-727`). The script's archived-ticket skip (`erg-pr-merge:335-341`) supports this, and SKILL.md:130-149 documents it accurately.
- **Stub statuses:** `STUB_*_HTTP` values produce JSON with `status` as a string, matching the `tostring` comparison at `erg-pr-merge:472` and `:502`.
- **No `--admin`:** the test asserts its absence in every scenario (`:712-713`), and the SKILL bullet says "The script adds no bypass."
- **Ticket and PR:** the four content-bearing paths match the Raid Plan and Feasibility sections. Verification and exit-criteria checkboxes are consistent with the diff. The ticket's Invariants match the behaviour.

## Limitations

- I could not run the suite or the gate. The author-reported counts (fast967, lint186, full1702passed3skipped, shell matrix green) are taken as stated and are unverified here.
- No live `gh` run, so the `(HTTP 403)` stderr match and real denial-body shapes are unverified. The ticket accepts this as a known limitation.
- Only the supplied diff and excerpts were read; the remainder of `erg-pr-status` and the `/merge` skill tree was not inspected.

## Verdict

**approve**

There are no blockers and no `verifiable:` findings. Finding 1 is a documentation accuracy point that the author may dismiss. Findings 2–4 need no action.

## round3/scope

Runtime identity:
```json
{
  "head": "c952ed92b6058bb0e2f23ad24baac03bda8bfeab",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "41fe8edf-c459-4826-87d1-be41f18bf1eb",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 13769,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 88900,
      "webSearchRequests": 0,
      "costUSD": 0.1258707,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 12344,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1258707,
  "elapsed_seconds": 68.6,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

## Code-reviewer report: PR #1454 (ticket 1117), read-only

**Scope:** Ticket intent only. I reviewed the supplied diff and full sources for `skills/merge/erg-pr-merge`, `skills/merge/SKILL.md`, `tests/test_erg_pr_merge.sh`, and the ticket. I did not execute the shell suite, run the forge, or inspect the live repository. Author-reported results (fast 967, lint 186, full 1702 passed / 3 skipped, shell matrix green) are cited as reported, not independently reproduced.

### Traced behaviour (current code)

- **Legacy branch endpoint** (`erg-pr-merge:446-479`): success path validates unchanged. An HTTP 403 accepts an empty body or exactly one error object with `status` null or "403" and no extra keys. Any other failure dies.
- **Rules endpoint** (`erg-pr-merge:481-509`): same pattern with `--paginate`. A partial page followed by a 403 yields two JSON values under `jq -s`, so length 2 is rejected (`erg-pr-merge:498-504`).
- **Stdout purity:** stderr is captured to a temp file and re-emitted to stderr (`:448-451`, `:483-486`), so successful-call warnings cannot corrupt the JSON that is validated.
- **Temp file:** removed before any `die` (`:450`, `:485`), so no leak on refusal paths.
- **Refusal recovery:** a forge refusal leaves the close commit pushed. The retry takes the archived-with-`Closed:` path (`erg-pr-merge:338-340`), which adds no commit. The test asserts this by commit count (`tests/test_erg_pr_merge.sh:718-726`).
- **Admin bypass:** no `--admin` is added anywhere in the diff, and the test asserts its absence for every scenario (`:712-713`).
- **Scenario matrix:** each scenario is asserted in a direction-specific way. The empty-body 403, extra-key, partial-page, mixed 403/500, and malformed-success cases each assert a specific outcome or reason substring. I found no scenario that passes vacuously.

### Findings

**No blockers.**

1. **consider (confidence: low).** When inspection is denied, the empty-rollup branch no longer waits out the check-registration window. Required checks that have not yet registered are the case the forge is expected to block, since the forge's ordinary merge refuses when required checks are missing. Evidence: `erg-pr-merge:524-540` (`merge_directly_or_die`) and `:510-514`. Verifying this needs a live forge, which was not requested. Dismissable.

2. **nofollow (confidence: high).** The stderr re-emission is not asserted directly. The `warning` scenario (`tests/test_erg_pr_merge.sh:692`) still indirectly covers stdout purity: if the warning reached stdout, `jq` would fail and the scenario would fail. No action needed.

3. **nofollow (confidence: high).** Matching `(HTTP 403)` as a literal substring of gh's stderr (`erg-pr-merge:464`, `:494`) fails closed if gh changes its format. This was accepted in the review scope.

4. **Documented limitation, not a defect (confidence: high).** An actor with bypass permission can merge past required checks through the ordinary merge when inspection is denied. `SKILL.md:141-145` states this ("including its configured actor permissions"), and the ticket accepts it.

### Unavailable evidence

- I could not run the test suite, the lint, or the full gate. Results are the author's.
- I could not inspect the live forge or its rulesets, so the forge-side enforcement claims are untested.
- I had no shell or file tools, so this report is output-only and is not written to `.panel/1454/scope.md` by me. Seat transport must write it.

### Verdict

**approve**

The diff does what ticket 1117 asks: 403 on either inspection endpoint delegates to ordinary merge enforcement, with no bypass. Partial, malformed, and non-403 cases still refuse, and refusal recovery is tested by commit count. The remaining items are a dismissable consider and nofollow notes.

## round3/red-team

Runtime identity:
```json
{
  "head": "c952ed92b6058bb0e2f23ad24baac03bda8bfeab",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "b591c7c7-ad9c-43fd-9cb3-9775f89eecf2",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 19855,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 88913,
      "webSearchRequests": 0,
      "costUSD": 0.14109870000000002,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 18322,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.14109870000000002,
  "elapsed_seconds": 96.2,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

# Red-team report: PR #1454, ticket 1117 (read-only, from supplied source)

**Scope and limits.** I reviewed only the supplied diff and FULL SOURCE listings. I did not run the suite, `gh`, or any forge call, and I have no write tool here, so this response is the report for the seat process to transport. The author's counts (fast967, lint186, full1702/3) are taken as reported, not re-measured.

## Adversarial API outcomes

I traced each branch of `no_checks_required` against the stub matrix.

- **Branch endpoint, success:** the existing protection validation is unchanged (`skills/merge/erg-pr-merge:452-463`).
- **Branch endpoint, HTTP 403 with empty stdout:** accepted and delegated (`:464`, `:468`, `:477`). Covered by `empty` and `both`.
- **Branch endpoint, HTTP 403 with a body:** the body must be exactly one object with a string `message`, `status` absent or `"403"`, and no keys outside the three allowed (`:469-473`). Any extra key, such as `errors`, refuses. Covered by `extra`.
- **Branch endpoint, other status:** refuses at `:478`. Covered by `legacy404`, `legacy500`.
- **Rules endpoint, 403 after partial pages:** `--paginate` output is slurped and must be exactly one error object (`:498-504`), so any emitted page refuses. Covered by `partial`.
- **Rules endpoint, success with a known required check:** refuses (`:488-493`). Covered by `denied-required-legacy` and `denied-required-rule`.
- **Mixed outcomes:** a 500 on either endpoint refuses even when the other is 403 (`mixed-rule500`, `mixed-legacy500`).

I found no path where a known requirement or a malformed successful payload is hidden by a 403 on the other endpoint. The `inspection_denied` flag is set only after the 403-specific validation passes for that endpoint.

## Refusal recovery

- A direct-merge refusal reaches `die` at `:594-597` and exits non-zero. The close commit stays pushed, as SKILL.md states (`skills/merge/SKILL.md:147`).
- On retry, the archived ticket with a `Closed:` header is skipped (`erg-pr-merge:335-341`), so no second close commit is made.
- The `refused` case checks that the retry adds no commit and performs a direct merge (`tests/test_erg_pr_merge.sh:716-726`). This is the correct oracle for recovery.
- The `--admin` absence is checked across every scenario (`:712-713`). The stub logs all `pr merge` argv, so the check covers both the auto and direct attempts.

## Findings

**No blocking findings. No introduced defects found.**

1. **consider:** Delegation widens what the script will merge when the requirement read is denied. An admin actor on a repository with `enforce_admins` off, or with a ruleset bypass, could merge through ordinary `gh pr merge --merge` past a required check that the script could not see. The pre-change script refused in that case. The delegation is documented (`skills/merge/SKILL.md:141-145`, `erg-pr-merge:510-511`), and on a plan-gated free private repo no protection can exist to bypass. Confidence: medium. Not reproduced: the stubs do not model `enforce_admins`.

2. **consider:** `denied-required-rule` and `denied-required-legacy` use the substring `reason="check"` (`tests/test_erg_pr_merge.sh:698`, `:700`). Any die message containing "check" would satisfy them. Today the intended message is the only one reached, so this is not a false pass. Tightening to `"require checks"` would make the oracle exact. Confidence: high that the oracle is loose; low that it currently hides a defect.

3. **nofollow:** Paginated rules with an empty first page and a 403 on page 2 (`[]` then error) refuse, because slurping yields length 2 (`erg-pr-merge:498-504`). This is conservative and untested. No action needed.

4. **nofollow:** A 403 body with a `status` other than `"403"` refuses (`:472`). Also conservative and untested. No action needed.

## Verdict

**approve**

No blocker and no `verifiable:` finding. The two `consider:` items are about the documented delegation trade-off and test-oracle tightness, not defects in the current code. This verdict rests on reading the supplied code and tests; I did not execute them, so it does not replace the author's green run.

## round3/doc-propagation

Runtime identity:
```json
{
  "head": "c952ed92b6058bb0e2f23ad24baac03bda8bfeab",
  "base": "37dda89d05a5f7fe61aeef24f3b0cdff7d478008",
  "session_id": "4463f993-2391-4a23-bda3-35686f6c6abd",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 10441,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 88907,
      "webSearchRequests": 0,
      "costUSD": 0.1175577,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 8644,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1175577,
  "elapsed_seconds": 54.0,
  "route": "claude headless no tools, atomic stdout artifact transport",
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

Raw report:

I can't write the artifact: this seat has no file-write tool, so the report below is the full content for the seat process to transport to `/home/haduong/.agents/.claude/worktrees/raid-1117/.panel/1454/doc-propagation.md`. I reviewed only the supplied PR #1454 material.

# Doc-propagation report: downstream fallback documentation, PR #1454 (head c952ed92)

## Findings

**1. consider (medium confidence): the retry bullet quotes an error string the new flow no longer produces for an absent ticket.**
- Evidence: `skills/merge/SKILL.md:130` still headlines the bullet `"close: no ticket found" on a retry`. The supplied `skills/merge/erg-pr-merge` contains no such string. An absent claimed ticket now aborts earlier, at Step 1.5: `erg-pr-merge:307-308` ("absent from tickets/ at the branch tip … ERG_PR_MERGE_ALLOW_MISSING_TICKET"). Case 22 asserts that wording (`tests/test_erg_pr_merge.sh:1114-1115`).
- The quoted string may still come from `erg close` (not supplied), so this is unconfirmed. If it does not, the bullet points an operator at a message they will not see.
- Suggested edit: quote the Step 1.5 message, or say "absent from tickets/ at the branch tip".

**2. consider (medium confidence): the one-line summary of direct merge omits the 403 delegation.**
- Evidence: `skills/merge/SKILL.md:65` says that with auto-merge disabled the script "merges directly only if every check is done". The new behaviour (`erg-pr-merge:510-514`) also merges on an empty rollup when the requirement inspection is denied with HTTP 403, delegating unseen requirements to the forge. The detailed bullet at `SKILL.md:139-149` documents this, so a reader of only the summary gets the old rule.
- Suggested edit: add "(or, with an empty rollup and HTTP 403 inspection denial, the forge's ordinary enforcement decides; see § When the script bounces)".

**3. consider (low confidence): the documented "unexpected denial bodies" refusal is tested only on the legacy endpoint.**
- Evidence: the SKILL.md claim at `SKILL.md:145-146` covers both endpoints. The only `extra` scenario sets `legacy_http=403; extra=1` (`tests/test_erg_pr_merge.sh:686`). The rules-side check at `erg-pr-merge:498-505` is an inline copy with no test. The partial-page case is likewise tested only for rules (`:691`).
- The code looks symmetric, so I have no failing assertion. This is a coverage gap in a documented claim, not a demonstrated defect.

**4. nofollow: stale wording in a code comment.**
- Evidence: `erg-pr-merge:25-26` says direct merge happens "only when the one-shot rollup read shows every check done". That is still true in the empty-rollup sense, and the function comment at `:517-523` is accurate. No action needed.

**5. consider (low confidence): the ticket's verification checkbox may outrun the supplied evidence.**
- Evidence: `tickets/1117-…erg:51-54` marks "The ticket-only PR gate (`erg check` and the cross-PR ticket collision check) passes" as `[x]`. The author's listed checks are fast967, lint186, full1702passed3skipped, and the shell matrix. The ticket-gate output is not among them. Confirm it was run, or record it.

**Checked and consistent (no action):**
- Retry recovery: `SKILL.md:146-149` matches the code. An archived ticket with a `Closed:` header is skipped (`erg-pr-merge:338-341`). The commit is made only if something is staged (`:369-371`), and the push is a no-op on retry (`:376`). Test `:716-726` asserts an unchanged commit count and a successful retry merge.
- Refusal path: the close commit stays pushed (`:376` precedes the merge at `:591-598`), and the forge error is reported unsuppressed. Test `refused` checks this.
- No `--admin` anywhere in the script or docs.
- The former "not idempotent" guidance is gone from `SKILL.md`.
- The API-outcome documentation matches the code: a 403 on either endpoint delegates after the other endpoint is validated (`:452-476`, `:487-506`), and non-403 errors and malformed successful data still die.

## Verdict

**comment.** No blockers and no introduced defect in the documentation. Finding 1 is a likely stale trigger string that should be corrected.

## Unavailable evidence (stated honestly)

- Downstream callers' documentation (roar, raid, `erg-pr-status`, `rules/git.md`) was not supplied. Their fallback descriptions could not be checked.
- The full `tickets/erg` source, which emits `erg close` messages, was not supplied, so finding 1 cannot be settled from this material.
- The stub's 403 body on stdout is a modelling choice; real `gh` may print the error only to stderr. Live forge behaviour is unverified and was not requested. This is a transparent limitation, not a finding.
- No tools were used. Line numbers come from the supplied full-source listings.

## Round 3 synthesis and dispositions

Review-pr round 3 — head c952ed92b6058bb0e2f23ad24baac03bda8bfeab

Panel: 262 changed lines, four files, skills/merge pipeline paths. All five previously unresolved perspectives reran through distinct real headless Claude sessions. Runtime canonical model claude-haiku-5-5, provider firstParty, Anthropic family, decorrelated from OpenAI producer. Requested effort medium; observed effort unavailable. PANEL-INTEGRITY: COMPLETE. No required perspective missing.

No blocking or verifiable findings remain. Correctness, consistency, scope and red-team approve. Documentation comments, with no introduced defect; its considerations are dispositioned below. Prior partial-page blocker and concrete stream/recovery/test/documentation points are fixed and covered by the 18-scenario matrix.

Disposition of final considerations:
- [doc-propagation] The historical `close: no ticket found` trigger exists: the real tickets/erg in an isolated empty temporary store returned exit1 and `close: no ticket found for ID9999`. No production ticket changed. Raw evidence /tmp/1117-erg-diagnostic.txt. The body now correctly handles archived tickets and explicit caller rerun.
- [correctness, consistency, documentation] The summary's every-check-done condition concerns the registered rollup; the explicit-empty-rollup403 branch is documented in the detailed fallback section. No contradictory merge behavior or failing assertion was shown.
- [all] Ordinary forge enforcement, including configured actor permissions, is the ticket's explicit trust boundary. No --admin or alternate bypass is added. Unknown denial-body fields and changed gh error formats refuse conservatively; this limitation is documented. No live merge experiment was requested.
- [red-team] Required-check refusal reason uses `check` as a shared substring for the different legacy/rules messages. Known required payloads, a pushed close, nonzero result and no direct merge are also asserted; no current false pass was shown. Keep this shared assertion.
- [documentation] Extra-body validation is symmetric between endpoints; legacy extra-body and rules partial-page controls exercise the two paths. Proposed mirrored cases have no failing assertion. Ticket validation and collision checks are independently green on the forge.
- No-follow audit notes require no action. Raw findings and their original verdicts remain in the seat artifacts; none was promoted to a reproduced bug.

Validation on final sources: make check-fast967 passed; merge shell suite passes18 new scenarios. Full make check1619 passed86 skipped60.02s because Xvfb transiently failed. After Xvfb recovery, supplemental Zotero integrations32 passed7.18s and53 passed34.27s, with no fixture/source bypass. The preceding runtime-behavior-equivalent head passed1702/3 in58.32s; seats were supplied that prior gate count, while this synthesis corrects the final-source coverage record. All ten final-head forge checks pass, including ticket validation and cross-PR collision. Pre-PR adherence passed186 mechanical tests plus completed distinct semantic review.

Verdict roster:
correctness: approve
consistency: approve
scope: approve
red-team: approve
doc-propagation: comment — no blockers; considerations dispositioned with evidence above

Dissent: documentation comment retained; no unresolved blocking dissent.

correctness: session 067b3eba-fc7e-41e7-8744-8d66eae4e6da; runtime canonicalModel claude-haiku-5-5 / firstParty; requested effort medium, observed effort unavailable
consistency: session c6a14524-4d8a-4c9d-8aac-ea97c9c74511; runtime canonicalModel claude-haiku-5-5 / firstParty; requested effort medium, observed effort unavailable
scope: session 41fe8edf-c459-4826-87d1-be41f18bf1eb; runtime canonicalModel claude-haiku-5-5 / firstParty; requested effort medium, observed effort unavailable
red-team: session b591c7c7-ad9c-43fd-9cb3-9775f89eecf2; runtime canonicalModel claude-haiku-5-5 / firstParty; requested effort medium, observed effort unavailable
doc-propagation: session 4463f993-2391-4a23-bda3-35686f6c6abd; runtime canonicalModel claude-haiku-5-5 / firstParty; requested effort medium, observed effort unavailable
Round3 API spend: $0.662895 (runtime list basis).


## round4/doc-propagation

```json
{
  "session_id": "76a702df-409b-40e0-a09c-ef26ba34b3ea",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 18133,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 100936,
      "webSearchRequests": 0,
      "costUSD": 0.1488167,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 15082,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1488167,
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

# doc-propagation review: erg-pr-merge unavailable-branch-rule fallback (HEAD c952ed92, origin/main)

Output is on stdout for capture. I have no write tools here, so I did not create `/home/haduong/.agents/.claude/worktrees/review-1454/.panel/1454/doc-propagation.md`. I ran nothing and read only the supplied public text. Line numbers refer to the supplied numbering. The supplied material is the final state of the four files, not a diff, so I could not confirm what this change altered from the prior head.

**Reviewer:** doc-propagation seat, this session. Runtime model claude-haiku-5-5 per the session environment; effort not observed. This is the same model as the other four round-3 seats, so I am not an independent check on their shared model-level blind spots.

## 1. Disposition of prior public comment (ROUND3, doc-propagation: comment)

| Prior consideration | Disposition | Evidence |
|---|---|---|
| Historical `close: no ticket found` trigger exists; body now handles archived tickets and rerun | **Accepted for the archived/rerun part. Trigger claim not verified.** Archived-ticket skip at `erg-pr-merge:335-341`; retry adds no second commit at `:369-371`; `SKILL.md:130-133, 148-149` match. The trigger itself rests on `/tmp/1117-erg-diagnostic.txt`, which was not supplied. The script only calls `erg close` after `compgen` finds a file (`:333-351`), so this message is not reachable through the script's own path. See D1. | `erg-pr-merge:333-351`; `SKILL.md:130-133` |
| Every-check-done summary vs. explicit-empty-rollup 403 branch | **Accepted.** The detailed section exists at `SKILL.md:139-146`, and `merge_directly_or_die` matches it at `erg-pr-merge:524-540`. The summary at `SKILL.md:64-66` omits the empty-rollup path; a cross-reference would help (D4). | `SKILL.md:64-66, 139-146` |
| Ordinary enforcement is the trust boundary; no `--admin`; unknown denial fields and changed gh formats refuse; "this limitation is documented" | **Partly accepted.** No `--admin` anywhere in the script. Unknown denial bodies are documented (`SKILL.md:143-146`). The dependency on the literal `(HTTP 403)` substring in gh stderr (`erg-pr-merge:464, 494`) is not documented (D5). | `erg-pr-merge:464, 494`; `SKILL.md:139-146` |
| Required-check reason uses shared substring `check`; known payloads, pushed close, nonzero, no direct merge asserted | **Substring: accepted with a weakness.** Every required-check die message contains "check" (`:444, 463, 493`). The shared assertion could pass on an unrelated "check" message, but no current false pass is shown. **"Pushed close" is overstated.** The matrix checks the local branch via `closed_has` (`test:309-312`), not `origin`. Only Case 6 asserts the push (`test:410-413`). | `test_erg_pr_merge.sh:309-312, 698-701, 716, 727` |
| Extra-body validation symmetric; legacy-extra and rules-partial controls; mirrored cases have no failing assertion | **Accepted as stated, with a coverage gap.** `extra` sets only the legacy endpoint (`test:686`), and `STUB_HTTP_EXTRA` only matters when the rules endpoint returns 403 (`test:159`). No scenario exercises rules-endpoint extra body or legacy partial pages. Code reading suggests both refuse. | `test_erg_pr_merge.sh:686, 689-697` |
| Ticket validation and collision checks green on forge | **Unavailable.** Forge output not supplied. | — |
| No-follow audit notes require no action | **Accepted** for the notes themselves. Raw seat artifacts are not supplied, so I could not check them. | — |

Matrix count checked: the loop at `test:677` has 18 scenarios, matching the record.

## 2. Documentation findings (new, from supplied source)

**D1 — `skills/merge/SKILL.md:130-133` names a trigger the script does not produce. Confidence: medium-high.** When a claimed ticket is absent from both directories, Step 1.5 dies first with "absent from tickets/ at the branch tip" (`erg-pr-merge:296-310`). The `close: no ticket found` text would only come from erg itself, after a file was found. The doc should name the message the operator will actually see.

**D2 — `SKILL.md:3` says "Atomically close … and merge", which the body contradicts. Confidence: high.** The close commit is pushed before merge (`erg-pr-merge:376`). A refusal leaves it pushed (`SKILL.md:146-147`), and ticket Invariants require exactly that recoverability (ticket lines 58-60). The description should drop "atomically" or say the close is not reverted on refusal.

**D3 — Silent skip when erg or `tickets/` is absent. Confidence: high that the code does this; medium that the doc gap matters.** With a valid claim, no `erg`, and no `tickets/` directory, the script prints a Note and still merges (`erg-pr-merge:324, 377-379`). `SKILL.md` does not mention it. This predates this change as far as I can tell, so it is out of scope here.

**D4 — "Empty rollup" bullet is not marked as fallback-only. Confidence: medium.** It sits under "When the script bounces" (`SKILL.md:123-158`). `no_checks_required` runs only after auto-merge fails (`erg-pr-merge:587-591`). The bullet should say so.

**D5 — Gh-format dependency undocumented. Confidence: high.** The 403 match depends on gh's `(HTTP 403)` stderr text (`erg-pr-merge:464, 494`). `SKILL.md` describes "unexpected denial bodies" but not this.

**D6 — Ticket checkboxes precede evidence. Confidence: high.** Exit criteria and Verification are ticked `[x]` (ticket lines 51-53, 64-68). The log holds only the creation entry (line 7). The ticket is still open. Either untick until verified, or cite the verifying PR head.

**D7 — Gate-count record is ambiguous. Confidence: high that the text is ambiguous; unknown whether it hides a failure.** ROUND3 reports "1619 passed86 skipped", "1702/3", and "make check-fast967". The "/3" could mean three failures or a fraction, and the full gate was not re-run cleanly on the final head after the Xvfb recovery. Restate with explicit passed/failed/skipped and the head each count belongs to.

**D8 — Panel independence wording. Confidence: medium.** All five seats are claude-haiku-5-5 on firstParty, so they are decorrelated from the producer but correlated with each other. The record should say so, rather than imply five independent seats.

## 3. Minors

- `consider:` D2 wording, and the frontmatter "Atomically" claim.
- `consider:` add mirrored tests: a legacy partial-page case and a rules-endpoint extra-body 403 case. I expect both to pass, so this is coverage, not a defect.
- `consider:` correct ROUND3's "pushed close" to "local close commit; push asserted only in Case 6".
- `consider:` replace the shared `check` substring with per-endpoint reasons, or document why the shared one is intentional.
- `hypothesis:` D7's "/3" is a failure count. Not verified; the raw gate output is not supplied.
- `nofollow: audit` — the `erg-pr-merge` header comment (`:15-26`) omits the 403 fallback. Pre-existing header scope; not a doc defect for this change.
- Verifiable with a failing assertion: none found. I did not find a case where a documented behaviour contradicts a passing or failing test.

## 4. Unavailable evidence

- `/tmp/1117-erg-diagnostic.txt` and the erg isolated-store run behind the trigger claim.
- Any gate output: `make check-fast`, the full `make check`, the Zotero supplemental runs, and the 18-scenario shell run.
- Forge checks on the final head: ticket validation and cross-PR collision.
- Session transcripts and raw seat artifacts for all five reviewers.
- The diff from the prior head, so I could not isolate what this change altered.
- Live gh behaviour, including the actual denial body and whether it contains extra fields.

## 5. Verdict

**comment.** The fallback documentation matches the script's behaviour on the paths I checked, and no blocking documentation defect appears. D2 and D6 should be fixed before merge, and the rest can be filed as minors. Clean-verdict conditions are not met because of D1–D2 and the unverified gate record in D7.

## round4/regression

```json
{
  "session_id": "8a8167df-f574-4a91-8d73-57c657809de9",
  "modelUsage": {
    "claude-haiku-5-5": {
      "inputTokens": 2,
      "outputTokens": 23062,
      "cacheReadInputTokens": 50944,
      "cacheCreationInputTokens": 100958,
      "webSearchRequests": 0,
      "costUSD": 0.1611612,
      "contextWindow": 1000000,
      "maxOutputTokens": 128000,
      "thinkingTokens": 20621,
      "canonicalModel": "claude-haiku-5-5",
      "provider": "firstParty",
      "costBasis": "list"
    }
  },
  "cost_usd": 0.1611612,
  "requested_effort": "medium",
  "observed_effort": "unavailable"
}
```

# Regression review: erg-pr-merge denied-inspection fallback (ticket 1117)

Target: HEAD `c952ed92b6058bb0e2f23ad24baac03bda8bfeab` (origin/main). Read-only, from the supplied sources only. I did not execute the test suite, call GitHub, or write to the repository. The report is the stdout payload for `/home/haduong/.agents/.claude/worktrees/review-1454/.panel/1454/regression.md`.

## Verdict: comment

No blocking defect found. I traced all three exit criteria to code and tests. The comments below are minor, and two evidence gaps are recorded in the unavailable-evidence section.

## Exit criteria traced

| Criterion (ticket 1117 lines 64-68) | Code | Test |
|---|---|---|
| 403 on branch-rule inspection no longer blocks a non-admin merge the forge accepts | Legacy 403 sets `inspection_denied=1` at `skills/merge/erg-pr-merge:476`; rules 403 at `:506`; the merge proceeds at `:596-597` with `--merge --delete-branch`, no `--admin` | `tests/test_erg_pr_merge.sh:684-685`, `:689-690`, `:692`, `:714-715` (both, empty, legacy, rule, warning) |
| Forge refusal reports the error, leaves the PR unmerged, no bypass | `gh pr merge … \|\| merge_took_effect \|\| die` at `:596-597`; `merge_took_effect` reads state at `:401-407`; no admin flag anywhere in the script | `:693`, `:716-726` (refusal output, retry adds no second close commit, `--admin` absent at `:712`) |
| Regression tests and ticket gate pass | Not executed by me | Round-3 record only, see unavailable evidence |

Invariants also hold on the reading:
- Failing checks refuse before any inspection: `:534-535`, which runs before `no_checks_required` is reached (`:530-533`). Pending checks refuse at `:537-539`, also before inspection. The 403 path cannot reach either.
- A null rollup refuses at `:443-444`, covered by `:875`.
- Malformed or partial successful data refuses: partial pages at `:469-474` and `:499-504`, malformed rules and legacy at `:453-463` and `:488-493`, covered by `:698-701`.
- Archived-ticket retry skips `erg close` at `:338-340` and creates no commit when nothing is staged (`:369`). This matches the SKILL.md retry text (`skills/merge/SKILL.md:130-149`).
- Scope matches the ticket's four planned paths (ticket lines 95-96). I found no collateral file.

The 18-scenario loop at `tests/test_erg_pr_merge.sh:677` matches the count in the ticket record.

## Findings

**1. consider: the shared `check` substring does not separate the two denied-required scenarios.** Confidence high (read-only). `tests/test_erg_pr_merge.sh:698-700` and `:727-728` assert `reason="check"`. Both refusal messages contain it: `skills/merge/erg-pr-merge:463` ("has required checks or returned invalid protection data") and `:493` ("require checks or returned invalid check data"). The assertion would still pass if a known-required payload were refused for an invalid-data reason. No failing assertion exists, so this is not verifiable as a defect. Tightening it to distinct substrings is cheap.

**2. consider: the mirrored rules extra-body case is not in the matrix.** Confidence high. Validation is symmetric in code (`:469-473` for legacy, `:499-503` for rules). The matrix covers extra-body only on the legacy endpoint (`:686`). Behaviour reads as correct. Adding a `rule-extra` scenario would pin it.

**3. hypothesis: a secondary-rate-limit 403 is classified as a permission or plan denial.** Confidence medium-low, because I cannot check live GitHub response bodies. Both `:464` and `:494` treat any HTTP 403 with an ordinary error object as denial. A rate-limit 403 would proceed to an ordinary merge and print "requirement inspection denied" (`:511`). The forge still enforces required checks, so this is not a bypass. The only effect is a misleading diagnostic.

**4. nofollow: audit.** The `for scenario` loop (`tests/test_erg_pr_merge.sh:677-731`) does not set `ERG_PR_MERGE_SYNC`. On success paths, `sync_local_base` (`skills/merge/erg-pr-merge:555-557`) runs the real `scripts/sync-local-main.sh` against the fixture repo. Case 5 and 14b already do this, so it is not new. Listed for audit only.

**5. nofollow: audit.** The test header (`tests/test_erg_pr_merge.sh:2-12`) lists cases 13-14 and does not mention the 1117 matrix. The final PASS line at `:1355` does mention it. Documentation only.

**6. consistency: the round-3 gate record is internally inconsistent.** Confidence high that the record is inconsistent. The forge text reports full `make check` as "1619 passed, 86 skipped, 60.02s" after an Xvfb failure. It then reports supplemental Zotero subsets (32 and 53 passed) and a separate "1702/3" count for the "preceding" head, and says the synthesis "corrects" the final-source coverage record. A clean full-gate result on c952ed92 is therefore not established by the record. This is an evidence gap, not a code defect.

**7. consistency: the round-3 panel shares one model with this seat.** All five round-3 seats ran `claude-haiku-5-5` on firstParty, with effort observed as unavailable. This seat also runs `claude-haiku-5-5`. The record states decorrelation from the OpenAI producer, which holds. Within the panel, the five verdicts are not independent on model identity. This review is not decorrelated from round 3 either. Record it as a limitation.

**Settled, not reopened:** the historical `close: no ticket found` trigger (round-3 evidence in `/tmp/1117-erg-diagnostic.txt`), the forge-enforcement trust boundary, and the summary wording at `skills/merge/SKILL.md:65` versus the detailed section at `:139-147`. The summary is consistent with the detailed section, and round 3 dispositioned it.

## Unavailable evidence

- No prior-revision diff was supplied. I cannot measure regression against the parent of `c952ed92`. I evaluated HEAD against the ticket's exit criteria and its test matrix.
- The test suite, `make check`, `erg check`, and the collision check were not run. The pass results above are the round-3 claims only.
- Not supplied: `scripts/sync-local-main.sh`, `tickets/erg`, `skills/route/references/decorrelation.md`, the live `gh` error text for 403 bodies, and the raw round-3 seat artifacts.
- No live GitHub behaviour was checked. Findings 3 and the trust-boundary reading rely on the stub modelling of `gh` output.

## Gaze adherence-attempt1.md

adherence: FAIL
escalation: adherence-infrastructure
head: c952ed92b6058bb0e2f23ad24baac03bda8bfeab
semantic_review:
  applicable: true
  status: skipped
  reason: "Earlier blocking phase: declared project runner could not execute because uv could not create a temporary file in its configured cache on the read-only filesystem."
  rule_sources: []
  worker_id: null
  model: unavailable
  family: unavailable
  effort: unavailable
  route: null
  launch_evidence: null
  completion_evidence: null
mechanical_failures:
  - test_or_grep: "make lint (declared adherence runner)"
    rule_ref: "verify-adherence#project-runner"
    file: "Makefile"
    line: 32
    reason: "Runner exited 2 before pytest: uv Could not acquire lock; Could not create temporary file at /data/cache/uv/.tmp... (Read-only file system)."
semantic_findings: []
untested_rules:
  - rule: "skills/merge/SKILL.md#When the script bounces"
    suggested_test: "Run a bounded semantic review of the changed fallback instructions against the project's full applicable rules after the adherence runner can execute."
static_checks:
  reference_resolution: skipped
  reason: "Diff touches no .tex, .qmd, or .bib files."
  diff_check: clean
declared_runner:
  file: "README.md"
  line: 111
  command: "make lint"
command_dry_run: "uv run --frozen python3 -m pytest tests/ -m adherence"


## Gaze adherence.md

adherence: PASS
escalation: null
head: c952ed92b6058bb0e2f23ad24baac03bda8bfeab
semantic_review:
  applicable: true
  status: ran
  reason: "Diff changes the merge fallback script and its recovery instructions; both are instruction/architectural surfaces requiring semantic review."
  rule_sources:
    - "AGENTS.md"
    - "rules/git.md"
    - "rules/workflow.md"
    - "rules/guards.md"
    - "skills/merge/SKILL.md"
  worker_id: "/root/gaze_adherence1454/adherence_semantic1454"
  model: unavailable
  family: unavailable
  effort: unavailable
  route: "Codex collaboration subagent; requested gpt-6-luna @medium (OpenAI), per caller's selected bounded-review route"
  launch_evidence: "collaboration.spawn_agent returned worker /root/gaze_adherence1454/adherence_semantic1454; launch arguments pinned model gpt-6-luna, reasoning_effort medium, fork_turns none."
  completion_evidence: "Worker returned a completed review of the supplied full diff and current/base instruction files; report validated against anchors in skills/merge/erg-pr-merge, skills/merge/SKILL.md, and tests/test_erg_pr_merge.sh."
  reviewed_evidence:
    - rule: "Project instructions — Skills Catalog"
      evidence: "Diff changes an existing skill; it does not add, rename, or remove one."
    - rule: "rules/git.md — Merging / Reading state you will act on"
      evidence: "HTTP 403 denials delegate only to an ordinary merge after validating the other inspection endpoint; known requirements and malformed data still refuse (skills/merge/erg-pr-merge:452-513)."
    - rule: "rules/workflow.md — Autonomous action / Ticket discipline"
      evidence: "Change remains within ticket 1117's four planned files; the new tests cover denied inspection, malformed/known-required responses, forge refusal, and retry (tests/test_erg_pr_merge.sh:675-730)."
    - rule: "rules/guards.md"
      evidence: "No credential, write-authorization, or context-handling behavior is changed."
    - rule: "skills/merge/SKILL.md — When the script bounces"
      evidence: "Recovery instructions match the script's HTTP 403 and archived-ticket retry behavior (skills/merge/SKILL.md:130-149)."
mechanical_failures: []
semantic_findings: []
untested_rules: []
static_checks:
  reference_resolution: skipped
  reason: "Diff touches no .tex, .qmd, or .bib files."
  diff_check: clean
declared_runner:
  file: "README.md"
  line: 111
  command: "make lint"
command_dry_run: "uv run --frozen python3 -m pytest tests/ -m adherence"
runner_result: "186 passed, 1519 deselected in 8.76s"
preserved_prior_attempt: ".panel/1454/adherence-attempt1.md"


## Gaze review.md

# Native review — PR1454

Result: CLEAN (no actionable findings).
Reviewed SHA: c952ed92b6058bb0e2f23ad24baac03bda8bfeab
Base: origin/main
Worktree: /home/haduong/.agents/.claude/worktrees/review-1454
Axes: all; doctype=-; lang=-

First and final review-pr-anchor checks passed against GitHub with identical SHA and roster:
- skills/merge/SKILL.md
- skills/merge/erg-pr-merge
- tests/test_erg_pr_merge.sh
- tickets/1117-erg-pr-merge-handle-unavailable-branch-r.erg

Native route: codex review --base origin/main; explicit model and review_model gpt-6.1-sol; model_reasoning_effort low.
Identity: OpenAI Codex v0.163.0; provider openai; model gpt-6.1-sol; reasoning effort low; session 01a15309-7ecf-7092-92b3-df3503b4b40e.
Exit code: 0. Raw runtime evidence: review-native.log in this directory.

The native reviewer examined the actual nonempty four-path diff and surrounding merge helper, ticket contracts, and fixtures. It checked the ordinary merge fallback after denied legacy/effective-rule inspection, continued validation of known requirements and malformed payloads, rejection of non-403 errors and partial paginated bodies, refusal propagation and idempotent closed-ticket retry. Documentation and ticket changes match that behavior. No actionable defects were identified.

Validation evidence: native shell syntax validation succeeded. Its regression command completed successfully and emitted the final PASS suite summary in the preserved log. The final native prose says the suite was still running, but the immediately preceding runtime completion records its success.

Containment limitation: native /review internally used bare git diff/status with its workdir explicitly set to the supplied review tree, rather than git -C as instructed. No wrong-tree execution or tracked-file edits were observed. Outer review operations used the explicit worktree, and final anchor remained unchanged. No forge review was posted.


## Gaze pr-review.md

---
phase: review-pr
pr: 1454
round: 4
head: c952ed92b6058bb0e2f23ad24baac03bda8bfeab
result: COMMENT
blocking: 0
panel_integrity: COMPLETE
dissent: preserved
gate: PASS (1702 passed, 3 skipped)
forge_post: verified (5568220497; reviews 3 -> 4)
---

Review-pr round 4 — head c952ed92b6058bb0e2f23ad24baac03bda8bfeab

Round derived from three posted skill reviews, not caller count. Same head as round3, no intervening rewrite: doc-propagation reran plus ONE regression seat over cleared correctness/consistency/scope/red-team. Original width262 changed lines,4files, skills/merge pipeline paths; scoped manifest2seats. PANEL-INTEGRITY: COMPLETE. Both distinct headless sessions completed artifacts within deadline; no required seat missing.

No blocking or reproduced introduced defect. Both selected seats return comment; their dissent is retained, not converted to approval.

Findings and dispositions:
- [doc-propagation] consider: D1 still questions the historical `close: no ticket found` heading. Existing isolated real erg diagnostic proves the string exists (exit1, `close: no ticket found for ID9999`); body correctly says inspect missing claims and skips archived closed tickets. The helper's earlier branch-tip diagnostic differs. Retain as dismissable wording consideration, no demonstrated current failure.
- [doc-propagation] nofollow: D2 frontmatter "Atomically" predates this diff (confirmed origin/main:skills/merge/SKILL.md:3); D3 absent-erg behavior likewise unchanged. No new ticket or source edit made in this read-only review. Existing wording does not negate the explicit pushed-close recovery instructions at lines146-149.
- [both] consider: shared `check` oracle and unmirrored rules extra-body/legacy partial-payload test cases remain optional coverage suggestions. Symmetric validators, known required-check payloads, nonzero/no-direct-merge assertions and the passing matrix show no false pass. Existing round3 disposition retained.
- [doc-propagation] consider: D4 fallback heading and summary cross-reference, D5 literal gh-format dependency detail. Detailed section states empty-rollup 403 ordinary enforcement and malformed/unexpected-body refusal; changed stderr format conservatively refuses. No behavioral contradiction reproduced.
- [doc-propagation] nofollow: D6 checkbox verification concern resolved by reread final-head forge SUCCESS for validate-tickets and cross-pr-ticket-collision; all10checksSUCCESS. D7 prior shorthand is clarified: previous equivalent-runtime head had1702passed,3skipped; final-source earlier run1619passed,86skipped plus85 supplemental recovered integrations. Current fresh gate result is recorded below.
- [regression] consider: rate-limit403 diagnostic wording. Ticket deliberately accepts every HTTP403 after payload validation, including permission/plan cases; ordinary merge still enforces configured actor permissions. No live merge experiment or admin bypass added.
- [both] nofollow: model correlation limitation accepted and stated explicitly below. Header, fixture-sync and raw-push assertion audit notes require no action. The matrix checks local closed state; separate Case6 asserts push, and code pushes before merge. Avoid overclaiming every matrix row independently asserts remote state.

Dissent: documentation states "D2 and D6 should be fixed before merge"; regression calls the prior gate record inconsistent. D2 is unchanged wording; D6 forge evidence is verified, and fresh gate resolves the record gap. These are comments with no request-changes. Seat artifacts preserve exact original statements, including malformed minor prefixes; this synthesis normalizes all posted minors to the required tag set.

Validation: focused tests/test_erg_pr_merge.sh independently exits0 at exact final SHA, including18new matrix scenarios. All10final-head forge checksSUCCESS. Fresh declared full gate `make --no-print-directory -C <review-tree> check`:1702passed,3skipped,0failed,58.69s;exit0 at exact final SHA.
Initial default cache failed on read-only /data/cache/uv. Sandbox full gate has local-service restrictions. A normal-environment run reached1700passed3skipped2failed solely because my `make -C` propagated directory banners into nested make-output fixtures; untouched refresh-STATE tests demonstrate this. Final run suppresses directory banners with --no-print-directory and changes no source or fixture.

Runtime evidence: doc-propagation session76a702df-409b-40e0-a09c-ef26ba34b3ea; regression session8a8167df-f574-4a91-8d73-57c657809de9. Each runtime modelUsage canonicalModel claude-haiku-5-5/provider firstParty, Anthropic family. Requested medium effort; observed effort unavailable. Distinct sessions are cross-family from OpenAI producer, but same-family/same-model with each other and prior panel: model-level independence between panel seats is unavailable. Public-source, no-tool seats could not execute checks or inspect live forge; orchestrator supplied verification above. Current panel API list cost$0.3099779. Prior15seats$1.855614 plus probe$0.0125293 retained separately. Native earlier semantic worker identity unavailable. No live forge merge or real403 transcript exercised.

Verdict roster:
doc-propagation: comment
regression: comment — covers cleared correctness,consistency,scope,red-team


## Gaze simplify.md

# PR 1454 portable simplification review

Verdict: CLEAN
simplify route: portable
Reviewer: distinct Codex simplification seat /root/simplify1454 (same active runtime; no external/provider independence claimed).
Reviewed SHA: c952ed92b6058bb0e2f23ad24baac03bda8bfeab
Base: refs/remotes/origin/main
Worktree: /home/haduong/.agents/.claude/worktrees/review-1454

Both before and after `review-pr-anchor.py 1454 --worktree ...` succeeded through network-enabled read-only checks and reported the same SHA and four-path roster. Examined explicit `git -C <worktree> diff origin/main...HEAD`, the surrounding merge helper and fallback call sites, existing shell-test setup/stubs and adjacent fallback tests, merge recovery documentation, and ticket 1117 scope/criteria.

Paths examined:
- skills/merge/erg-pr-merge
- skills/merge/SKILL.md
- tests/test_erg_pr_merge.sh
- tickets/1117-erg-pr-merge-handle-unavailable-branch-r.erg

Concrete simplification candidates considered:

1. Extract the duplicated API diagnostic capture and 403-body predicate (erg-pr-merge:446-507). Two endpoint blocks duplicate a short capture sequence and denial validator, but successful response schemas differ and the rules endpoint alone paginates. Keeping two explicit calls preserves straightforward control flow and endpoint-specific errors; a generic wrapper would need extra output/status plumbing in shell. The denial predicate is small and identical at exactly two adjacent call sites. There is no existing reusable inspection helper in the searched merge helper/scripts. For this bounded ticket, introducing a new abstraction is not a necessary simplification; the ticket explicitly anticipates no new abstraction. No change requested.

2. Collapse both inspections into one permissive denial branch or skip the second call after 403 (erg-pr-merge:464-507). Rejected: the remaining endpoint can expose known required checks or malformed data, and paginated failure can emit partial successful data. The explicit independent validation and strict single-error-object predicate serve the ticket's requirements. No change requested.

3. Replace the scenario loop with separate fixture tests, or reduce its flags (test_erg_pr_merge.sh:675-732). The existing seed_repo/run_merge/closed_has mechanisms are already reused, and the case table confines scenario differences while sharing outcome checks. The distinct flags represent endpoint-specific and payload-specific observable cases. Splitting would duplicate fixture and assertion code; removing cases would lose behavior coverage. No change requested.

4. Remove the special refusal-and-retry assertion (test_erg_pr_merge.sh:716-727). Rejected: it alone ties an ordinary forge refusal to an unchanged close-commit count on retry, directly covering recoverable ticket closing. Existing archived-ticket handling is reused without new production machinery. No change requested.

5. Shorten recovery documentation (SKILL.md:130-149). The text separates absent tickets, already archived tickets, pending checks, denied inspections, malformed responses, and forge refusal. These are materially different operator actions; further compression would obscure the retry contract. No change requested.

Findings: none. Must-fix simplification findings: none. No source changes made; no tests rerun because this seat made no changes and was assigned source review, with completed verification supplied by the orchestrator. The ticket's explicit forge enforcement trust boundary was preserved.


## Gaze gate.md

/verify-gate round=1 verdict=APPROVED
Gate session id: ec60ee14-a2f9-4eb2-8365-9e9bf7eddc85
Review worktree path: /home/haduong/.agents/.claude/worktrees/review-1454
Ruled tip SHA: c952ed92b6058bb0e2f23ad24baac03bda8bfeab
Exit criteria: 3/3  Review blockers: 0  Simplify: 0
Adherence: 0 blocking  Scope overflow: 0 files (0 ticketed/0 escalate)
Published minors: no unresolved verifiable minors; consider findings retained as informational, nofollow muted. Raw malformed labels are preserved below and do not bounce round 1 under the explicit Minor tag handling rule.

```yaml
verdict: APPROVED
round: 1
pr: 1454
ticket: "1117"
gate_session_id: ec60ee14-a2f9-4eb2-8365-9e9bf7eddc85
review_worktree: /home/haduong/.agents/.claude/worktrees/review-1454
ruled_tip_sha: c952ed92b6058bb0e2f23ad24baac03bda8bfeab
round_derivation: "Live issue comments: 0; four skill review syntheses, none matching /verify-gate round=N verdict=V. Current gate round = 0 + 1."
per_exit_criterion:
  - criterion: "A GitHub plan/permission 403 during branch-rule inspection no longer prevents a normal, non-admin merge when the forge accepts it."
    status: ADDRESSED
    evidence: "51407e128dbab759cd53f2a666d69a9522e72a48 introduced the fallback; 42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9 hardened streams/payloads. Final code skills/merge/erg-pr-merge:464,494,510,593; c952ed92b6058bb0e2f23ad24baac03bda8bfeab tests/test_erg_pr_merge.sh:677 scenarios both/empty/legacy/rule, and :712 no-admin assertion."
  - criterion: "If the forge rejects that merge, `/merge` reports the refusal and leaves the PR unmerged; no rules or checks are bypassed."
    status: ADDRESSED
    evidence: "42200d4512e9911f3d6ee71e7fbbf3aa3aecc0d9 tests/test_erg_pr_merge.sh:716 refusal stderr, nonzero result, direct ordinary attempt, successful retry and unchanged close count; final skills/merge/erg-pr-merge:593 and :596 ordinary merge || merge_took_effect || die. Current no-admin assertion :712, known/malformed/non403 cases :677; existing pending refusal Case14 :633, null-rollup :810 and failing controls remain. Close push occurs before merge at :376; archived skip :338."
  - criterion: "The regression tests and ticket-only PR gate pass."
    status: ADDRESSED
    evidence: "test_id tests/test_erg_pr_merge.sh including 18-scenario ticket1117 matrix at c952ed92b6058bb0e2f23ad24baac03bda8bfeab; native review runtime log records final suite PASS. Exact-head /tmp/1454-gaze-check-final.log:1702 passed,3 skipped,0 failed,58.69s. Final-head forge test_ids validate-tickets job117935527755 and cross-pr-ticket-collision job117935527852, CI run39214634881:SUCCESS; all10 forge checks SUCCESS, read live."
unresolved_review_comments: []
malformed_minors:
  - comment_ref: ".panel/1454/doc-propagation.md#D1-D8-and-Minors"
    excerpt: "Raw D1/D3/D4/D5/D6/D7/D8 headings lack a canonical minor prefix; D7 also appears as hypothesis:. Published round4 synthesis supplies canonical dispositions. Raw tags are retained, not rewritten."
  - comment_ref: ".panel/1454/regression.md#Findings-3-6-7"
    excerpt: "Raw #3 hypothesis:, #6 consistency:, #7 consistency: are outside verifiable:/consider:/nofollow:. Published synthesis supplies dispositions. No failing assertion or blocking verdict is asserted."
unresolved_simplify_findings: []
unresolved_adherence_violations: []
scope_overflow: []
rationale: |
  The strongest attack was the round1 red-team partial-page blocker: a later HTTP403
  previously hid a successful required-rule page. Post-comment commit42200d45
  separates stderr, requires a single ordinary error object or empty stdout on403,
  and rejects partial pages. Final matrix partial/extra and known-required controls
  pin refusals. The other substantive attack concerns actors with forge-configured
  bypass privileges. The ticket expressly delegates unknown requirements to the
  ordinary forge operation; final docs disclose configured actor permissions at
  skills/merge/SKILL.md:143. The helper adds no --admin or alternate bypass.
  No live403 transcript or live merge was exercised; this is the requested stubbed
  regression contract, and strict CLI/body formats fail closed.
  Four actual forge syntheses and all raw round1-4 reports were read. No separate
  human issue comments or inline threads exist (live REST/GraphQL; no pagination).
  Consider findings remain informational; nofollow findings are muted. Raw malformed
  minor prefixes are explicitly recorded and are nonblocking on gate round1 under
  the live rule; they would require escalation if still present on gate round2.
  No phase contradiction remains: the preserved adherence cache failure was retried
  successfully with186 mechanical tests plus separate completed semantic review;
  exact-head full gate resolves the earlier differing coverage counts.
```

Evidence and dissent audit:

- Round1 review PRR_kwDORsAV3c8AAAABS-Bgag, submitted07:00:49Z, head51407e12: red-team B1 ADDRESSED by post-comment42200d45 (09:04:32+0200), helper:448,469,483,499 and partial scenario. Stream-warning considerations ADDRESSED by same commit plus warning scenario; actual retry assertions ADDRESSED at test:718-725. Known-required/documentation wording subsequently updated. Literal gh format, rate-limit classification and ordinary-forge trust remain informational considerations, not reproduced defects. Diagnostic/header/no-admin/checkbox notes are nofollow.
- Round2 review PRR_kwDORsAV3c8AAAABS-H8pQ, submitted07:09:59Z, head42200d45: post-commentc952ed92 (09:13:38+0200) adds empty, extra, mixed-error scenarios and reason assertions at test:677-728; correct HTTP body status test:142,159; branch comment helper:465; updated explicit caller retry and unknown-body refusal SKILL.md:130-149. Failing/pending plus denied-inspection combination remains optional: nonempty rollups never inspect endpoints (helper:530-539). Function renaming/refactoring is optional; accurate new comment:431-435 and simplify review support retaining local function. Live-forge/body-shape limitations remain disclosed.
- Round3 review PRR_kwDORsAV3c8AAAABS-M73g, submitted07:19:29Z, same final head: four approving seats, documentation COMMENT. Historical error exists in isolated real erg output /tmp/1117-erg-diagnostic.txt; earlier Step1.5 diagnostic differs, so D1 remains a valid wording consideration, not declared fixed. Summary and detailed fallback describe different granularity; SKILL.md:139-149 states explicit empty-rollup delegation. Mirrored payload tests and shared `check` oracle remain optional; known-required payloads, nonzero and absence of direct merge jointly discriminate current behavior. No matrix row is claimed independently to prove a remote push: Case6 test:402-413 separately asserts it.
- Round4 review PRR_kwDORsAV3c8AAAABS-RNUQ, submitted07:27:11Z, same final head: both selected seats COMMENT, dissent preserved. D2 frontmatter Atomically is pre-existing (origin/main line3 verified) and remains a consider finding despite posted synthesis calling it nofollow; no claim of author fixing it. D3 absent-erg handling also unchanged. D4 fallback context/cross-reference and D5 literal gh diagnostic detail remain informational. D6 checkbox evidence verified directly against forge validate-tickets/collision SUCCESS, not inferred from ticket marks. D7 and regression#6 evidence gap resolved by exact-head full-gate log1702passed3skipped0failed58.69s; earlier failures/skips remain preserved. D8/regression#7 correlation accepted and recorded below. Raw malformed labels were not converted into verifiable bugs or hidden; round1 rule applies.
- Native review is CLEAN at exact SHA, observed OpenAI gpt-6.1-sol low, session01a15309-7ecf-7092-92b3-df3503b4b40e. Its bare git commands ran within the pinned supplied tree; outer anchor checks passed. This containment caveat remains recorded. Simplify portable CLEAN, no must-fix. No source changes occurred in gaze.
- High-risk cross-family requirement met by actual Anthropic reports: five distinct sessions each in rounds1-3 and two in round4. All17 identity files show canonicalModel claude-haiku-5-5/provider firstParty; requested medium, observed effort unavailable. Round4 sessions76a702df-409b-40e0-a09c-ef26ba34b3ea and8a8167df-f574-4a91-8d73-57c657809de9; earlier sessions retained in /tmp/raid1117-review-round{1,2,3}/*.identity.json. Producer OpenAI. These seats are lineage independent of producer and mutually correlated by model; no model diversity among panel seats is claimed. No required perspective unavailable. Gate seat is Codex same family as producer; gate does not claim separate cross-family independence.
- Scope: actual two-dot `git -C <tree> log origin/main..origin/raid-1117 --stat` has six commits and exactly four content-bearing paths. Helper implements criterion1/2; tests verify all three/invariants; SKILL.md documents recovery dependency; ticket records plan/verification. No overflow, below15-file breaker. No README catalog regeneration needed: no skill added/renamed/removed.

Posting: returned to gaze orchestrator for one combined final PR comment and readback; this contained gate writes only this artifact, no forge mutation, ticket write, commit, push or merge.


## Capture limits

No separate model revision was exposed. Anthropic effort was requested medium but not observed. The no-tool seats reviewed supplied public sources and did not execute tests or independently inspect live forge data. Their lineage differs from the OpenAI producer, but their model identity is shared with one another. Native review used bare Git inside the correct pinned worktree; before/after anchors passed. No real HTTP403 incident was recreated on GitHub.

## Backfill and close checks

Backfill: appended=0, no-match=0, unresolved=91; no historical coordinates were inferred. The unresolved historical records lack unambiguous per-record reviewed revisions.
Close check: 30 recent PRs, 15 claims across11PRs; no findings;2 unrecognised Ticket lines reported.
