# PR 1390 review evidence

Identity limitation: writer runtime exposes bare gpt-6.1-sol; Claude reports canonicalModel claude-sonnet-5-5 and provider firstParty; native headers expose model/provider separately. No verbatim provider-qualified full ID is exposed in these artifacts. All affected attribution identities use runtime-masked; no provider-qualified ID is reconstructed.

Merge confirmed by root: 2026-10-14T10:46:46Z; merge commit fea2413ae3e01cf40182463bee6030cf08826cb3. Approved source 58bee7ffefb10c32db7364f27ae0d36f1f2c6e2f; base ae72703fd000f5f011401fbe13a40e069c575fb1.

Writer: Codex runtime gpt-6.1-sol; effective effort not evidenced in supplied runtime context. Public audience: already-published PR findings and non-secret runtime identity/completion facts only.

## Original correctness context
Runtime result: {"type": "result", "subtype": "success", "session_id": "7160ae5d-4130-41e5-9212-1f5ef66e3592", "is_error": false, "duration_ms": 33421, "total_cost_usd": 0.1973618, "modelUsage": {"claude-sonnet-5-5": {"inputTokens": 10, "outputTokens": 3269, "cacheReadInputTokens": 179358, "cacheCreationInputTokens": 36679, "webSearchRequests": 0, "costUSD": 0.1973618, "contextWindow": 1000000, "maxOutputTokens": 128000, "thinkingTokens": 713, "canonicalModel": "claude-sonnet-5-5", "provider": "firstParty", "costBasis": "list"}}}
Requested effort medium; effective effort unavailable. Producer OpenAI; report mistakenly identifies producer Anthropic; posted synthesis corrects that attribution.
# Correctness seat — PR #1390 (anchor HEAD 40708b7bd6dc96597b1d7707732b735f0a4efa93)

