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

## Same-method control

The table above compares against the 1084 figure, whose method is unknown.
Rerunning this window rule on every Claude Code roar since 2026-09-01, on
both hosts (`roardeep.py`, `analyze.py`, `analysis-output.txt`), shows that
comparison was misleading:

| Solo Claude Code roars | Roars | Median turns | Median start context | Median equivalents |
|---|---|---|---|---|
| 2026-10-01 to 1084 merge | 53 | 10 | 169k | 203k |
| After 1084 merge | 14 | 12.5 | 152k | 232k |

Against roars from the same weeks, 1084 saved no turns; the median rose.
The apparent 16 → 14 came from a baseline drawn mostly from September.

## Why the turns were not saved

- close-and-clean runs in three phases (`before-exit`, `preflight`,
  `after-exit`) around `ExitWorktree`, which only the model can call, and
  `ExitWorktree` is deferred, so each roar also spends a `ToolSearch` turn.
  With the `sync-local-main.sh` call added by 1097 on 2026-10-14, the
  mechanical floor is about six turns: the script did not remove turns, it
  renamed them.
- Sessions re-verify around the script: git-read calls per solo roar went
  from 4.0 to 5.3 (fetch, `merge-base --is-ancestor`, `rev-parse` before and
  after `ExitWorktree`), and some roars ran a phase twice.
- The 8–10-mechanical-turns premise was wrong. The long roars are long on
  judgment work: review attribution capture and backfill, journal writing,
  PR evidence reconstruction (for example doudou 2026-10-14 12:58, 35 turns,
  most on attribution records).
- Tool calls per turn rose (1.23 → 1.36), so batching improved; it did not
  offset the added phases.

## Why roars start in smaller sessions

Weekly medians, all Claude Code roars:

| Week | Roars | Start context | Pre-roar API calls | Start > 256k |
|---|---|---|---|---|
| Sep 1–7 | 40 | 316k | 169 | 70% |
| Sep 8–14 | 32 | 293k | 169 | 72% |
| Sep 15–21 | 23 | 224k | 147 | 48% |
| Sep 22–30 | 30 | 212k | 106 | 33% |
| Oct 1–7 | 13 | 138k | 69 | 23% |
| Oct 8–14 | 91 | 147k | 64 | 23% |

The decline is gradual from mid-September and flat since early October,
so it predates 1084 and is not its effect. Sessions do less work before
roar (pre-roar API calls 169 → 64) and roars run far more often (13 → 91
per week). The cause is not isolated. Changes in the window include the
gaze PR-size refusal (2026-09-23), the session-start resident-text warning
(0971, 2026-09-24), the bundled roar wrap-up (2026-10-01) and the
resident-rules trim with the 256K guard (2026-10-06); none was measured
separately.

## Caveats

The 1084 baseline's exact window rule is unknown. The after-sample is
small. Two 2-turn windows (doudou 2026-10-13 20:09, padme 2026-10-14
17:38) look like re-invocations of a roar already run. Pi kept one
interactive roar session (bundled). Transcripts older than September are
no longer on disk.
