# Ticket 1414: do Codex and Pi need the conditional rules? (2026-11-01)

## Setup
- Arms, each 2 tasks x 2 repetitions x rule absent/supplied = 16 runs (`run.sh`, `prompts/`, `out/`).
- Codex: Codex CLI v0.166.0, served `gpt-6.1-sol` (provider openai, effort low, read-only, ephemeral). Rule supplied as a prompt prefix (not ticket 1413's global file).
- Pi: served `padme` / `qwen3.8-flash-next-iq3_s` (local, thinking medium); `--no-tools -ne -ns -nc -np`; rule via `--append-system-prompt <file>`.
- Task 1: Python CLI script plus test (rule `coding-python.md`). Task 2: ~120-word French academic paragraph (rules `prose/_all.md` + `lang/fr.md`). The task prompts never mention the rules.
- Scorer: blind (anonymous ids, shuffled, `blind-key.json` withheld), Claude Sonnet 5.5 subagent (family differs from both producers: OpenAI, Qwen), rubric `rubric.md`. Scorer report is reproduced below. Cost: Codex runs 16 x ~1-1.5k..7k tokens (under 60k total), Pi local, scorer ~66k tokens: a few cents to well under 1 USD.
- Mechanical check: `ruff check` passes on 7 of 8 task-1 outputs in both arms (1 finding each in pi-t1-none-r0 and pi-t1-rule-r1).

## Scores (unblinded)
Task 1 (max 7): codex none 4, 4; codex rule 7, 7; pi none 4, 4; pi rule 7, 5.
Task 2 (max 9): codex none 8, 8; codex rule 8, 9; pi none 8, 7; pi rule 9, 9.

Per-output: T1-00 pi-none-r0 4 · T1-01 pi-none-r1 4 · T1-02 pi-rule-r1 5 · T1-03 codex-rule-r1 7 · T1-04 codex-rule-r0 7 · T1-05 pi-rule-r0 7 · T1-06 codex-none-r0 4 · T1-07 codex-none-r1 4 · T2-00 codex-rule-r0 8 · T2-01 codex-none-r1 8 · T2-02 pi-none-r1 8 · T2-03 codex-rule-r1 9 · T2-04 codex-none-r0 8 · T2-05 pi-none-r0 7 · T2-06 pi-rule-r0 9 · T2-07 pi-rule-r1 9.

## Finding per rule class
- **Mechanically enforced (coding-python): needed on both.** Without the rule all 4 outputs print the report instead of logging and name the test file outside `tests/test_<module>.py`; 3 of 4 lack type hints on signatures, one skips argparse. Supplying the rule fixes the print/logging and `tests/` items in 3 of 4 outputs. ruff does not flag these (it passed the rule-less outputs), so the stated gate "ruff" does not catch them; only hygiene tests or review would. The expected cost is not just fix rounds. Evidence: scores above, `out/*-t1-*`.
- **Judgment-only (prose/_all + lang/fr): marginal, at the ceiling.** Without the rule both models already use guillemets and decimal commas and avoid the banned vocabulary. Rule-less misses: weak copula "constitue" (3 of 4), tricolon (2 of 4), "cruciale" (1 of 4). With the rule: 1 weak copula in 4. Mean 7.75 vs 8.75 of 9; n=2 per cell, one-point differences are within noise. Not shown to be needed for `lang/fr` items (F1, F2) which no skill names; not shown to be useless either.
- Caveats: one task per class, 2 reps, a rubric derived from the rule (favours the rule arm), one scorer, low-effort Codex. Pi arm used a system-prompt channel, Codex a prompt prefix.

## Follow-up (criterion 3)
Needed for coding-python on Codex and Pi. The prose class is not shown to be needed. Reach for coding-python through a skill pointer or injection on those runtimes; whether ticket 1413's global file is the right channel is the author's call. No follow-up ticket filed from here (severity floor: author decides).

## Scorer report (verbatim table)
Task 1 P1..P7 totals: T1-00 4, T1-01 4, T1-02 5, T1-03 7, T1-04 7, T1-05 7, T1-06 4, T1-07 4. Violations: P4 print (T1-00,01,02,06,07), P6 test not in tests/ (T1-00,01,02,06,07), P7 no hints (T1-00,06,07), P2 no argparse (T1-01).
Task 2 totals: T2-00 8 (F7 "constitue"), T2-01 8 (F6 tricolon), T2-02 8 (F7), T2-03 9, T2-04 8 (F6), T2-05 7 (F5 "cruciale", F7), T2-06 9, T2-07 9.
