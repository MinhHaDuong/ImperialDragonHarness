# Decorrelation doctrine

What "an independent review" means. Review skills, profiles and rules point here.

## Three axes

- **Angle**: seats look at different things (correctness, scope, red team). Buys coverage, not independence.
- **Lineage**: seats come from different model families (the `family` field of a grid row). Buys errors that are less likely to be shared with the producer.
- **Replication**: same model, same prompt, different sampling. Catches random slips, not systematic bias.

The arena judge panel is lineage-decorrelated and same-angle: one rubric, three families, none a candidate's. A multi-angle panel of one family is a thoroughness check, not an independent review.

## Scale the review to the risk

Most changes are small and cheap to verify; one cheaper reviewer from the producer's own family is the normal case.

| Change | Review |
|---|---|
| Trivial or mechanical (typo, ticket bookkeeping, data refresh, a rename with a green test) | One same-family reviewer. No cross-family seat. |
| Ordinary (a feature or fix with tests, a doc rewrite) | The usual angles; same family is fine. Report the family; do not call it independent. |
| High risk: a wrong approve would be hard to detect or reverse after merge (rules and guards, merge and release gates, credentials, deletion or migration), or the author asks | At least one seat from another family. |

The orchestrator picks the row. When unsure, take the lighter one.
`PANEL-INTEGRITY: DEGRADED` is for a seat that was required and could not run, not for a same-family review.

## Independent means another family

- A review is **independent** only when at least one seat comes from a different family than the producer. Take the producer's family from the grid `family` field of the model actually run, never from the provider or door (GLM served through Mistral is still GLM). A lineage twin counts as the same family.
- Replication substitutes for lineage only when no other-family seat is reachable; the report then says "same family, not independent".
- When a required other-family seat is unreachable, say so. Never simulate one.

To get a cross-family seat from Claude Code, whose `Agent` children are all Anthropic, start a headless CLI from bash: the `headless` entry in `routes.json` `launch_doors` whose `families` excludes the producer's, through the cheapest live door, with the full seat contract in the prompt (`skills/review-pr/SKILL.md`, detached-seat substitution). If it cannot run, record `no report` and write `PANEL-INTEGRITY: DEGRADED`, naming the missing perspective. Cross-family seats cost real money (key caps, credit walls in `routes.json`); state the spend in the report.

## The launch line

Before launching a worker, write one line: `worker | family | effort | risk row | reason`. Example: `haiku | Anthropic | medium | trivial | ticket bookkeeping, cheapest adequate`. The reason is the point: writing it forces the proportionate choice.
