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

## Scale the review to the risk

Most changes are small and cheap to verify. A straightforward review by a
cheaper model of the same class, in the producer's own family, is the normal
case and is enough. Independence is bought only where it pays.

| Change | Review |
|---|---|
| Trivial or mechanical (typo, ticket bookkeeping, data refresh, a rename with a green test) | One same-family reviewer, at or below the producer's class. No cross-family seat. |
| Ordinary (a feature or fix with tests, a doc rewrite) | The usual angles, same family is fine. Report the family; do not call it independent. |
| High risk (rules and guards, merge and release gates, credentials, deletion or migration, anything hard to reverse, or the author asks) | At least one seat from another family. |

The author or the orchestrator decides the row; when unsure, take the lighter
one. A same-family review is never reported as independent, but it is not
degraded either: `PANEL-INTEGRITY: DEGRADED` is for a seat that was required
and could not run.

## The rule for an independent review

- A review counts as **independent** only when at least one seat comes from
  a different family than the producer. Take the producer's family from the
  grid `family` field; in an attribution record derive it from the provider
  prefix of the `model` id. A lineage twin (same family, different build) is
  labelled in the grid and counts as the same family.
- **Replication substitutes for lineage only when no other-family seat is
  reachable**, and the report then says "same family, not independent".
- Capability is chosen from the grid for the work, and a cheaper model of the
  same class is a legitimate reviewer. There is no "sibling minimum".
- When an other-family seat was required (high risk) and none is reachable,
  say so in the report. Never simulate one.

## When a cross-family seat is required

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
