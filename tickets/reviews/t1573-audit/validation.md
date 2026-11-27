# Ticket 1573 validation

## Scope and semantic mapping

The author-stage join checklist covers coded keys after the authors' preceding
transformations, before checker normalization; row/key denominators, duplicate
multiplicity and many-to-many expansion; unmatched literal-key samples; and
missingness traced into constructions and downstream samples. The construction
table compares text, notes/appendices, and code with source anchors and preserves
contradictions as anomalies. These correspond to findings 1/2 in parent 1572
and the read-only Atanasov comparison at replicator df890ef. No paper-specific
case was copied and no scientific run or foreign write occurred.

## Checks

- `make lint`: 191 passed, 3736 deselected.
- `make check-fast`: 1966 passed, seven pre-existing deprecation warnings.
- Byte preservation: removing the exactly two new binding audit lines and
  their separator restores baseline SKILL.md byte for byte; assessment.md
  and rules.md match aa5772f2b249f42952564a39042649c5dfd8501e byte for byte.
- `git diff --check origin/main...HEAD`: passed.
- Initial rebase before committing refused unstaged changes; after the narrow
  commit, rebase reported the branch up to date. No stash or overwrite used.
- An unprivileged `merge-gate.py tier` reported conflict while git metadata
  were read-only; that output is not a confirmed merge-conflict diagnosis.

## Runtime evidence

Native collaboration exposed task /root/raid_1568/coder1573 and its semantic
worker /root/raid_1568/coder1573/adherence1573. The requested route was
Sol 6.1 medium, OpenAI, native subscription. Full served model and effort
identifiers were not independently exposed; requested pins are not observed
identity. No paid API route or independent-family review is claimed.

## Adherence verdict

adherence: PASS. Mechanical runner `make lint` ran under the Makefile's
explicit adherence contract. Prose reference resolution was inapplicable
(no TeX, Quarto, or bibliography changes); no trace input was supplied.
Semantic review was required for skill instruction changes and ran as a
distinct native worker, with valid rule-by-rule evidence and no findings:
`adherence-semantic.md`. Observed worker task is recorded above; observed
full model/family/effort are unavailable. No inline self-review substitutes
for that worker. Report completion was observed by `wait-roster.py` and
reading its completed artifact.
