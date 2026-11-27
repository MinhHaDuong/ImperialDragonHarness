# Independent recomputation contract audit

Product under review: `b6c6ed7fbb31f2bcddbc26a14f829039a1c36c20`.
Pinned base: `9c1faa5a989f6d0197cd1d3a1eb997c26ffbcc87`.
Documentation-only audit; hypothetical cases below are neither executed paper
estimates nor scientific findings. No scientific scripts or frozen reports changed.

## Source and authority

- [1597 exits and accepted plan](../../tickets/1597-replicate-independent-recomputation-evid.erg).
- [1580 A6 source, receiving ledger, and standing boundaries](../../tickets/1580-replicate-author-review-of-the-two-pilot.erg).
- [Recovered original A6, author message and dispatch qualification](../../tickets/reviews/t1580/recovered-source.md#additional-original-source-constraints): the author requests useful recomputation despite absent code; the accepted dispatch supplies the separate label/count. No scoring promotion is inferred.
- [Distinct feasibility](../../tickets/reviews/t1580/feasibility.md): prospective sidecar, production/comparison separation, and unchanged canonical assessment.

## Discriminating scenarios

The audit applies the normative document to contrasting possible states, rather
than searching for a preferred phrase. Each outcome below follows from the cited
contract; the rejected alternative would change the evidence or authority.

| Hypothetical input | Required outcome | Rejected alternative and contract evidence |
|---|---|---|
| A uniquely sourced mean matches print; author code is absent; another required statistic is unexamined | Independent production `recomputed` and separate printed `match`; missing code and unknown required target stay visible; no canonical/selected success | Promoting the subset to Fully or CRA/CRR success would violate [assessment separation and required coverage](../../skills/replicate/references/independent-recomputation.md#keep-assessment-and-counts-distinct) |
| The same eligible producer completes but its value misses strict printed precision | Production remains `recomputed`; comparison is `discrepancy`, with full output and printed source/precision | Treating every successful producer as a match, or rewriting a canonical failure, violates [separate production and comparison](../../skills/replicate/references/independent-recomputation.md#retain-production-and-comparison-separately) |
| A mean needs an unresolved weight or denominator convention | Record the gap before computation; no implicit convention selected by agreement | A short calculation alone cannot establish triviality under [prospective eligibility](../../skills/replicate/references/independent-recomputation.md#decide-eligibility-before-computing) |
| The quantity is fully determined but outside the authorized rerun perimeter | `not_run` with reason and needed next step; no computation | Triviality supplies no scope, acquisition, challenge, or translation authority under [eligibility](../../skills/replicate/references/independent-recomputation.md#decide-eligibility-before-computing) |
| An authorized independent attempt fails before a value exists | Retain `failed`, attempted step/log and reason; comparison unresolved, unavailable value/difference empty | A success-only ledger or invented difference violates [retention and provenance](../../skills/replicate/references/independent-recomputation.md#retain-production-and-comparison-separately) |
| A produced quantity has an ambiguous/missing exact comparator, or only a sourced inequality | Comparison unresolved; retain auxiliary value or separate assertion evidence with links as applicable | Auxiliary or assertion evidence cannot fabricate a numeric comparator under [separate ledgers](../../skills/replicate/references/independent-recomputation.md#retain-production-and-comparison-separately) |
| A target has repeated runs and contributes a quantity also used in assertion evidence | Separate target coverage from run attempts, reconcile IDs/overlap, retain each run; report separate evidence totals | Counting attempts as new targets or pooling all ledgers violates [counting units](../../skills/replicate/references/independent-recomputation.md#keep-assessment-and-counts-distinct) |
| An authorized faithful Stata translation meets its complete model/sample/SE and required-output evidence contract | Its existing canonical CRA eligibility remains available, separately labelled by actual method | Treating an ad hoc independent statistic as that route, or prohibiting the existing route, violates [faithful-route preservation](../../skills/replicate/references/independent-recomputation.md#keep-assessment-and-counts-distinct) and [unchanged eligibility](../../skills/replicate/references/assessment.md#faithful-stata-to-python-cra) |

All scenarios satisfy the four exits on the reviewed product. This is a semantic
contract audit, not a claim that any replication has supplied these evidence fields.
Reporting links are present in rerun/user output, cumulative-report, assessment,
and rules. The new reference centralizes the contract; no wording-pin tests added.

## Mechanical and preservation evidence

From the owned worktree, frozen `uv sync --frozen`, `UV_LINK_MODE=clone`, own
`.tmp/uv-cache` and `.tmp/ruff-cache`, and `env -u TMPDIR` were used. The Makefile
adherence declaration was read and `make -n lint` confirmed its command.

A standard-library byte comparison enumerated the pinned base's template paths
with `git ls-tree`, required a nonempty list as positive control, then compared
`git show <base>:<path>` bytes to each current file. Observed: all seven template
artifacts byte-identical. A second byte/string comparison verified that the entire
assessment reference from `## assessment.json` onward was identical to that base:
schema, categories, canonical/selected CRA/CRR eligibility, comparison vocabulary,
assertions, and auxiliary contract remained unchanged. Only its introductory
pointer was extended. `git diff --check` passed. No template files, frozen science,
scientific appraisal, identification review, or robustness menus were modified.

`make lint`: PASS, 191 passed, 3736 deselected (13.16 s).
`make check-fast`: initial sandbox run had 1769 passes and 197 setup errors;
the common observed error was socket construction denied with `PermissionError`
in the existing `tests/zotero_live.py:135` fixture. No assertion failure or
product change was inferred from that result. The unchanged full fast target
was rerun with elevated local socket access: PASS, 1966 passed, seven existing
deprecation warnings (8.36 s). No tests or gate scope were changed.

Distinct semantic review of the immutable product is preserved in
[adherence-semantic.md](adherence-semantic.md), with no findings. The reviewer
was a separate native context; served model/effort were unavailable. The
product was committed and `git rebase origin/main` reported already up to date
before lint and fast verification. The later evidence commit adds no product edits.

```yaml
adherence: PASS
mechanical_runner: ran
escalation: null
semantic_review:
  applicable: true
  status: ran
  reason: independent evidence architecture needs semantic verification
  rule_sources: [rules/guards.md, rules/git.md, rules/workflow.md, rules/authoring-skills.md, rules/prose/_all.md, rules/lang/en.md]
  worker_id: /root/raid1580_lead/blind_design
  model: unavailable
  family: OpenAI shared family, no lineage independence
  effort: unavailable
  route: requested gpt-6.1-sol/OpenAI/medium, native distinct parent context
  launch_evidence: immutable product head/tree/branch review request before evidence commit
  completion_evidence: design/1597-independent-recomputation/adherence-semantic.md
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

Reference-resolution phase 1.0 has no TeX/Quarto/Bib diff. Optional trace-path
scan was not requested. The local Markdown source links were resolved against
the owned tree; the referenced source ticket remains open at this product head.
Parent closure owns propagation of its eventual archived ticket path.
