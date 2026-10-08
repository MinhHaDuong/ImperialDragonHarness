# Decorrelation doctrine

The one place that says what "an independent review" means. Review skills,
profiles and rules point here. Absorbs ticket 1057.

## Three axes

| Axis | What differs between seats | What it buys | What it does not buy |
|---|---|---|---|
| Angle | The perspective: correctness, consistency, scope, red team | Coverage of different defect classes | Independence from the producer's blind spots |
| Lineage | The model family (the `family` field of a grid row) | Errors that are less likely to be shared with the producer | Coverage of a perspective nobody was asked to take |
| Replication | Nothing but sampling noise: same model, same prompt | Catches random slips | Any systematic bias; the producer's family agrees with itself |

The arena judge panel is a lineage-decorrelated, same-angle panel: one
rubric, three families, none of them a candidate's family. A multi-angle
panel of one family is a thoroughness check, not an independent review.

## The rule

- A review counts as **independent** only when at least one seat comes from
  a different family than the producer. Take the producer's family from the
  grid `family` field; in an attribution record derive it from the provider
  prefix of the `model` id. A lineage twin (same family, different build) is
  labelled in the grid and counts as the same family.
- **Replication substitutes for lineage only when no other-family seat is
  reachable**, and the report then says "same family, not independent".
- Capability is chosen from the grid for the work. There is no rule that a
  reviewer sits below or above the producer; there is no "sibling minimum".
  When risk is high, take the strongest other-family seat that is reachable.
- When no other-family seat is reachable, say so in the report. Never
  simulate one.

## Default on a Claude-produced change

1. Every `Agent` child in Claude Code is Anthropic, so the extra seat is a
   headless CLI started from bash, from `launch_doors` in `routes.json`
   (the `headless` entry whose `families` excludes the producer's).
2. Attempt one such seat through the cheapest live door, with the full seat
   contract in its prompt (`skills/review-pr/SKILL.md`, detached-seat
   substitution).
3. If it cannot run, record the seat as `no report` and write
   `PANEL-INTEGRITY: DEGRADED` in the report front matter, naming the
   missing perspective.

Which doors exist today (2026-10-08, `routes.json` carries the status):
`codex exec -m <openai model>` runs and reaches OpenAI only; `pi` reaches
whatever providers are configured on the host (padme: huggingface and local
seats); `vibe -p` cannot be a seat because file tools are denied headless
(ticket 1017). Cost is real: the OpenRouter key has a monthly cap and the
OpenAI account has hit a credit wall. State the spend in the report.

## Mechanical floor

Every skill that launches workers must say that the model is chosen per
launch from the route skill. `tests/test_launch_model_choice.py` fails a
skill body that launches workers without saying so, so an omitted choice is
a CI failure and not a silent inheritance of the session model. The test
checks that the statement exists; the choice itself stays the orchestrator's
judgment.
