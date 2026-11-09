# Evidence seat, round 1 (census + assessment), summary of its report
Notes/scripts: scratchpad/1096/evidence/ (idh-gh.txt, jetp-attr-*.md, padme-census.json, notes-final.md). Harness repo on GitHub: MinhHaDuong/ImperialDragonHarness. Host padme unless noted. M = measured, D = derived.

## Raids 1080 (PR 1389) and 1089 (PR 1390)
Sources: gh pr view; memory/journal/2026/2026-10-14-review-attribution-pr1389.md, -pr1390.md, 2026-10-14-pr1390-review-evidence.md; memory/evidence/review-attribution-pr1389/.
- First review to merge (D): 1389 79.0 min (09:24:29→10:43:27Z); 1390 59.1 min (09:47:37→10:46:46Z).
- 1389: two full 5-seat panels on different heads (00c5a333, 825b1eda) + gaze-era portable simplify, native-root, simplify-current, semantic-delta on 9bd20fa3, final gate. Attribution lines 28 (18 ran, 10 failed), incl. 5 semantic-acceptance fixture runs. No same-SHA duplicate panel; rebases changed SHA only (gate: "11 identical blobs plus one deletion").
- 1390: one hunt panel (3 completed seats) on 40708b7; then a deliberate same-head round-2 scoped panel (2 Luna seats) on unchanged 40708b7, posting nothing new; then adherence, native review, simplify, gate. 17 lines (9 ran, 7 failed, 1 skipped); the 7 failures are bootstrap/startup: 2 Claude CLI argument errors, 1 native spawn thread limit, 2 native review read-only FS, 1 gaze controller timeout (exit 124), 1 interrupted gate.
- No per-phase timings recorded; the 59/79 min cannot be split by phase.

## JETP-observer PRs 151-160 (journals memory/journal/2026/2026-10-14-review-attribution-pr{152..160}.md in JETP-observer)
151, 158, 159 ticket-only, no review; 157 study PR, no review comment.
| PR | batteries | seats | first review→merge (D) | same-head dup |
| 152 | 1 hunt review-pr (1 width-gated seat), reused by gaze (+adherence, B, simplify, gate) | 6 | 10.6 min | no |
| 153 | 1 gaze, REROLL, gate-only round 2 | 11 | 70.9 min | no |
| 154 | 1 (tiny tier) | 6 (4 ran) | 1.8 min | no |
| 155 | 1 inline; sub-agent battery not spawned; DEGRADED | 3 | 5.2 min | no |
| 156 | 2 rounds; first gaze attempt hit 15-file breaker; author waiver for make check | 20 | 90.9 min | no (head changed) |
| 160 | 0 | 2 inline | n/a | no |
Long PRs (153, 156) were long because of REROLL/fix rounds, not duplicate batteries.

## Trace census (padme ~/.claude/projects, 4,489 JSONL, all scanned)
Skill calls/sessions: gaze 156/96; review-pr 336/152; review-pr-prose 3/4; verify-gate 62/30; hunt 174/174; raid 21/20. Pi padme: 60 files, 1 gaze mention. doudou: 7,323 Claude JSONL + 40 Pi files counted, then host unreachable; no doudou skill census.
Same-head repeat via REVIEW-ANCHOR lines: 182 distinct (project, PR, head); 3 heads anchored in ≥2 sessions (1.6%, D); 52 of 104 anchored PRs saw ≥2 heads. Lower bound (only sessions using the anchor script).
GitHub ground truth (ImperialDragonHarness PRs 1330-1392, 63 merged): #1334 true same-head double panel on f961c062 (gaze Agent C then standalone review-pr, 2 min apart) — the probe's positive control fired. #1368 second review on same head was a deliberate cross-family red-team seat. First review→merge: #1372 82.7, #1373 83.4, #1378 49.7, #1374 1,333 min (8 panels, 8 heads).

## Positive control: extra seats that caught something
- #1377 (journal 2026-10-13-review-attribution-pr1377.md): on head c21e841b the Codex correctness seat approved; native Codex review and Claude red-team both requested changes on the same head (scripts/check-cross-pr-ticket-collision.sh:116-118); fix 17a0c63e. Same head, different seats/family.
- #1372, #1373, #1374: a detached OpenAI-family battery forced one bounce each (false all-clear, echo masking a failure, BASH_ENV inheritance, unreadable dirs omitted).
- #1334: all panel seats approved; gate/make check found a real blocker (skills channel 7016 > 7000 chars).
- #1354: red-team alone raised two blockers, upheld by gate. JETP #153: catch in the first battery.
- No episode found where a repeat by the SAME seats on an UNCHANGED head caught something (tested scope: 63 IDH PRs, JETP 152-160, anchor sessions).

## Assessment
- Shared core helps: 1390 unchanged-head repeat; #1334 duplicate; removes hand blob checks in 1389/1390 gates. Changes nothing: JETP 152/154 (gaze already reused). Could hurt: #1377 — reuse is safe there only if the plan still buys red-team or cross-family seats for that risk row; a width-gated single seat would have missed it. #1334: reuse must also key on gate/adherence/check results for the head, or a reused approve hides a red make check.
- A: removes prose duplication; prose mode is rare (3 calls vs 336). Does not touch closing time drivers.
- C: captures nearly all measured repeat savings, cheapest; hurts if native /review is dropped without replacement (#1377, #1372-1374 caught by extra OpenAI-family seats).
- B: no episode where it helps.
- The 10-25 min/MR saving is unsupported: JETP 152 and 154 total 10.6 and 1.8 min; only 2 of 63 sampled IDH PRs (#1334, 1390) and 3 of 182 anchored heads are same-head repeats. Recorded delays on 1389/1390 are failures (startup, exit-124, interrupted gate) that no option addresses.
