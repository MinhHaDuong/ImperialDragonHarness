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

### Sizing a gaze brief

This section is the one home for how much review a merge request gets. The
orchestrator (`/raid`, `/hunt`, `/merge`, or the author) writes the `/gaze`
brief (`skills/gaze/SKILL.md` § The brief); gaze runs it and does not resize
it. It is judgement, not a floor or a category: the orchestrator knows the
diff, the risk, what was already reviewed and what changed since, and the
brief is where it says so. Two earlier attempts failed in opposite ways, a
hunt-owned plan with a risk floor (tracker 1100) and a "no floor" rule that
left the choice inside gaze (ticket 1176).

Size from four facts: what the diff touches, how hard a wrong approve is to
detect or undo (the table above), what an earlier round already read, and
what moved since. Name the scope when a review already covered the rest.
Worked cases:

| Change | Brief | Why |
|---|---|---|
| One-paragraph prose deletion the author already agreed to | `seats=consistency; scope=all` | One seat checks that nothing points at the cut text; a five-seat panel (PR 1667) spent ten minutes on agreed text. |
| Rebase or merge of main only, nothing of the branch's own changed | No new gaze: the earlier result stands when the tip adds only a bookkeeping delta (`skills/merge/SKILL.md` § Gating tiers); if the merge resolved a conflict, `seats=correctness; scope=paths:<conflicted files>` | The branch's diff was read; only the resolution is new. |
| Fix of listed findings | `seats=<the seats that raised them>; scope=<previous reviewed head>..HEAD` | The seats that found the defects check the fix, on the fix only; a fresh full panel re-reads what passed. |
| Large multi-file change (PR 1677: 7 files, about 200 lines, took four full panels) | Round 1: `seats=correctness,consistency,scope,simplify; scope=all`, plus `red-team` from another family on the high-risk row; later rounds: the fix case | Width once, then narrow: each later round reads only what moved. |
| Edit of `memory/MEMORY.md` or `memory/topics/` | Run gaze, although the tier is bookkeeping, with `seats=none` (one adherence seat) by default; widen to `consistency` when the entry changes guidance sessions act on | Every session reads these files as guidance (ticket 1223); the tier keeps them bookkeeping for the record's checks, and the brief, not the tier, buys review when needed. |

## Independent means another family

- A review is **independent** only when at least one seat comes from a different family than the producer. Take the producer's family from the grid `family` field of the model actually run, never from the provider or door (GLM served through Mistral is still GLM). A lineage twin counts as the same family.
- Replication substitutes for lineage only when no other-family seat is reachable; the report then says "same family, not independent".
- When a required other-family seat is unreachable, say so. Never simulate one.

To get a cross-family seat from Claude Code, whose `Agent` children are all Anthropic, start a headless CLI from bash: the `headless` entry in `routes.json` `launch_doors` whose `families` excludes the producer's, through the cheapest live door, with the full seat contract in the prompt (`skills/gaze/references/panel.md`, detached-seat substitution). If it cannot run, record `no report` and write `PANEL-INTEGRITY: DEGRADED`, naming the missing perspective. Cross-family seats cost real money (key caps, credit walls in `routes.json`); state the spend in the report.

## The launch line

Before launching a worker, write one line: `worker | family | effort | risk row | reason`. Example: `haiku | Anthropic | medium | trivial | ticket bookkeeping, cheapest adequate`. The reason is the point: writing it forces the proportionate choice.
