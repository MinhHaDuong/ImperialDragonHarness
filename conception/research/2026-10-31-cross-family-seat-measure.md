# Do other-family review seats find more? A measure on our own records

2026-10-31. Read-only analysis of `memory/evidence/attribution/*.md` (212 records,
2026-10-05 to 2026-10-31) by a Sonnet subagent, asked to measure rather than argue.
It motivated dropping the cross-family gate (decorrelation.md § Family is a preference,
not a gate). Companion to [ensemble-decorrelation-evidence.md](./ensemble-decorrelation-evidence.md).

## Method

- Seats: review-step seats with `status: ran`, self and gate seats counted apart.
  The records carry no `family=` field, so family comes from the model prefix and
  the runtime. The ticket 1388 mislabel (`anthropic/gpt-*`) was corrected on 5 seats.
- "Valid" is proxied by **adopted** (the finding was acted on). "Unique" means no
  other seat of the same PR carries the same `path:line` anchor.
- Positive control: known findings of PRs 1199, 1288 and 2073 were all picked up
  and classed correctly. All 968 finding lines parsed, with no orphan.

## Results

| Seat vs producer | PRs | Seats | Findings/seat | Adopt % | Unique-adopted | Seats with ≥1 adopted |
|---|---|---|---|---|---|---|
| Same family | 157 | 961 | 0.59 | 60% | 154 | 20% |
| Other family | 111 | 259 | 1.15 | 56% | 102 | 31% |
| Self | 27 | 44 | 0.89 | 36% | 9 | 20% |
| Local (padme) | 1 | 1 | 2.00 | 50% | 0 | 1 of 1 |

Within the 64 PRs whose panel mixed both, other minus same, bootstrapped over PRs:

| Measure | Difference | 95% interval |
|---|---|---|
| Adopted findings per seat | +0.28 | +0.11 to +0.45 |
| Unique-adopted findings per seat | +0.23 | +0.11 to +0.37 |
| Seats with ≥1 adopted finding | +0.11 | +0.03 to +0.19 |

On the same angle, the difference shrinks: red-team seats find about 1.2 per seat
in either family. Median seat latency was 52 s for Anthropic and 37 s for OpenAI
seats (50 timings). Spend is not recorded.

## What it can and cannot support

- **Supported:** other-family seats raise more findings per seat. In mixed panels
  they also get more findings adopted per seat.
- **Not supported:** "more valid defects". Adoption is decided by the producer's
  side. Severity is unrecorded: 1 finding line is blocking, 445 verifiable, 522
  consider. No miss by a same-family panel was ever tagged, so recall is unmeasured.
- **Confounders:** the other-family seat is a different tool with a harsher brief
  (headless read-only red team), it was added to higher-risk PRs, and same-family
  seats are dominated by cheap rounds (adherence, scope, reruns). Only 8 PRs pair
  an OpenAI producer with an Anthropic reviewer. The local seat is a single case.

A cleaner test randomizes which family gets the same brief on the same PR and
judges validity apart from adoption. Nothing schedules it: no decision waits on it.
