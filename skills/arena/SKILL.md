---
name: arena
description: "Replay the model tournament bench: declare arms, run, judge, feed the route grid."
disable-model-invocation: false
user-invocable: true
---

# Arena — rejouer le bench de modèles

`[Declare → Pre-register → Run → Judge → Readout]`

The arena is a reusable instrument, not a one-off. A new candidate (Qwen 4,
any hosted tier, any local quant) enters the SAME doors and its results land
in skills/route's grid. Everything lives in `~/arena`; the protocol and
history live in the concept note (§8) and tracker ticket 1024.

## Declare a candidate

- The candidate is the atomic identity (model @effort) — never the weights
  alone. A new effort level on a known model is a NEW candidate.
- `runner.py`: `ARMS` entry (provider, model, port for locals, EXPLICIT
  effort — resolve `@default` to the real level first, see skills/route) +
  `PRICE_TABLE` entry (in/out per M). For locals: `start-arm.sh` /
  `stop-arm.sh` entries.
- Verify the effective thinking level from session evidence
  (`thinking_level_change`), never trust the launch label.
- Hosted arms: $5.00 spend cap per arm per tournament, enforced by the
  runner's budget gate; locals pay electricity (see analyze2.py params).
- A new arm runs the smoke ticket (0470) end-to-end before real legs.

## Pre-register BEFORE the first leg

Hypotheses (H1/H2 style), the arm slate, prices, caps — written into the
concept note §8 and the tracker journal before any data exists for the new
arm. No protocol change mid-cycle; no early stopping (author ruled
2026-10-05: full passes only, futility-by-inspection after the fact).

## Run

- `drive2.py` — parallel driver: LOCAL lane strictly sequential (GPU
  exclusivity, solo-machine speed data), one worker per HOSTED arm
  (network-bound, overlap freely), 3-seat judge pool pipelined.
- Holes after a pass: relaunch drive2 (it skips recorded legs). Legs whose
  attempts were infrastructure voids must be freed FIRST — archive the
  attempt dirs to `runs-void/{leg}-infra-void-{cause}-{date}/` (evidence
  preserved, append-only respected); the attempt cap is LIFETIME, not
  per-pass, and blocked attempts make the re-pass a silent no-op.
- Document provider deaths and billing walls explicitly
  (`DNF-provider.json`), never as silent holes.

## Known harness warts (found cycle 2, fixed — keep them fixed)

1. `check_unloaded()` gates LOCAL arms only — hosted legs are
   network-bound; the old form voided 30 legs pre-pi during local-lane
   overlap.
2. The attempt cap (2) is lifetime: infra voids must be archived to
   `runs-void/` to free a leg; real attempts always count.
3. The record block must stay in sync with guarded pre-pi blocks (the
   `load1` NameError crashed hosted legs AFTER pi completed and destroyed
   worktrees via the finally).
4. Judged-ness = 3 seat FILES, not a judges dir (drive2 `judged3()`);
   judge.py is idempotent per seat (an existing seat file is final —
   re-judging is nondeterministic and overwrites settled verdicts).

Also: branch collisions are handled by design (`-r2`, `-preserved-<ts>`
suffixes); `stop-arm.sh` vram-wait polls VRAM thresholds that arm A's
resident server legitimately holds — wrap-ups are slow, not stuck.

## Judge

- Panel seats in `panel.json`, families DISJOINT from all candidate
  families (cycle 2: gemini / grok / minimax — all via OpenRouter, so an
  OR key-cap hit stalls the whole panel: watch the key limit, not just
  workspace credits).
- Blind: producer identity scrubbed; no leak tolerated (`leak` field).
- Rubric: start at 10, deductions REROLL/CHANGES/COMMENTS/NITS with
  evidence lines; BLOCKED/impossibility is a legitimate outcome; a
  principled refusal is scored on its merits, not auto-zero.

## Readout

Resolve the helper root from the runtime-supplied loaded skill path:

```bash
IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"
```


`python3 "$IDH_ROOT/scripts/tournament-analysis.py" --arena ~/arena`
(with `IDH_ROOT` resolved to the harness checkout) emits cumulative per-identity statistics, paired quality outcomes
and a Pareto frontier restricted to complete observations. The legacy
`analyze2.py` excluded non-OK legs and must not supply routing conclusions.
Model failures score zero, with consumed time and cost retained; infrastructure
errors stay pending until replayed. Display coverage beside every median.
Do not call equal paired medians strict dominance. Electricity is registered:
0.23 EUR/kWh, padme 600 W under load. Interim reads carry the easy-ticket
order bias — the big tickets (the killers) decide; never present a
mid-cycle read as final.

## Feeds

The cycle verdict updates skills/route (grid + routes.json) in the same
pass. Weak separators (the smoke ticket) stay IN the matrix — tests are
paired, exclusion would be data selection.

## Reporting methodology

Moved here from the route skill: these rules govern how cycle data is read, not
which worker to choose.

- Costs are per leg on the ten-ticket sample; cycles are additive and each
  (model @effort) identity stays distinct. Preliminary smoke runs are excluded.
  Locals pay electricity (0.23 EUR/kWh x 600 W, registered 2026-10-06); hosted
  pay the API (pi cost.total, component-priced).
- Model timeouts and admissible empty submissions score zero; include consumed
  time and cost, and show completion coverage. Provider/quota errors are invalid
  observations pending replay, not evidence of model abandonment. Identities
  with pending cases remain provisional and are excluded from final rankings.
- Paired comparisons retain model failures and report wins, ties and losses;
  an equal median difference does not establish per-ticket dominance.
- Difficulty is semantic: in the 16-arm data strong arms correlate 0.83-1.0 on
  which tickets are hard, while difficulty vs diff-lines is 0.08 (code-large
  holds both the easiest and the hardest tickets). Judgment / consistency
  tickets (0874, 0452) are the killers; concrete fixes (0333) and trivial
  swaps (0470) are not.
- 0470 is the smoke ticket: fast, fully characterized, near-zero variance. It
  validates infrastructure and does not discriminate models.
