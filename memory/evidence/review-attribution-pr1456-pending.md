# PR 1456 review attribution capture status

Captured 2026-10-19 from the durable PR trail at https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1456 and local gate artifacts `/tmp/gate1456-comment.txt`, `/tmp/gate1456-supplement.txt`, and `/tmp/gate1456-round2.txt`. The PR merged as `f3350ced4f8d190419a8d52109205a9080cc1232`; reviewed source head `f2c1de47916716ae77412e10ada6e351a03e1622`.

## Known review attempts and outcomes

- Luna round 1: correctness, consistency, scope, red-team, and doc-propagation perspectives ran at `7197ab66133d214ae936e860479c3896db9ff2d1`, OpenAI family, reported alias `gpt-6-luna`, high effort. The synthesis reports correctness findings at `scripts/tmp_report.py:453` (candidate-specific creation freshness) and `scripts/tmp_report.py:705` (formatting unavailable disk readings); red-team shared the latter finding. Consistency found the unchecked reviewed-PR item at `tickets/closed/1118-report-temporary-candidates-and-session.erg:50`. Doc propagation found the host-wide scan/scoped attribution wording at `skills/roar/SKILL.md:88`. These were fixed in `005a7557912e349819bfa58c30f2bf3959e32f75`; `ac99071c24544dbb4553bc139663435f0ab1795a` addressed the remaining documentation wording. The scope perspective's extra commit-ID request was explicitly not retained as a finding.
- Luna round 2: correctness, consistency, scope, red-team, and doc-propagation perspectives ran. The PR synthesis reports approvals at `005a755` for correctness, consistency, scope, and red-team, and at `ac99071` for doc propagation. It reports no findings. Supplemental live-head checks ran at `ac99071`: doc propagation and regression; both report no findings. The same PR synthesis reports the alias `gpt-6-luna`, high effort, OpenAI family.
- Sol formal gate round 1 ran at `ac99071` and returned REROLL. It reported two formal blockers: ancestry was lost through an intermediate ancestor with no matching candidate citation, and the Codex/Pi startup path did not invoke the advisory disk probe. A supplement confirmed the startup wiring gap in the same round. The gate summary reports two `consider` items but does not provide their finding anchors or adoption dispositions.
- Sol formal gate round 2 ran at `f2c1de47` and returned APPROVED, with all five exit criteria addressed. The synthesis reports two `consider` items but does not provide their finding anchors or adoption dispositions. The fixes are described in the round-2 comment and landed in `f2c1de47`.

Durable synthesis and validation references:

- Round 1: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1456#issuecomment-6265649889
- Round 1 startup supplement: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1456#issuecomment-6265729535
- Producer validation: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1456#issuecomment-6265830110
- Round 2: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1456#issuecomment-6265835900

## Why the fixed-line attribution record remains pending

The current Codex writer metadata and native reviewer tool metadata expose no provider-qualified full model ID, model version, or writer effort. The durable Luna syntheses give only `gpt-6-luna` and high effort; the Sol gate syntheses give only `openai/gpt-6.1-sol` and medium effort. These aliases are not verbatim provider-qualified full model IDs. No provider model version is present. The native Sol reviewer launch tool returned only `{"task_name":"/root/sol_gate_1456"}`; that tool return contains no model, version, or effort fields. The local gate text preserves the reported Sol alias and medium effort but cannot supply the exact model pin.

The durable PR trail contains review syntheses, not the individual raw Luna seat reports. Both Sol gate summaries report two `consider` items without their anchors or adoption dispositions. Writer effort is required by the attribution contract and is unavailable. These missing observations prevent validation of a complete attribution record. No reviewer identity, model pin, finding anchor, or adoption disposition has been inferred to fill the gaps. This file preserves the known attempt roster and findings while the PR 1456 attribution capture remains pending.
