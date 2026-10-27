# Raid — fix-and-regate loop

Loaded from `skills/raid/SKILL.md` § Phase 6.

**Fix-and-regate (caller-owned; formerly gaze's fix-agent contract).** On
`FINDINGS` or a round-1 REROLL, the raid spawns the fix agent — the **coder
profile** (`agents/coder.md`, whose contract is `profiles/coder/PROFILE.md`;
the model is chosen per launch from the `route` skill) — in the PR's worktree,
feeding it the unresolved lists (review comments, gaze findings, simplify
findings, failing gate checks, per-exit-criterion gaps) as input, and waits for the artifact it
writes on completion. Fix agent gets ≤10 min. The agent works under:

- Strict rule: **only** the listed items. No scope creep. No "while I'm here" edits.
- TDD discipline still applies: add a failing test for any behavioural fix before coding, and show it failing for the targeted reason (an AssertionError on the behaviour, not an import, argument or fixture error) before the fix.
- Test-run budget: `make check-fast` plus the tests implicated by the unresolved-items list during the fix; one declared project gate before the final push — not per fix. A mapped doc-only fix uses `python3 "$IDH_ROOT/scripts/scoped-check.py"` and quotes selected and skipped targets; Python code and unmapped changes use the full `make check`.
- Push commits to the PR branch; do not open new PRs.

After a FINDINGS fix, run gaze on the new head with a narrower intent: verify
those fixes, because they were the findings; after a round-1 REROLL fix,
re-gate once with the same `session=`. Breakers on this loop:

- Fix agent timeout (10 min) → ESCALATE.
- Gate disagrees with a gaze result on a must-fix finding → ESCALATE (no silent resolution).
- Two REROLL rounds reached → ESCALATE.
- FINDINGS again on the fixes after the narrower gaze → ESCALATE, except the
  second-round rule below.

**Second fix round (author ruling, 2026-10-27).** One further round runs without
the author when every finding of the narrower gaze (a) concerns the previous
fixes, with no new scope, (b) is tagged `verifiable:` with its reproduction,
and (c) is fixed red-test-first, the red run shown failing for the targeted
reason. A third round, or any judgment finding, escalates.

