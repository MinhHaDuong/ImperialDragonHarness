# PR 1374 review round 3

Forge review: PRR_kwDORsAV3c8AAAABR11Wyg
Reviewed commit: 3dbdcbbf338750b770c864c9224c2d2baa51fbfc
Submitted: 2026-10-12T14:38:11Z

## /review-pr round 3 — PR #1374 (independent GAZE panel)

Reviewed HEAD: `3dbdcbbf338750b770c864c9224c2d2baa51fbfc`; base `origin/main` (`fc0a75d8355817400b4370824f5314fa212d7c5a`). Parent review-pr-anchor checks passed before and after the battery. Width: 7 files / 756 lines, high-risk (`scripts/**`, `skills/**`). Previous round selected consistency + red team, unresolved/unrun scope + one regression check for correctness/doc propagation. All four perspective processes returned substantive reports through the available Pi subagent tool; none was synthesized as a simulated seat.

PANEL-INTEGRITY: DEGRADED — adherence=Pi worker/openrouter/~anthropic/claude-sonnet-latest (PI_PROVIDER/PI_MODEL/PI_REASONING_LEVEL=high reported); native-review=NOT-RUN (native /review unavailable); consistency,red-team,scope,regression=distinct Pi reviewer subagents pinned by /home/haduong/.pi/agent/agents/reviewer.md to openrouter/~openai/gpt-sol-latest (cross-family vs Anthropic implementer; resolved version and effort runtime-masked; substantive returned reports at ruled SHA); simplify=separate Pi worker/openrouter/~anthropic/claude-sonnet-latest (high reported). Required native review unavailable; several individual anchor commands unavailable under reviewer profile, compensated by parent live anchor plus seat HEAD reads; manifest/artifact polling NOT-RUN under caller no-file-edit rail, reports collected by blocking tool completion instead. Scoped correctness/doc propagation represented by regression, not separately rerun. Optional external panel not selected. Route grid covers Sonnet medium, not observed high: worker effort route mismatch is explicitly unverified, not grid-compliant.

dissent: red team and scope request changes; consistency and regression comment. Portable simplify found no must-fix, but its general “ticket intent preserved” assertion does not resolve the scope seat’s concrete preflight-sequencing objection.

### Blocking findings
1. **Lease not bound to probed OID** — `skills/roar/close-and-clean.sh:214-215` (red team). `3dbdcbbf` reads a fresh tracking OID for the lease AFTER approving the ref. A colleague pushes unmerged B and another session fetches between those operations: the lease adopts B and allows deletion. Non-mutating exported-Git-function repro executing the real script: probe approves A, lease reads B, mocked remote accepts B, output `remote deleted: topic` and `RESULT: clean`, rc 0. Freeze candidate OID once, probe that OID and lease exactly it. Existing test injects push after lease expansion, so it misses this window.
2. **Ambiguous integration base** — `skills/roar/close-and-clean.sh:173-179,187` (red team). The new helper uses shorthand `origin/$DEFAULT` / `$DEFAULT` for verification and ancestry; an `origin/main` or `main` tag can shadow the intended integration branch and authorize deletion of unmerged work. Static Git-resolution sequence, not dynamically reproduced here. Fully qualify and freeze the actual base ref/OID.
3. **Local probe/delete race** — `skills/roar/close-and-clean.sh:196-199` (red team). Probe approves A; concurrent update of unchecked-out branch to unmerged B; name-based `branch -D` deletes B with no expected-old-OID check. Static evidence; inherited recipe also had this race (pre-existing but moved into the new unattended helper). Reported for explicit safety disposition, not hidden as a newly invented regression.
4. **Enumeration errors report clean** — `skills/roar/close-and-clean.sh:203,219,240` (red team). Process substitutions drop both `for-each-ref` exit statuses. Non-mutating mock repro: BOTH enumerators exit 7; real script returns 0 / `RESULT: clean`. Validate enumeration before consumption and return could-not-look/2 on failure.
5. **Stale worktree-exit preflight** — `skills/roar/SKILL.md:248-255` (scope). Changed step 9a trusts the step-7 result before step-8 full tests/integration review and the wrap-up bundle. Worktree state may change before removal; ancestry is not cleanliness. Restore fresh preflight immediately before exit, preserving criterion 4’s judgment sequence.

### Minor findings
- verifiable: `tests/test_roar_close_and_clean.sh:41,242,247` (shared consistency/regression): wrapper requires `touch`, hermetic whitelist omits it. Source assertion reproduced: `touch not in whitelist` and `touch "$T/c13/pushed"` present. The intended once-only marker cannot be created. Use shell redirection or include touch.
- verifiable: `skills/roar/SKILL.md:59-61,220-221` (consistency): unchanged no-forge policy says missing prerequisites are explicit skips, never failure; new step-7 contract and helper `close-and-clean.sh:91-93` report missing ticket store as could-not-look/2. Reconcile the contradictory instruction contract without weakening fail-closed forge checks.
- consider: `tickets/1089-pi-subagent-link-no-ops-on-an-npm-global.erg:10-30` and ticket 1084:9: npm-global linking discovery is outside 1084’s criteria; justify ticket-only bookkeeping or separate it. It is NOT the outstanding remeasurement follow-up.
- consider: portable simplify suggestions: remove redundant ticket-directory test (:91), dead first mutant sed expression (test :258), optionally deduplicate race fixture setup, and clarify step-9a prose. No must-fix simplification findings; no fixes applied under caller rails.

### Gate evidence
`make lint`: 182 passed. Full `make check`: 1558 passed / 4 skipped; all agnostic and drift gates ran. Hermetic guard: 26 shell suites / 29 child spawns, clean; new shell suite clears BASH_ENV. The shell suite is invoked by `tests/test_bash_suites.py` (not direct Makefile text), so simplify’s missing direct Makefile match does not establish a test-wiring gap. Tests passing do not refute the untested races or mocked failure path.

All FIVE ticket 1084 criteria remain `[ ]`. Criterion 5 explicitly requires post-merge roars and a journal result and cannot be verified now. None is certified complete from an unticked box; implementation/test evidence will be mapped individually by verify-gate.

### Verdict roster
- consistency: comment
- red team: request-changes
- scope: request-changes
- regression (correctness + doc propagation): comment

Synthesis verdict: request-changes. Review round 3 is a panel-history count, NOT a third verify-gate attempt: this GAZE invocation has not yet gated.
