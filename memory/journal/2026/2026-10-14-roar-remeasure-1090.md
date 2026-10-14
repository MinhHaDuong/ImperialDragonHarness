# Roar turns remeasured after close-and-clean (1090) — 2026-10-14

Project: ImperialDragonHarness. Sources: Claude Code, Codex and Pi session
transcripts on padme and doudou; script and raw rows in
[2026-10-14-roar-remeasure-1090/](2026-10-14-roar-remeasure-1090/).

## Method

- Population: every roar invoked after 1084 merged (2026-10-12 13:58Z), all
  repositories, all three runtimes, both hosts. 22 distinct roars after
  removing one session logged in two project folders.
- Window: from the prompt (or `Skill` call) that invokes roar to the next
  typed user prompt, or session end. Only roar turns are counted.
- Turn: one model API response (Claude Code: distinct `message.id`, main
  thread only; Codex: `token_count` event; Pi: assistant message).
- Cache-read input equivalents: `0.1 × cache_read + 1.25 × cache_write +
  uncached input`, summed over the window. The 1084 baseline script was not
  committed; this weighting is reconstructed and reproduces the baseline
  arithmetic (16 turns from 215k ≈ 3.8M cache reads ≈ 380k, plus writes ≈ 420k).
- Bundled prompts ("Merge and $roar", "After all three, $roar and $lair",
  "Cleanup, /roar and /lair") include non-roar work in the window and are
  reported separately.

## Result

| | Roars | Median turns | Median start context | Median equivalents | Start > 256k |
|---|---|---|---|---|---|
| Baseline (1084: padme, Claude Code, 2026-10-11) | 75 | 16 | 215k | ~420k | 29 |
| After, roar-only prompts, all runtimes | 15 | 14 | 147k | 224k | 1 |
| After, roar-only prompts, Claude Code | 13 | 14 | 157k | 274k | 1 |
| After, bundled prompts (upper bound) | 7 | 38 | 109k | 541k | 1 |

## Reading

- Turns per roar fell about 12% (16 → 14), not the ~40% that 1084 derived
  from assuming 8–10 of 16 turns were mechanical. The derived estimate is
  replaced by this figure.
- Equivalents fell about 47% (420k → 224k), but most of that comes from
  roars now starting in smaller contexts (215k → 147k; 29/75 → 1/15 above
  256k), which close-and-clean does not control. Per turn: 420k/16 ≈ 26k
  before, 224k/14 ≈ 16k after (derived).
- Caveats: the baseline was one host and one runtime, and its exact window
  rule is unknown; the after-sample is small (15). Two 2-turn windows
  (doudou 2026-10-13 20:09, padme 2026-10-14 17:38) look like re-invocations
  of a roar already run. Pi kept one interactive roar session (bundled).
