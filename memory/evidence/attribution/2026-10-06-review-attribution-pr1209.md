kind: review-attribution
pr: 1209 · merged 2026-10-06 · project: .agents
writer: runtime=codex · model=openai/gpt-6-luna · effort=medium
reviewer: seat=correctness · runtime=codex · model=openai/gpt-6-luna · status: ran
  finding: verifiable · tests/test_projection_validator.py:208 · adopted: yes
reviewer: seat=consistency · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=scope · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=red-team · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=doc-propagation · runtime=codex · model=openai/gpt-6-luna · status: ran
  finding: consider · docs/adapter-operations.md:33 · adopted: yes
reviewer: seat=portable-simplification · runtime=codex · model=openai/gpt-6-luna · status: ran
  finding: consider · scripts/validate-projections.py:265 · adopted: yes
reviewer: seat=criterion-gate · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=correctness · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=correctness · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=correctness · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=consistency · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=red-team · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=doc-propagation · runtime=codex · model=openai/gpt-6-luna · status: ran
reviewer: seat=portable-simplification · runtime=codex · model=openai/gpt-6-luna · status: ran

Actual root producer metadata and direct spawn edges establish writer and all seven review contexts as openai/gpt-6-luna/medium. Initial Correctness requested changes because three assertions expected removed diagnostic strings; original report anchors tests/test_projection_validator.py:208-213,225-232,235-241 at aeb1c303ecca258eaac01b83c01c60da1d7ec33b. This is one compound finding, recorded once at208. Source Git confirms the original anchored definition/assertions; producer corrected assertions and same reviewer approved d21281a7b15dcefc12255aef639731b86637ce79 and subsequent fca0da0a005264e9cd3155c9611fd1b545c86955 and9e479d9b9ad4a4647114464d578aa9488b30c1dd. Initial Consistency raised a medium-confidence wording consider about the dangling-link comment; its original report names scripts/shell-init.sh without a line, so it stays prose. Producer changed that wording to broken projection and the same reviewer approved d21281a7. Doc-propagation independently raised the runbook claim at docs/adapter-operations.md:33 on d21281a7; correction adopted and reviewer approved fca0da0a. Portable P3 on scripts/validate-projections.py:265 at fca0da0a recommended any() instead of unused accumulation; it was adopted and actual portable confirmed CLEAN at9e479d9b.

Actual public synthesis covers five approving perspectives at fca0da0a. The later9e479d9b change has actual current-head Correctness and Red-team confirmations, portable CLEAN and final criterion-gate approval. These are reused-context phases, not extra independent reviewers. Scope found no issues. No native process is recorded or invented. Source runtime safe proof: docs/2026-10-06-attribution-capture-proof.json, keys `pr1209-reviewers-safe.json` and `pr1209-initial-anchors-safe.json`; retained sanitized phase artifacts in that committed file ; public https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1209 . Same model/provider; context separation only. No model revision exposed.

Stable actual-context seats preserve each completed follow-up as a separate raw attempt: Correctness has initial requested-changes plus three approvals; Consistency initial comment plus corrected approval; Doc initial comment plus corrected approval; Red-team initial approval plus final regression approval; portable initial suggestion plus adopted CLEAN. These are the same contexts, not decorrelation fan-out.

Stable seat/runtime/model/version values identify each actual reused reviewer context; rounds, source revisions and evidence remain in opaque prose. Every completed raw attempt remains recorded. Only genuinely distinct native processes or gate contexts use distinct seats.

Actual completed public panel: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1209#pullrequestreview-5419637189 .
