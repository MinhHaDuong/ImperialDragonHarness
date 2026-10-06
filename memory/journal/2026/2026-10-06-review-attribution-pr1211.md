kind: review-attribution
pr: 1211 · merged 2026-10-05 · project: .agents
writer: runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:3 · effort=standard

reviewer: seat=correctness-r1 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · scripts/validate-projections.py:129 · adopted: yes
  finding: verifiable · adapters/projections.json:9 · adopted: yes
  finding: consider · tests/test_claude_code_adapter.py:73 · adopted: yes
reviewer: seat=consistency-r1 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/projections.json:9 · adopted: yes
  finding: verifiable · adapters/claude-code/README.md:5 · adopted: yes
  finding: verifiable · adapters/README.md:165 · adopted: yes
  finding: verifiable · adapters/codex/hooks.json:2 · adopted: yes
  finding: verifiable · README.md:85 · adopted: yes
  finding: verifiable · docs/idh-install-strategy.md:49 · adopted: yes
  finding: consider · adapters/claude-code/README.md:18 · adopted: yes
  finding: consider · scripts/adapter-claude-code-activate.sh:7 · adopted: yes
reviewer: seat=scope-r1 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: consider · tests/test_guard_adapter_wiring.py:112 · adopted: yes
reviewer: seat=red-team-r1 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · scripts/validate-projections.py:129 · adopted: yes
  finding: verifiable · adapters/projections.json:5 · adopted: yes
  finding: verifiable · scripts/probe-plugin-hook-loading.sh:50 · adopted: yes
reviewer: seat=doc-propagation-r1 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/projections.json:12 · adopted: yes
  finding: verifiable · adapters/codex/hooks.json:2 · adopted: yes

reviewer: seat=correctness-r2 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/claude-code/README.md:5 · adopted: yes
  finding: consider · scripts/validate-projections.py:173 · adopted: yes
  finding: consider · adapters/lifecycle.py:119 · adopted: yes
reviewer: seat=consistency-r2 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/claude-code/README.md:5 · adopted: yes
  finding: consider · ROADMAP.md:16 · adopted: yes
  finding: consider · STATE.md:25 · adopted: yes
reviewer: seat=scope-r2 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/claude-code/README.md:5 · adopted: yes
  finding: consider · adapters/lifecycle.py:119 · adopted: yes
reviewer: seat=red-team-r2 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/lifecycle.py:119 · adopted: yes
  finding: verifiable · adapters/lifecycle.py:141 · adopted: yes
  finding: verifiable · scripts/validate-projections.py:83 · adopted: yes
  finding: verifiable · adapters/claude-code/hooks/hooks.json:43 · adopted: no
reviewer: seat=doc-propagation-r2 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/README.md:194 · adopted: yes
  finding: verifiable · adapters/pilot-support.json:398 · adopted: yes
  finding: consider · adapters/claude-code/README.md:9 · adopted: yes
  finding: consider · docs/adapter-operations.md:82 · adopted: yes

reviewer: seat=correctness-r3 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: consider · adapters/lifecycle.py:103 · adopted: yes
  finding: consider · scripts/validate-projections.py:180 · adopted: yes
reviewer: seat=consistency-r3 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: consider · adapters/projections.json:12 · adopted: no
reviewer: seat=scope-r3 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: consider · adapters/lifecycle.py:105 · adopted: no
reviewer: seat=red-team-r3 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: verifiable · adapters/lifecycle.py:103 · adopted: yes
  finding: verifiable · adapters/claude-code/README.md:14 · adopted: yes
  finding: verifiable · scripts/validate-projections.py:90 · adopted: no
  finding: consider · adapters/projections.json:15 · adopted: no
reviewer: seat=doc-propagation-r3 · runtime=vibe · model-state=runtime-masked · model-evidence=memory/pending-capture-pr1211.md.txt:69 · status: ran
  finding: consider · adapters/projections.json:24 · adopted: yes

context: three five-seat rounds at anchors 67d4c809 / e0591d11 / e3a7ca1a; reset exception each round (fix diffs touched files outside the prior round's set). Evidence: the three synthesis reviews posted on PR #1211. Per-seat model pinning unavailable in the runtime (each seat's report front-matter records it); writer model id masked in session logs, not reconstructed from an alias. A review seat's HOME-clobber incident during a reproduction is disclosed in the round-2 review; the live file was restored sha-verified.

Capture resolution: runtime-masked evidence is the preserved original draft,
whose writer observation is at line 3 and per-seat provider-id concealment for these attempts at lines 69–72.
The three public synthesis reviews corroborate the 15 attempted seats:
https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1211#pullrequestreview-5419766568
https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1211#pullrequestreview-5419861597
https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1211#pullrequestreview-5419966564
The draft's blocker severity is normalized to verifiable for the approved
finding grammar; all original anchors and adoption decisions are retained.
Only these 15 actual documented attempts are captured. Historical model ids
remain unknowable; whole-game model estimates exclude this record.

Reviewer concealment corroboration: the original 1038 incident report at
tickets/closed/1038-attribution-capture-cannot-state-the-wri.erg:26 establishes
that both reviewer seats and writer were unnameable at model level for PR1211.
The pending resolution at memory/pending-capture-pr1211.md.txt:69 states that
spawned-seat provider ids were not exposed for these attempts; its lines 70–72
connect this to the three five-seat syntheses and unrecoverable historical ids.
This assertion covers all 15 documented reviewer attempts; unavailable pinning
alone is not used as evidence of concealed identities.
