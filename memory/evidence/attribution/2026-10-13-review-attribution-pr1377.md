kind: review-attribution
pr: 1377 · merged 2026-10-13 · project: ImperialDragonHarness
writer: runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · effort=runtime-masked
reviewer: seat=correctness-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: c21e841bdb33c4f9cec793b6d68dedca1f8ae6a5; gpt-6.1-sol low; approved, fork defect missed
reviewer: seat=native-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: c21e841bdb33c4f9cec793b6d68dedca1f8ae6a5; native review; observed OpenAI and gpt-6.1-sol low; request-changes
  finding: verifiable · scripts/check-cross-pr-ticket-collision.sh:118 · adopted: yes
reviewer: seat=red-team-1377 · runtime=claude-code · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: c21e841bdb33c4f9cec793b6d68dedca1f8ae6a5; context dc8e4f24-fc60-4a21-b474-4a5b43d31104; observed claude-sonnet-5-5 medium; request-changes
  finding: verifiable · scripts/check-cross-pr-ticket-collision.sh:116 · adopted: yes
  finding: verifiable · tests/test_check_cross_pr_ticket_collision.sh:345 · adopted: yes
  finding: consider · scripts/check-cross-pr-ticket-collision.sh:115 · adopted: yes
  finding: consider · scripts/check-cross-pr-ticket-collision.sh:108 · adopted: yes
  finding: verifiable · tickets/closed/1092-check-cross-pr-ticket-collision-reports.erg:1 · adopted: yes
reviewer: seat=correctness-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 17a0c63ebc82a72ece4b4514a98bf5b2dcd18c92; same reused context, approved
reviewer: seat=consistency-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 17a0c63ebc82a72ece4b4514a98bf5b2dcd18c92; gpt-6-luna medium; documented exit precedence adopted
  finding: verifiable · scripts/check-cross-pr-ticket-collision.sh:115 · adopted: yes
reviewer: seat=doc-propagation-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 17a0c63ebc82a72ece4b4514a98bf5b2dcd18c92; gpt-6-luna medium; opening test inventory updated
  finding: consider · tests/test_check_cross_pr_ticket_collision.sh:18 · adopted: yes
reviewer: seat=simplify-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 17a0c63ebc82a72ece4b4514a98bf5b2dcd18c92; gpt-6-luna medium; MINOR unused pr-view result removed
  finding: consider · scripts/check-cross-pr-ticket-collision.sh:107 · adopted: yes
reviewer: seat=correctness-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 5a0600a24369fb3780f72505a99d367fd29c1f73; same reused context, approved
reviewer: seat=simplify-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 5a0600a24369fb3780f72505a99d367fd29c1f73; same reused context, CLEAN
reviewer: seat=red-team-1377 · runtime=claude-code · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 5a0600a24369fb3780f72505a99d367fd29c1f73; same CLI context, approve; live repository-field and real PR checks
reviewer: seat=gate-1377 · runtime=codex · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md:51 · status: ran
Context: 5a0600a24369fb3780f72505a99d367fd29c1f73; gpt-6.1-sol medium; ebbf9fae-f004-44f8-9b87-0c7266fb1253; round 1 APPROVED

Identity evidence: launch pins and CLI provider/model components are observed; a verbatim provider-qualified backend ID/version is unavailable. No ID is reconstructed. Reused contexts retain the same seat across attempts. Public audience judged before capture. Published PR reviews and the accompanying checkpoint establish outcomes.