Requested model claude-sonnet-5-5, Anthropic family, effort medium requested; effective runtime effort not evidenced.
Read: diff origin/main...HEAD (6 paths), closed ticket 1089, profile, guards. Ran only tests/test_pi_subagent_link.py: 7 passed. Whole suite not run (parent's gate). Not independent of the Anthropic-family author.

## Exit criteria
1. npm-global symlink links index.ts/agents.ts — met. `readlink -f` resolves the PATH `pi` symlink, the ancestor walk stops at `@earendil-works/pi-coding-agent`, `has_modules` checks both files, links resolve (test_npm_global_links_and_is_idempotent, run twice).
2. Neither layout → nonzero naming both attempts — met. scripts/pi-subagent-link:52 prints managed `marker -> candidate` and executable `path -> resolved -> candidate`; exit 1; no `extensions/` dir created (test asserts, absent and incomplete cases).
3. Managed current-version regression — met. Managed is tried first; a broken managed source falls through to the executable (test_managed_preferred_or_falls_back both params); managed-only works with no pi on PATH.
4. Caller criterion (annotated) — met. scripts/pi-haiku:27 drops `2>/dev/null`; `|| true` keeps continue-on-failure under `set -e`; `exec pi` argv and status unchanged. The test uses a copy of the real wrapper with a single asserted keyfile replacement and a synthetic key, and checks the diagnostic, exit 23 and exact argv. No credential reads in the diff.
5. 1095 stays open as a separate ticket (new file, not closed) — consistent with the deferral.

## Edge-case trace of the helper (set -euo pipefail)
- Empty or whitespace marker: candidate becomes `releases//…`, has_modules false, falls back. OK.
- `command -v pi || true` and `readlink -f … || true` cannot trip `-e`. OK.
- Ancestor loop terminates: `readlink -f` is absolute, so dirname reaches `/`. OK.
- First match of the package name ends the walk (`break`), so a nested same-named dir is not re-tried. Acceptable.

## Findings (no blockers)
- consider: behaviour change, intended by the ticket. The old helper exited 0 on a host with no Pi install (header said "so CI boxes pass"). It now exits 1 there. The only in-repo caller, pi-haiku, absorbs it with `|| true`, so CI is unaffected. Confidence high. Any future direct caller under `set -e` must handle the nonzero exit; grep found no such caller.
- consider: pi-haiku now prints the diagnostic on every start of a host with no usable subagent example, with no quiet mode. This is the intended "visible" requirement, so it is cosmetic noise at worst. Confidence medium.
- nofollow: `ln -sfn` still overwrites a regular file at `$dest/index.ts` without warning. It predates this diff and is out of scope. Confidence high.
- nofollow: `has_modules` tests `-f` then `-r` for each file. The redundancy is harmless, and `-r` guards against an unreadable file linking successfully.

No verifiable: failures found.

## Verdict: approve
Correctness perspective only; this is not a merge or gate verdict. Consistency, doc-propagation, red-team and scope perspectives are not covered by this artifact.


## Original consistency context
Runtime result: {"type": "result", "subtype": "success", "session_id": "4b3d2aae-7a47-4230-9db0-9c26a04c7ce6", "is_error": false, "duration_ms": 30471, "total_cost_usd": 0.19908969999999998, "modelUsage": {"claude-sonnet-5-5": {"inputTokens": 8, "outputTokens": 3316, "cacheReadInputTokens": 137737, "cacheCreationInputTokens": 38035, "webSearchRequests": 0, "costUSD": 0.19908969999999998, "contextWindow": 1000000, "maxOutputTokens": 128000, "thinkingTokens": 799, "canonicalModel": "claude-sonnet-5-5", "provider": "firstParty", "costBasis": "list"}}}
Requested effort medium; effective effort unavailable. Producer OpenAI; report mistakenly identifies producer Anthropic; posted synthesis corrects that attribution.
# PR #1390 — consistency seat

Anchor HEAD 40708b7bd6dc96597b1d7707732b735f0a4efa93; read `origin/main...HEAD` (6 paths) and the closed 1089 ticket.
Seat: code-reviewer / consistency. Requested model claude-sonnet-5-5, effort medium, Anthropic family; effective runtime effort not evidenced. Same-family only; not an independent review. Tests not run by this seat (parent reports GREEN 7 / fast 937 / adherence 185 / full gate).

## Exit criteria vs diff
- npm-global symlink links index.ts/agents.ts: met (scripts/pi-subagent-link ancestor walk to `@earendil-works/pi-coding-agent`; `test_npm_global_links_and_is_idempotent`).
- Neither layout → nonzero naming both attempts: met (line 52 message names marker→candidate and `pi on PATH: … -> …`; `test_failure_names_both_attempts_without_dangling_links`, both variants).
- Managed current-version regression: met (`test_managed_preferred_or_falls_back[False]`, `test_managed_without_executable`).
- Caller criterion: met. `2>/dev/null` removed at scripts/pi-haiku:27, `|| true` kept so flow continues to the final `exec pi`; test asserts diagnostic in stderr, argv exact, status 23, keyfile synthetic (single-replacement assert, HOME untouched).
- 1095 deferral: file present, label `deferred`, open, referenced accurately from 1089 evidence. Scope matches the ticket's planned five content paths (plus closed-path move).

## Findings
No blockers.

1. consider: skills/route/routes.json:81 (and skills/route/routes-recommendations-pi.md:11) still say the helper re-points links "from ~/.pi/agent/install/current-version" only; after this change it falls back to the PATH executable's package and fails nonzero when neither works. Confidence medium. Out of the ticket's declared scope, so doc-propagation seat's call; a one-clause edit would keep the route documentation consistent with the script.
2. consider: scripts/pi-haiku header comment is unchanged, and wrapper behaviour changes (setup failures are now visible on every start on hosts with no Pi tree, e.g. a stub-less CI box, instead of silent). This is the intended trade-off per the ticket; confidence high that it is deliberate. Nothing to change.
3. nofollow: test_failure_… non-incomplete variant asserts only the substring "PATH", not that a "not found" executable attempt is named; the incomplete variant covers the executable path. Confidence high; adequate for the criterion.
4. nofollow: ticket moved to tickets/closed/ with `Closed: implemented` and a log line, consistent with the other closed tickets' header format; the removed open copy and added closed copy are a rename in effect (diff shows delete + add; content of Context/Fix shape/criteria preserved, criteria ticked). Confidence high.

## Verdict
approve (consistency perspective only; same-family seat, not a merge or gate verdict).


## Original doc-propagation context
Runtime result: {"type": "result", "subtype": "success", "session_id": "ed1be837-6504-4b18-9f62-02beffa7eb77", "is_error": false, "duration_ms": 31207, "total_cost_usd": 0.1915596, "modelUsage": {"claude-sonnet-5-5": {"inputTokens": 8, "outputTokens": 3438, "cacheReadInputTokens": 137356, "cacheCreationInputTokens": 35857, "webSearchRequests": 0, "costUSD": 0.1915596, "contextWindow": 1000000, "maxOutputTokens": 128000, "thinkingTokens": 376, "canonicalModel": "claude-sonnet-5-5", "provider": "firstParty", "costBasis": "list"}}}
Requested effort medium; effective effort unavailable. Producer OpenAI; report mistakenly identifies producer Anthropic; posted synthesis corrects that attribution.
# Doc-propagation seat — PR #1390 (anchor 40708b7bd6dc96597b1d7707732b735f0a4efa93)

Reviewer: claude-sonnet-5-5, Anthropic family (same family as author; not independent). Effective effort: not evidenced. Read-only; diff read via `git -C <tree> diff origin/main...HEAD`. No test suite run.

## Criteria vs diff
- npm-global symlink links index.ts/agents.ts: scripts/pi-subagent-link ancestor walk; test_npm_global_links_and_is_idempotent. Met.
- Neither layout → nonzero naming both attempts: script line 52; test_failure_names_both_attempts... Met.
- Managed current-version regression: test_managed_without_executable, test_managed_preferred_or_falls_back. Met.
- Caller criterion (stderr visible, continue to Pi, exact argv, status; synthetic keyfile): scripts/pi-haiku:27 drops `2>/dev/null`, keeps `|| true`; test_wrapper_preserves_... asserts diagnostic, rc 23, argv. Met.
- 1095 stays open (Label: deferred, no Closed line); 1089 moved to tickets/closed with all boxes checked. Met.

## Findings

1. **medium confidence — stale description of the helper in routing docs (doc propagation miss).**
   - skills/route/routes.json:81 states `scripts/pi-subagent-link re-points them from ~/.pi/agent/install/current-version`; skills/route/routes-recommendations-pi.md:11 says the extension is "relinked by scripts/pi-subagent-link" (still true, less specific).
   - After this PR the helper's primary source is still current-version but it falls back to the `pi` executable's package root, and fails (nonzero, visible) instead of exiting 0. routes.json is a registry the route skill reads; its sentence is now incomplete, and it states the subagent door "verified on padme only", which the ticket cites as the cause.
   - Suggested: add "falling back to the package containing the pi executable on PATH (npm-global)" to routes.json:81. Not touched by the diff (unchanged lines), so treat as follow-up.
   - consider: update skills/route/routes.json:81 wording; low cost, no behaviour change. (If routes.json edits are gated by a registry/generation check, do it in a separate PR.)

2. **high confidence, minor — removed header contract not recorded elsewhere.** The old header promised "Exits 0 and says why when Pi is not installed, so CI boxes pass." The new helper exits 1 in that case. The only in-repo caller is scripts/pi-haiku:27 (`|| true`; grep of the tree shows no other invocation), so no CI box regresses; the ticket records the change (Fix shape, Actions 2–4). 
   - nofollow: behaviour change is intended and documented in the ticket; no other caller found.

3. **high confidence, minor — memory notes remain historical.** memory/topics/runtime-observations.md:30-31 and journal entries describe the pre-fix exit-0 behaviour. These are dated records (journal append-only); no edit expected.
   - nofollow: history, not instruction.

4. **medium confidence, minor — ticket closed before merge.** tickets/closed/1089…erg log shows `2026-10-14T09:38Z closed — implemented` and `Closed: implemented`, committed on the PR branch. This matches the repo's close-claim-in-PR convention (ticket moves with the merging PR), so only a note: if the PR is not merged, main keeps the ticket open (the deletion/move is on the branch only), which is correct.
   - nofollow.

5. **low confidence, minor — ticket scope statement vs paths.** Ticket says "two shell files, one test module and this ticket" and "at most five paths"; the PR touches six paths (adds 1095 ticket plus the open→closed move counted as two). 1095 is explicitly the deferred follow-up and justified in the ticket and commit 3bef62d9.
   - nofollow: disclosed, bounded.

6. consider: the ticket body (closed copy) retains the upstream issue link (earendil-works/pi#10932) and the user's `~/.local/bin` preference as required; confirm the PR description repeats them ("preserve in the delivery"), since the PR body was not available to this seat. Not verifiable from the tree.

## Missing perspective
PR body/description not read (not provided); full gate reported by parent, not re-run here.

## Verdict
**comment** — all four exit criteria and the caller criterion are met by the diff; one non-blocking doc-propagation gap (routes.json:81 still describes only the current-version layout).


## Runtime header 1390-native-root.log
OpenAI Codex v0.162.1
--------
workdir: /home/haduong/.agents/.claude/worktrees/raid-1089-prep
model: gpt-6.1-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a139e2-a856-7c90-a35c-3b8f6c576f84
--------

## Runtime header 1390-simplify-root.log
Reading additional input from stdin...
OpenAI Codex v0.162.1
--------
workdir: /home/haduong/.agents/.claude/worktrees/raid-1089-prep
model: gpt-6.1-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a139e5-34eb-7fe1-9783-ef5cecb3b6d4

## Runtime header 1390-final-gate.log
Reading additional input from stdin...
OpenAI Codex v0.162.1
--------
workdir: /home/haduong/.agents/.claude/worktrees/review-1390
model: gpt-6.1-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a139f0-71ea-7e60-a6cf-0da7924dcba1

## Runtime header 1390-complete.log
OpenAI Codex v0.162.1
--------
workdir: /home/haduong/.agents/.claude/worktrees/review-1390
model: gpt-6.1-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a13a00-fc2e-7790-ab65-673ae4fe7b25
--------

## Runtime header 1390-integration.log
OpenAI Codex v0.162.1
--------
workdir: /home/haduong/.agents
model: gpt-6.1-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a13a00-fc2e-7790-ab65-673ae4fe7b25
--------

## Runtime header 1390.log
OpenAI Codex v0.162.1
--------
workdir: /home/haduong/.agents/.claude/worktrees/review-1390
model: gpt-6.1-sol
provider: openai
approval: on-request
sandbox: workspace-write [workdir, /tmp, $TMPDIR] (network access enabled)
reasoning effort: medium
reasoning summaries: none
session id: 01a139d9-4a04-7152-8940-d3f1e3597c86
--------

## Published/reported verdict 1390-simplify-root.md
CLEAN — no actionable simplification findings.

Reviewed SHA: `40708b7bd6dc96597b1d7707732b735f0a4efa93`
Base: `84ef2a08d6276bcaf905a68b712f9650df3d8a27`

Examined the complete six-path diff: both shell scripts, `tests/test_pi_subagent_link.py`, the removed/open and added/closed 1089 ticket paths, and ticket 1095, plus surrounding scripts and test utilities.

Specific candidates considered:

- Discovery nesting and ancestor traversal: preserve managed precedence, executable resolution and diagnostic context; extraction would add indirection.
- Repeated source validation: already reused through `has_modules`.
- Managed-install setup duplicated in two tests: too small to justify another helper.
- Wrapper-copy fixture: keeps credential isolation while exercising the actual wrapper.
- Existing utility reuse: `child_env()` is already used; no suitable shared package-discovery helper found.

Bash syntax checks passed. Integration tests were inspected, not executed. HEAD matched before and after; working tree remained clean. No edits, commits, pushes or forge actions.

## Published/reported verdict 1390-prior-gate.md
# /verify-gate verdict

```yaml
verdict: ESCALATE
round: 1
pr: 1390
ticket: 1089
gate_session_id: 7986404d-f8e2-439d-b014-3c84ced9beaa
review_worktree_path: /home/haduong/.agents/.claude/worktrees/review-1390
ruled_tip_sha: 40708b7bd6dc96597b1d7707732b735f0a4efa93
base_sha: 84ef2a08d6276bcaf905a68b712f9650df3d8a27
per_exit_criterion:
  - criterion: "`scripts/pi-subagent-link` links the subagent extension and agents on an npm-global install (fixture: `pi` symlink into a `node_modules/@earendil-works/pi-coding-agent` tree)"
    status: ADDRESSED
    evidence: "da217da60303fcb11f42ddf1fcbd5a9eab851525 scripts/pi-subagent-link:28-45,56-59; tests/test_pi_subagent_link.py::test_npm_global_links_and_is_idempotent (line 61), real symlink fixture at line 39 and link assertions at line 53. Recorded focused GREEN 7 and exact-head full check 1585 passed/4 skipped."
  - criterion: "With neither layout present it exits non-zero with a message naming both paths it tried"
    status: ADDRESSED
    evidence: "da217da60303fcb11f42ddf1fcbd5a9eab851525 scripts/pi-subagent-link:8-10,26-31,51-53 names managed marker and executable/PATH attempt; tests/test_pi_subagent_link.py::test_failure_names_both_attempts_without_dangling_links (line 97), absent and incomplete parameters assert nonzero, both attempts and no destination creation."
  - criterion: "The existing `current-version` layout still works (regression test)"
    status: ADDRESSED
    evidence: "da217da60303fcb11f42ddf1fcbd5a9eab851525 scripts/pi-subagent-link:17-24 preserves managed-first lookup; tests/test_pi_subagent_link.py::test_managed_preferred_or_falls_back (line 70), ::test_managed_without_executable (line 86). Recorded focused and full results reused at unchanged exact HEAD."
unresolved_review_comments: []
malformed_minors: []
unresolved_simplify_findings: []
unresolved_adherence_violations: []
scope_overflow:
  - file: tickets/1095-tmp-lifecycle-task-owned-cleanup-and-cra.erg
    reason: "Outside 1089 implementation criteria but explicitly author-authorized deferred related follow-up; not a close claim."
    suggested_disposition: TICKETED
phase_gaps:
  - phase: native-review
    status: NOT-RUN
    evidence: ".panel/1390/native-review.md records read-only filesystem app-server initialization failure before review execution."
  - phase: simplify
    status: MISSING
    evidence: "Prompt exists, no completed simplify result available when ruling; absence is not a clean simplify pass."
root_cause_class: Missing Data
rationale: |
  All three contractual criteria have concrete code and regression evidence; no blocking code finding or adherence violation is established. Nevertheless required native review and simplify evidence is unavailable, so full Gaze cannot be approved. Prior cross-family review is retained with the documentation seat's COMMENT dissent, not relabeled approval. Gate round is 1: saved comments/inline arrays are empty and the sole saved review has no /verify-gate round=N verdict=V marker. Review-pr round 2 in scoped.md is a perspective-review count, not gate round 2. Startup errors are NOT-RUN, never completed seats.
```

Exit criteria: 3/3. Review blockers: 0. Simplify must-fix findings known: 0, but phase evidence missing. Adherence blocking: 0. Scope overflow: 1 already-ticketed authorized deferred follow-up. Minors: verifiable 0, consider 6, nofollow 8, malformed 0.

Evidence reused per explicit author instruction: full exact-head `make check` 1585 passed / 4 skipped in 111.97s; adherence `make -n lint` and `make lint` 185 passed; focused 7 and fast 937. No tests repeated. `.panel/1390/adherence.md` validates Makefile:31-32 runner declaration, no semantic residue, same anchor. Full suite result comes from recorded prior review, not a new measurement.

## Every prior finding and its disposition

References below identify the raw seat reports in `/tmp/raid1089-review-record`, also preserved in forge review PRR_kwDORsAV3c8AAAABSMhAiw (.panel/1390/pr.json).

| Comment reference | Tag | Byte/rule validation and disposition |
|---|---|---|
| correctness.md finding 1, missing Pi now nonzero | consider | Intentional criterion 2; helper:51-53 and pi-haiku:27 `|| true` substantiate the posted rationale. Informational. |
| correctness.md finding 2, repeated visible diagnostic | consider | pi-haiku:27 removes stderr discard; visibility is explicitly required in closed 1089 Actions 4. Informational. |
| correctness.md finding 3, symlink overwrite | nofollow | helper:59 `ln -sfn` is unchanged versus base. Pre-existing, muted. |
| correctness.md finding 4, file/read checks | nofollow | helper:13-14 both `-f` and `-r` validate source modules. Harmless, muted. |
| consistency.md finding 1, route-cache description | consider | routes.json:81 retains managed-source description; helper:17-24 still implements that source and :28-45 adds fallback. Wording omits fallback. Keep optional doc dissent; posted author rationale cites bounded scope and unchanged historical host evidence. |
| consistency.md finding 2, wrapper header/visibility | consider | pi-haiku:27 and closed ticket Actions 4 establish deliberate visible diagnostic. Informational. |
| consistency.md finding 3, missing-source test substring | nofollow | test:102-108 asserts marker, PATH and nonzero; helper:26 explicitly names not found. Adequate criterion coverage, muted. |
| consistency.md finding 4, closed-ticket move | nofollow | open file deleted, closed copy has Closed:implemented; PR sole close claim names existing closed copy. Main retains open ticket until merge. Muted. |
| doc-propagation.md finding 1, route wording | consider | Same validated omission as consistency 1. routes-recommendations-pi.md:11 merely says helper relinks; that sentence stays true. Doc seat COMMENT persists; optional registry expansion dismissed in posted rationale, not repaired. |
| doc-propagation.md finding 2, removed exit-zero contract | nofollow | Former header replaced with accurate nonzero contract at helper:2-4; closed ticket Fix shape/Actions explicitly requires nonzero. Muted. |
| doc-propagation.md finding 3, historical memory | nofollow | Dated historical facts do not become current implementation instructions; append-only memory boundary applies. Muted. |
| doc-propagation.md finding 4, closure before merge | nofollow | Closure is branch-local ticket move in diff, not main mutation. Muted. |
| doc-propagation.md finding 5, six paths | nofollow | Two scripts + test + open/closed ticket paths map to 1089; sixth is author-requested deferred 1095 committed in 3bef62d9. Its Label:deferred and lack of Closed field corroborate related-follow-up disposition. Muted. |
| doc-propagation.md finding 6, delivery preferences/link | consider | Saved PR body explicitly includes ~/.local/bin, upstream issue10932 and only1089-closes/1095-deferred statements. Confirmed, addressed. |

No post-review fix commits exist: last commit 09:42:10Z precedes posted review 09:47:37Z. Consider comments are informational under skill rules; author dispositions were included in the posted review and validated above. No resolved marker is invented.

Prior three-seat provenance: reports requested Claude Sonnet5.5/medium; manifest and summary record Anthropic runtime canonicalModel and unavailable effective effort. Summary corrects raw reports' mistaken Anthropic author attribution to OpenAI Sol6.1. Cross-family prior panel is therefore retained. scoped.md's phrase “prior panel's recorded same-family provenance” is incorrect; do not carry it forward as evidence. Scoped doc/regression recheck is a local same-family review, not new independently decorrelated seats. Prior raw verdicts remain correctness approve, consistency approve, documentation comment. Public repository status is directly recorded in repo.json (`isPrivate:false`); no privacy violation follows merely from public historical host facts.

Scope inspected against exact base..anchor commit history. Two shell paths and tests implement/verify criteria; open/closed 1089 paths record the contract and closure; deferred1095 is authorized and already ticketed. Gate made no source, ticket, git, or forge mutation. No PR comment posted; caller owns publication.
{"headRefOid":"40708b7bd6dc96597b1d7707732b735f0a4efa93","state":"OPEN"}

hook: PreToolUse
hook: PreToolUse Completed

## Published/reported verdict 1390-complete.md
APPROVED

```yaml
verdict: APPROVED
round: 1
pr: 1390
ticket: 1089
gate_mode: completion-of-interrupted-initial-gate
gate_session_id: 7986404d-f8e2-439d-b014-3c84ced9beaa
review_worktree_path: /home/haduong/.agents/.claude/worktrees/review-1390
ruled_tip_sha: 3892b281456aa506b0aa99036cc9943cfba1547f
base_sha: 718d6fb9d05b3014e92381e88eeb55039adfa50b
previous_reviewed_tip: 40708b7bd6dc96597b1d7707732b735f0a4efa93

per_exit_criterion:
  - criterion: "`scripts/pi-subagent-link` links the subagent extension and agents on an npm-global install (fixture: `pi` symlink into a `node_modules/@earendil-works/pi-coding-agent` tree)"
    status: ADDRESSED
    evidence: >-
      3892b281456aa506b0aa99036cc9943cfba1547f:
      scripts/pi-subagent-link:28-45,56-59;
      tests/test_pi_subagent_link.py:39-45,53-66,
      test_npm_global_links_and_is_idempotent.
  - criterion: "With neither layout present it exits non-zero with a message naming both paths it tried"
    status: ADDRESSED
    evidence: >-
      3892b281456aa506b0aa99036cc9943cfba1547f:
      scripts/pi-subagent-link:8-10,26-31,51-53;
      tests/test_pi_subagent_link.py:96-108,
      test_failure_names_both_attempts_without_dangling_links,
      absent and incomplete parameters.
  - criterion: "The existing `current-version` layout still works (regression test)"
    status: ADDRESSED
    evidence: >-
      3892b281456aa506b0aa99036cc9943cfba1547f:
      scripts/pi-subagent-link:17-24;
      tests/test_pi_subagent_link.py:69-93,
      test_managed_preferred_or_falls_back and
      test_managed_without_executable.

snapshot_validation:
  result: EQUAL
  method: Compared git blob IDs for every current PR changed path against previous_reviewed_tip.
  blobs:
    scripts/pi-haiku: 5189ac7845e2b835607f4b4aba44ec87b638dce6
    scripts/pi-subagent-link: a9dbb293dd7a27196d2afb7a652401b725aad56c
    tests/test_pi_subagent_link.py: 370bfe15073fd95bbb55bee4b70196d1e8bbae92
    tickets/1089-pi-subagent-link-no-ops-on-an-npm-global.erg: ABSENT
    tickets/1095-tmp-lifecycle-task-owned-cleanup-and-cra.erg: 79a1ef41e8c6d314f4d7047bd38ee4e6b27c8697
    tickets/closed/1089-pi-subagent-link-no-ops-on-an-npm-global.erg: 57d0032cd1ad94e8ba702865b444161bca0854bb
  base_delta: >-
    Compared old base 84ef2a08d6276bcaf905a68b712f9650df3d8a27
    with current base: only ticket 1096 and its factual journal changed.
    No implementation, test or runtime-rule change invalidates prior evidence.

review_inventory:
  forge_review: PRR_kwDORsAV3c8AAAABSMhAiw
  live_issue_comments: 0
  live_inline_comments: 0
  provenance: >-
    Recorded actual three-seat Claude Sonnet 5.5 panel; medium effort
    requested, effective effort unavailable. Producer OpenAI Sol 6.1;
    raw reports' incorrect author-family statements are corrected by
    the posted summary. Cross-family panel retained.
  verdicts:
    correctness: approve
    consistency: approve
    doc-propagation: comment

comment_dispositions:
  - comment_ref: correctness.md#finding-1
    tag: consider
    disposition: INTENTIONAL
    evidence: "Criterion 2; helper:51-53; pi-haiku:27 absorbs setup failure."
  - comment_ref: correctness.md#finding-2
    tag: consider
    disposition: INTENTIONAL
    evidence: "pi-haiku:27; closed 1089 Actions 4 requires visible diagnostics."
  - comment_ref: correctness.md#finding-3
    tag: nofollow
    disposition: MUTED_PREEXISTING
    evidence: "helper:59 ln -sfn unchanged from base."
  - comment_ref: correctness.md#finding-4
    tag: nofollow
    disposition: MUTED
    evidence: "helper:13-14 validates regular readable source modules."
  - comment_ref: consistency.md#finding-1
    tag: consider
    disposition: DISMISSED_WITH_POSTED_RATIONALE
    evidence: >-
      routes.json:81 still describes the supported managed source.
      Posted review bounds registry expansion outside this ticket.
      Fallback wording remains incomplete; not claimed repaired.
  - comment_ref: consistency.md#finding-2
    tag: consider
    disposition: INTENTIONAL
    evidence: "pi-haiku:27; closed 1089 Actions 4."
  - comment_ref: consistency.md#finding-3
    tag: nofollow
    disposition: MUTED
    evidence: "test:102-108 checks nonzero, marker and PATH; helper:26 names not found."
  - comment_ref: consistency.md#finding-4
    tag: nofollow
    disposition: MUTED
    evidence: "Branch-local open/closed ticket move; Closed: implemented; close target exists."
  - comment_ref: doc-propagation.md#finding-1
    tag: consider
    disposition: DISMISSED_WITH_POSTED_RATIONALE
    evidence: >-
      Optional routes.json:81 expansion remains outstanding as documentation
      dissent. routes-recommendations-pi.md:11 remains true.
      Posted bounded-scope rationale validated.
  - comment_ref: doc-propagation.md#finding-2
    tag: nofollow
    disposition: MUTED
    evidence: "helper:2-4; closed 1089 Fix shape and Actions record nonzero contract."
  - comment_ref: doc-propagation.md#finding-3
    tag: nofollow
    disposition: MUTED_HISTORICAL
    evidence: "Dated memory is historical; append-only boundary retained."
  - comment_ref: doc-propagation.md#finding-4
    tag: nofollow
    disposition: MUTED
    evidence: "Ticket closure exists only on PR branch until merge."
  - comment_ref: doc-propagation.md#finding-5
    tag: nofollow
    disposition: MUTED_AUTHORIZED_SCOPE
    evidence: "Six paths include explicitly authorized deferred 1095; no close claim for 1095."
  - comment_ref: doc-propagation.md#finding-6
    tag: consider
    disposition: ADDRESSED
    evidence: "Live PR body includes ~/.local/bin, upstream issue 10932 and open deferred 1095."

unresolved_review_comments: []
malformed_minors: []
unresolved_simplify_findings: []
unresolved_adherence_violations: []
scope_overflow:
  - file: tickets/1095-tmp-lifecycle-task-owned-cleanup-and-cra.erg
    reason: "Explicitly user-authorized related deferred follow-up; remains open."
    suggested_disposition: TICKETED

phase_evidence:
  prior_gate:
    artifact: /tmp/idh-final-gazes/1390-prior-gate.md
    result: "ESCALATE solely for missing native-review and simplify evidence."
  native_review:
    status: COMPLETE
    artifact: /tmp/idh-final-gazes/1390-native-root.log
    reviewer: gpt-6.1-sol
    effort: low
    session: 01a139e2-a856-7c90-a35c-3b8f6c576f84
    result: "Completed concrete behavior inspection; no actionable defects."
  simplify:
    status: COMPLETE
    artifact: /tmp/idh-final-gazes/1390-simplify-root.md
    execution_log: /tmp/idh-final-gazes/1390-simplify-root.log
    result: "CLEAN; all six paths; pre/post HEAD 40708b7bd6dc96597b1d7707732b735f0a4efa93."
  adherence:
    status: PASS_REUSED
    evidence: >-
      Prior verified gate, live posted review and closed ticket record
      declared lint runner: 185 passed; no required uncovered semantic residue.
      Original .panel artifact is absent from this worktree.
  tests:
    status: REUSED_UNCHANGED_BLOBS
    evidence: >-
      Exact 40708 snapshot: full 1585 passed / 4 skipped;
      focused 7 passed; fast 937 passed.
      No tests rerun by this gate.
  failed_attempts:
    - "Prior native bootstrap failure remains FAILED/unavailable; not completed review."
    - "Prior full semantic timeouts remain FAILED; not clean semantic passes."
  privacy_objection:
    disposition: REFUTED
    evidence: "Live gh repo view confirms MinhHaDuong/ImperialDragonHarness isPrivate=false."

phase_gaps: []
publication:
  pr_comment_posted: false
  owner: caller
merge_constraint: "Forge required checks still gate merge; this verdict does not merge."

rationale: >-
  All three criteria have actual code and regression anchors. Every changed
  blob equals the previously tested and reviewed snapshot. The recovered
  native review and separate simplify execution close the interrupted gate's
  only required phase gaps. All fourteen prior findings retain explicit
  dispositions, including the optional routing-documentation dissent.
  Failed attempts remain failures. No blocking finding, adherence violation
  or unexplained scope expansion remains.
```

## Published/reported verdict 1390-integration.md
APPROVED

```yaml
verdict: APPROVED
round: 1
pr: 1390
ticket: 1089
mode: scoped-source-and-base-refresh
gate_session_id: 01a13a00-fc2e-7790-ab65-673ae4fe7b25
ruled_tip_sha: 58bee7ffefb10c32db7364f27ae0d36f1f2c6e2f
base_sha: ae72703fd000f5f011401fbe13a40e069c575fb1
prior_approved_tip: 3892b281456aa506b0aa99036cc9943cfba1547f
blob_comparison: "All six changed paths identical to prior approved tip."
union_preserved: "1080 skill/docs/tests match current base; 1089 scripts/tests/tickets retain approved blobs."
per_exit_criterion:
  - criterion: npm-global extension and agents linking
    status: ADDRESSED
    evidence: "Current tip helper:28-45,56-59; test_npm_global_links_and_is_idempotent."
  - criterion: Neither layout exits nonzero naming both attempts
    status: ADDRESSED
    evidence: "Current tip helper:8-10,26-31,51-53; test_failure_names_both_attempts_without_dangling_links."
  - criterion: Existing current-version layout regression
    status: ADDRESSED
    evidence: "Current tip helper:17-24; test_managed_preferred_or_falls_back; test_managed_without_executable."
review_dispositions: "All 14 retained; documentation COMMENT dissent preserved."
unresolved_review_comments: []
malformed_minors: []
unresolved_simplify_findings: []
unresolved_adherence_violations: []
scope_overflow:
  - file: tickets/1095-tmp-lifecycle-task-owned-cleanup-and-cra.erg
    reason: Explicitly authorized deferred follow-up; remains open.
    suggested_disposition: TICKETED
phase_gaps: []
verification:
  union_ci: "1588 passed, 10 skipped; nine jobs passed."
  collision: "Synthetic-event self-collision failed; separate actual PR1390 event passed."
  tests_rerun: false
  prior_failed_attempts: "Remain FAILED; not relabeled completed."
provenance_correction: "7986404d belonged to a different interrupted gate attempt."
publication:
  comment: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1390#issuecomment-6166565226
  readback_matches: true
rationale: >-
  Nonoverlapping merged base changes preserve prior evidence. Updated adherence
  applicability introduces no required semantic run for this unchanged script
  diff. Required native-review and simplify evidence remains valid.
merge_performed: false
merge_constraint: Forge required checks still apply.
```

## Initial gaze attempted context outcomes
Initial orchestrator CLI session 01a139d9-4a04-7152-8940-d3f1e3597c86: actual medium reasoning header. Required native-review bootstrap failed twice before a review context initialized; attempts are failed, not ran. Native Luna adherence and scoped doc/regression completed with requested medium; effective identity/effort not independently exposed in supplied trail. Initial gate emitted ESCALATE for missing required phases; its UUID7986404d-f8e2-439d-b014-3c84ced9beaa is a gate coordination ID, not the recovered session ID. A subsequent medium Sol gate session01a139f0-71ea-7e60-a6cf-0da7924dcba1 was interrupted without completion.
WARNING: proceeding, even though we could not create PATH aliases: Read-only file system (os error 30)
Error: failed to initialize in-process app-server client: Read-only file system (os error 30)
adherence: PASS
head: 40708b7bd6dc96597b1d7707732b735f0a4efa93
base: 84ef2a08d6276bcaf905a68b712f9650df3d8a27
mechanical_failures: []
semantic_findings: []
untested_rules: []
evidence:
  project_runner:
    declaration: Makefile:31-32 documents the adherence gate as mechanical grep/AST ratchets and hygiene checks; `lint` runs `$(RUN) python3 -m pytest tests/ -m adherence`.
    dry_run: `make -n lint` PASS (recorded by exact-head prior gate in .panel/1390/pr.json).
    execution: `make lint` PASS, 185 passed (recorded by exact-head prior gate in .panel/1390/pr.json).
    full_gate: `make check` via scripts/raid-gate.py PASS, 1585 passed, 4 skipped (111.97s), same exact HEAD and recorded in .panel/1390/pr.json.
    reuse: Author explicitly directed reuse; unchanged HEAD verified. No checks rerun.
  reference_resolution: skipped; changed files contain no .tex, .qmd, or .bib sources.
  semantic_fallback: not required; no .claude/rules/*.md changed and the shell behavior is covered by declared mechanical tests. Existing doc-propagation comment is retained for the separate scoped review.
  path_access_scan: skipped; no trace= input supplied.
# Scoped review — PR #1390, round 2

Anchor: HEAD 40708b7bd6dc96597b1d7707732b735f0a4efa93; base 84ef2a08d6276bcaf905a68b712f9650df3d8a27. Round 2 follows the one prior posted review in `.panel/1390/pr.json`. The exact HEAD is unchanged from that review, so this is a scoped recheck and does not rewrite or supersede its verdicts.

## Prior doc-propagation comment

Prior verdict: **comment**, optional consideration that `skills/route/routes.json:81` still describes only the managed `~/.pi/agent/install/current-version` source, omitting the PATH-resolved npm package fallback and nonzero failure behavior. Rechecked the exact-head diff and prior rationale: the final commit only clarifies the deferred 1095 ticket title/body; it does not alter the helper or routing documentation. The wording remains incomplete as a description of all helper behavior. Keep the dissent visible as `consider:` / optional follow-up, not a blocker. Prior disposition remains that this registry edit is outside the bounded 1089 ticket scope (and may merit its own PR if registry edits are gated). The PR body documents the npm fallback, while the route registry sentence itself remains unchanged.

## Regression check for cleared correctness and consistency perspectives

One combined regression check covers the correctness and consistency perspectives that approved in round 1, as required for round N>1. It checks only whether changes since that review broke approved behavior. The final delta is documentation/ticket wording only; the unchanged code and tests remain anchored at the same HEAD. The exact-head prior review records the exit criteria as met: managed-first behavior and npm fallback, complete-module validation before linking, useful nonzero diagnostics when both sources fail, wrapper diagnostic visibility while preserving continuation/argv/status, and the open deferred 1095 follow-up. No regression identified. This is the required scoped regression coverage, not a newly independent correctness or consistency review.

Roster for this scoped pass: doc-propagation — comment (same optional consideration, still outstanding); combined regression of prior correctness + consistency approvals — pass, no regression found. The prior panel's recorded same-family provenance and doc-propagation dissent remain intact.
git rev-parse --show-toplevel               # FIRST: confirm cwd is the session
s=p/'scoped.md'
s.write_text(s.read_text()+'''\\nOrchestrator correction: the prior posted review already ruled on this same final HEAD; there is no code or ticket delta since that review. Original raw seats mislabeled the producer Anthropic; the posted review corrects producer to OpenAI Sol6.1. Actual canonicalModel records are claude-sonnet-5-5, so original completed seats are cross-family, while this scoped Luna seat is same-family replication. Their findings and doc comment remain unchanged.\\n''')
(p/'phase-status.md').write_text('Required phases: adherence PASS native Luna medium; scoped Agent C doc-propagation comment + one cleared-angle regression completed native Luna medium; portable simplify CLEAN native Sol6.1 low both anchors PASS. Required native /review NOT-RUN: two pinned Sol6.1 low read-only CLI attempts failed initialize in-process app-server client with Read-only file system before review; sqlite_home/log_dir confined-panel retry also failed. No fabricated clean review. Gate must ESCALATE for phaseB infrastructure gap, all3ticketcriteria may be ADDRESSED. Prior exacthead full makecheck1585passed4skipped and make lint185 reused. Prior3Claude canonicalModel claude-sonnet-5-5 cost0.5880111 crossfamily. Diff-check trailing blank EOF1095:43 is nonblocking formatting nit. No changes. Cleanup limited by author no-writes-outside-panel; retain registered reviewtree.')
PY
python3 /home/haduong/.agents/scripts/prose_predicate.py --risk scripts/pi-haiku scripts/pi-subagent-link tests/test_pi_subagent_link.py tickets/1089-pi-subagent-link-no-ops-on-an-npm-global.erg tickets/1095-tmp-lifecycle-task-owned-cleanup-and-cra.erg tickets/closed/1089-pi-subagent-link-no-ops-on-an-npm-global.erg; git rev-parse --show-toplevel HEAD; git status --porcelain; git branch --show-current; python3 /home/haduong/.agents/scripts/worktree-exit-preflight.sh --help" in /home/haduong/.agents/.claude/worktrees/review-1390

## Coder-panel startup attempts
Automatic approval first rejected Claude disclosure; public-repository proof resolved its premise and retry was accepted. First two CLI processes2199193/2199195 exited before review because variadic tool arguments consumed the positional prompt. Corrected stdin processes2228203/2228206 completed, then documentation process2260605 completed. A native spawn request failed agent thread limit before any reviewer context launched. No failed startup is reported as a completed review.

## Completion provenance correction
Recovered gate actual session01a13a00-fc2e-7790-ab65-673ae4fe7b25 completed, then resumed the SAME context for fresh-base refresh. Initial complete.md incorrectly copied7986404d; integration.md and runtime headers correct it. Fresh-base APPROVED comment6166565226. All six changed blobs equal original40708b7 and prior3892b281. Documentation consider remains dismissed, not fixed.

## Controller completion correction
Initial gaze controller session01a139d9-4a04-7152-8940-d3f1e3597c86 timed out, exit124. Its global attempt is failed; separately completed subordinate reviews remain ran. The earlier initial-gaze narrative described its partial work, not successful overall completion.

Identity evidence for writer: Codex task runtime names bare gpt-6.1-sol, without verbatim provider-qualified full ID; effective effort not exposed.

Identity evidence for claude-panel-preflight: This failed/preflight attempt never established a running reviewer identity; requested routing identity is evidence only, not an observed worker model. No verbatim full ID available; failed/skipped status is retained, no completed review inferred.

Identity evidence for claude-correctness-startup-2199193: This failed/preflight attempt never established a running reviewer identity; requested routing identity is evidence only, not an observed worker model. No verbatim full ID available; failed/skipped status is retained, no completed review inferred.

Identity evidence for claude-consistency-startup-2199195: This failed/preflight attempt never established a running reviewer identity; requested routing identity is evidence only, not an observed worker model. No verbatim full ID available; failed/skipped status is retained, no completed review inferred.

Identity evidence for native-correctness-spawn: This failed/preflight attempt never established a running reviewer identity; requested routing identity is evidence only, not an observed worker model. No verbatim full ID available; failed/skipped status is retained, no completed review inferred.

Identity evidence for correctness-7160ae5d: Actual Claude completed context identified by its session UUID and canonicalModel claude-sonnet-5-5/provider firstParty above; verbatim provider-qualified full ID absent. Requested medium, effective effort unavailable.

Identity evidence for consistency-4b3d2aae: Actual Claude completed context identified by its session UUID and canonicalModel claude-sonnet-5-5/provider firstParty above; verbatim provider-qualified full ID absent. Requested medium, effective effort unavailable.

Identity evidence for doc-propagation-ed1be837: Actual Claude completed context identified by its session UUID and canonicalModel claude-sonnet-5-5/provider firstParty above; verbatim provider-qualified full ID absent. Requested medium, effective effort unavailable.

Identity evidence for gaze-01a139d9: Actual context and completion/interruption status established in named native CLI header/verdict above; runtime prints bare gpt-6.1-sol and provider openai in separate fields, without verbatim provider-qualified full ID. Header reasoning effort is preserved, never reconstructed from aliases.

Identity evidence for adherence-native-luna: Actual completed subordinate role is established by initial-gaze report; requested bare gpt-6-luna/medium, actual full model ID and effective effort not exposed in the supplied role trail. Missing subordinate context UUID remains unavailable, not inferred.

Identity evidence for scoped-doc-regression-native-luna: Actual completed subordinate role is established by initial-gaze report; requested bare gpt-6-luna/medium, actual full model ID and effective effort not exposed in the supplied role trail. Missing subordinate context UUID remains unavailable, not inferred.

Identity evidence for native-review-bootstrap-first: This failed/preflight attempt never established a running reviewer identity; requested routing identity is evidence only, not an observed worker model. No verbatim full ID available; failed/skipped status is retained, no completed review inferred.

Identity evidence for native-review-bootstrap-confined-retry: This failed/preflight attempt never established a running reviewer identity; requested routing identity is evidence only, not an observed worker model. No verbatim full ID available; failed/skipped status is retained, no completed review inferred.

Identity evidence for native-review-01a139e2: Actual context and completion/interruption status established in named native CLI header/verdict above; runtime prints bare gpt-6.1-sol and provider openai in separate fields, without verbatim provider-qualified full ID. Header reasoning effort is preserved, never reconstructed from aliases.

Identity evidence for simplify-01a139e5: Actual context and completion/interruption status established in named native CLI header/verdict above; runtime prints bare gpt-6.1-sol and provider openai in separate fields, without verbatim provider-qualified full ID. Header reasoning effort is preserved, never reconstructed from aliases.

Identity evidence for gate-01a139f0-interrupted: Actual context and completion/interruption status established in named native CLI header/verdict above; runtime prints bare gpt-6.1-sol and provider openai in separate fields, without verbatim provider-qualified full ID. Header reasoning effort is preserved, never reconstructed from aliases.

Identity evidence for gate-01a13a00-completion: Actual context and completion/interruption status established in named native CLI header/verdict above; runtime prints bare gpt-6.1-sol and provider openai in separate fields, without verbatim provider-qualified full ID. Header reasoning effort is preserved, never reconstructed from aliases.

Identity evidence for gate-01a13a00-completion: Actual context and completion/interruption status established in named native CLI header/verdict above; runtime prints bare gpt-6.1-sol and provider openai in separate fields, without verbatim provider-qualified full ID. Header reasoning effort is preserved, never reconstructed from aliases.
