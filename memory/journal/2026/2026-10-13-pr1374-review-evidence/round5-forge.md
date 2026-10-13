# PR 1374 review round 5

Forge review: PRR_kwDORsAV3c8AAAABR23WVA
Reviewed commit: 3424fb345d807c00338f33c495eae07e34cc3216
Submitted: 2026-10-12T16:09:43Z

## /review-pr round 5 — PR #1374 (RE-GAZE round 3)

Reviewed HEAD: `3424fb345d807c00338f33c495eae07e34cc3216`; base `origin/main`. Parent live review-anchor passed before and after the battery. Size: 8 content-bearing files / 1019 lines; high risk (`scripts/**`, `skills/**`). Previous review roster selects consistency + red team + scope + single correctness/doc regression. Four distinct Pi reviewer contexts completed through functions.subagent in one parallel call; no simulated seats.

PANEL-INTEGRITY: DEGRADED — native /review NOT-RUN/unavailable: missing built-in general-review perspective. Four perspective contexts: agent-file pin openrouter/~openai/gpt-sol-latest, OpenAI versus recorded Anthropic producer, functions.subagent; evidence actual four SHA-specific reports, before/after HEAD and explicit full/fix diff analysis. Exact resolved model/version/effort not exposed, benched pair not established. Adherence: separate worker, openrouter/~anthropic/claude-sonnet-latest/high, live contract + make lint182 passed; Sonnet high differs from grid medium. Reviewer profile forbids writes, so no artifact/manifest polling; reports collected through actual blocking tool completion. Scratch evidence is under /tmp/regaze-1374-DxgC0I, not .panel, under caller no-repo-edit rail. Fresh review worktree creation/removal NOT-RUN under caller containment rails. Correctness/doc propagation represented by regression, not separately repeated. Optional external panel not selected.

### Blocking findings (independently injected by parent using current script and real Git in /tmp)
1. **Human-output parser loses recovery identity with legal Git configuration** — `skills/roar/close-and-clean.sh:241–251`. Configure `core.abbrev=4`, move topic A→unmerged B at branch-D entry, let real Git delete: output `Deleted branch topic (was 8047).`; parser requires7+ hex, reports unknown/not-restorable2; topic ABSENT. Rewriting successful deletion output to a different format independently yields2/ABSENT. LC_ALL=C fixes language, not abbreviation/protocol. Failing parse signals failure but is not preservation-safe because destruction precedes it. Consistency/red team/regression independently object.
2. **Recovery accepts tag-shadowed abbreviation** — `skills/roar/close-and-clean.sh:189–190`. B=`8047bee15dcfbca49e222f37f579d34bd6679458`; tag `8047bee` points to C=`848a5a57fb906f862648c7c39731e2310d1e9c2e`. Real Git deleted B, helper resolves the tag and recreates topic at C; rc1 falsely says `restored at 8047bee`. The existing base-shadow fix remains effective, but new restoration reintroduces revision-name DWIM. Red team/regression independently object.
3. **Delete-and-compensate loses unprobed branch on interruption and loses branch metadata even on success** — `skills/roar/close-and-clean.sh:234–251`. Wrapper moves A→B immediately before real branch-D, then SIGKILLs the root sweep after delete: rc=-9, topic ABSENT, reflog absent, `for-each-ref --contains B` empty. Separate normal completion restores B/rc1 but clears branch.topic.remote/merge and replaces old reflog. Not equivalent to refusing an unapproved tip before deletion. Red team/consistency object. Cheap pre-delete full-OID equality check is missing and **blocking as a minimum mitigation**: scratch-only control moving immediately after probe preserves B plus upstream/reflog with that check, whereas current script deletes/recreates B and loses metadata. That check alone does NOT close the final check/delete race; require fail-closed local deletion or durable/coordination-based protection of the remaining window, not another claimed CAS based on compensation.

### Verified fixes / safe behaviors
- Late peer worktree: current branch-D refuses inside delete, rc1, topic and peer intact. Suite section16's unsafe update-ref control actually removes the ref under the live peer.
- restore collision: after B deletion a peer creates topic at C; empty-old update-ref refuses, C unchanged/rc2. No clobber. B is not durably rescued by this behavior.
- Forced local+remote enumerator exit7 ->2/no clean; failed fetch ->2/no deletion; integration tag shadow ->unmerged local+remote topic retained0. Missing tickets/ ->explicit skip0; existing tickets/ without erg ->2/no clean. Native suite independently covers unavailable forge2.
- Five concern controls now honestly assert default deletion, symref false-finding1, single current-guard redundancy, worktree redundancy/refusal1, -d over-retention1 plus separate noprobe destruction. Multi-layer current mutant and unsafe update-ref mutant are explicitly distinguished from single-strip controls. Global header overclaim remains informational, not a fabricated destructive demonstration.

### Checks / evidence
Actual current-tip `bash tests/test_roar_close_and_clean.sh`: rc0, **82 PASS assertions**, including both moved-tip interleavings, late peer, mutants and all prior failure cases. Actual `make check`: rc0, **1557 passed / 5 skipped**, all full-gate targets. Actual adherence `make lint`:182 passed. Evidence/scripts/logs retained under `/tmp/regaze-1374-DxgC0I` (`inject.py`, `injections.json`, `extra.py`, `extra.json`, `shell-suite.log`, `make-check.log`). Initial crash injection killed the command-substitution shell, not root; corrected `death-window-root` explicitly SIGKILLs the root process and is the cited crash evidence.

### Non-blocking dispositions
- consider: stale leased/refused-never-destroyed and guard-header descriptions should reflect compensation and redundancy; no new enforced assertion attached.
- consider: append correction of historical ticket1084 log's1089 reference; current criterion correctly discharges remeasurement by1090. Append-only log not silently rewritten.
- 1089 is explicitly authorized bundled discovery bookkeeping, no implementation;1090 preserves the actual future measurement obligation. Criterion5 is **discharged by follow-up ticket**, not measured or ticked.

### Verdict roster
- consistency: request-changes
- red team: request-changes
- scope: comment (no blocking scope finding)
- regression (correctness + doc propagation): request-changes

dissent: scope finds contract-preserving wiring and explicit future measurement discharge; the other seats block local preservation. Synthesis: request-changes. Panel-history round5 is distinct from gate-attempt count. No repository edits/commits/pushes/branches/worktree deletion or other-worktree access occurred; all destructive experiments used our own /tmp repos. Branch was not rebased; current-base prerequisite remains caller responsibility.
