kind: review-attribution
pr: 1447 · merged 2026-10-16 · project: ImperialDragonHarness
writer: runtime=Claude Code · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:9 · effort=unavailable
reviewer: seat=pr1447-hunt-review-loops · runtime=Claude Code · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:10 · status: ran
reviewer: seat=pr1447-gaze-adherence · runtime=Claude Code · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:12 · status: ran
reviewer: seat=pr1447-gaze-review-panels · runtime=Claude Code · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:13 · status: ran
reviewer: seat=pr1447-gaze-codex · runtime=codex · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:14 · status: ran
  finding: verifiable · scripts/zotero.py:2535 · adopted: yes
  finding: verifiable · scripts/zotero.py:2105 · adopted: yes
reviewer: seat=pr1447-gaze-simplify · runtime=Claude Code · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:15 · status: ran
reviewer: seat=pr1447-gaze-gate · runtime=Claude Code · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:16 · status: ran
reviewer: seat=pr1447-gaze-gate · runtime=Claude Code · model-state=runtime-masked · model-evidence=memory/evidence/2026-10-16-review-identities-pr1447-1448.md:16 · status: ran

Context: anchors refer to fba2553893db3a8681318d8dd3ee4a4377a8ffa0 (gate round 1, REROLL); final reviewed and merged head da87721facb280703a338ef0451471d1b8971603 (round 2, APPROVED).
Context: the round-1 blocker (a new test ran the real poppler tools, absent on CI) was found by the writer's regression seat and the codex seat; it has no line anchor in the trail, so it is not recorded as a finding line. Fixed in d250c462.
Context: the codex finding at scripts/zotero.py:2535 (--dir promised "every file") was downgraded by the gate from blocker to a doc mismatch and fixed in docs and help text.
Context: the author waived the 15-file breaker for this PR verbatim; all seats except codex are same-family.
