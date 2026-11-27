# Verification — cumulative replicate interface

## Unit and provenance

Product head `85ff8b30c4ddcd4a2353e14830d69391e26a5723`, base
`193d610faf3340e1cd29c6c64a16cf83cb908b54`. Worker context
`/root/raid_delivery/hunt1590`, native tool route; actual serving model and
reasoning effort unavailable in runtime metadata. Requested model pins are
not observed identities. Parent report provenance is separate in
`receiving-checkpoint.md`; no cross-family independence is claimed.

Deliverable is documentation/interface behavior. Scenario controls below are
source-based walkthroughs, not a scientific run or a fresh-paper rehearsal.
They introduce no code, new assertion tests pinning prose, helper/service,
schema, foreign project operation, estimates, migration, or rescore.

## Source/scenario controls

All anchors are relative to `skills/replicate/` at the product head. Each
scenario was walked through its trigger, required stage order, evidence
updates, output, and stopping boundary against the final sources.

| Scenario input | Observed instruction path and required disposition |
|---|---|
| Fresh request for identify | SKILL opening table and Every stage1–4 perform inventory then identify; inventory opens report/note, identify follows opening before Computational Reproducibility. Every written section is reread and each stage builds through its latest section. No estimate execution is authorized. |
| Resume challenge with valid rerun rows and completed/failed/blocked/withdrawn checks | Every stage1–2 revalidates evidence, rereads sections, and reuses valid computations; challenge5 reads dispositions so absent CSV rows do not masquerade as unattempted checks. Same note draft, no duplicate comparison results or level-history change. |
| Later text/code/sample contradiction contradicts earlier opening or assessment explanation | Every stage2 records old claim, new evidence, changed section, date, and reason; scientific-appraisal retains first-run observations, cause, and impact separately. All cumulative sections are corrected/rebuilt; frozen classifications remain intact. |
| No run or missing input; request complete | Rerun5–6 establishes no run criterion without actual evidence; Every stage4, assessment status guidance, and cumulative-report2 visibly retain not-yet-run/reason and independently verified provision-based impossibility. Complete cannot manufacture computations or bypass approval. |
| Caller supplies main-result or whole-paper execution scope | Rerun Choose execution scope bypasses question, records caller perimeter before computation, and keeps canonical whole-paper dossier plus any selected-target declaration separate. Whole-paper applicability still includes empirical supporting footnotes and SI. |
| Scope unspecified, no answer yet, manual continuation unavailable | Rerun scope procedure records question/time; before five elapsed minutes no computation. Disclose absence of automatic continuation, keep pending, compile report/note. No claim that a timer resumed work. |
| Explicit resume after five minutes without answer | Verify elapsed time and use the author-authorized main-result default, recording requested/actual perimeter and unexamined coverage. This fallback belongs to an unanswered generic question. |
| Explicit resume carries a later actual whole-paper answer | Rerun scope procedure uses actual answer if supplied, including after elapsed default time while pending; no second question or silent main-only substitution. |
| Explicit I4R choice but authoritative assignment perimeter unavailable | Rerun scope paragraph and templates/INDEX Cumulative use require primary source/version and exact target inventory/gaps. Scope stays unresolved; pilot Tables1–3 and generic template coverage cannot select the perimeter or trigger main-only fallback. |
| Approval refused, silent, stale, conditional, or outside delegated perimeter | Challenge4 and probe-approval require valid plan/version approval and fulfilled conditions. No signature timeout. Local partial report/note persists; complete cannot bypass the stop. File/conversation provenance and truthful transcription remain distinct from an actual author signature. |
| Blind advisor wants title discovery or answer-bearing Highlights/report | Inventory blind boundary, identify brief-before-lookup, main-result source boundary, and validation exclusions forbid that route. Missing permitted evidence stays a gap; no estimates or excluded-source retrieval is authorized. |
| Noncausal descriptive/predictive/meta-analysis claim | Identify and scientific-appraisal use appropriate argument/model/facts and explicit coverage, with no forced causal DAG or pooled estimates. Causal cases retain separate graph fidelity/credibility and actual reviewer disagreement/limitations. |
| Challenge planning after material identification threat | Challenge1–3 links candidates to threat/premise, requires at least one fair main-result check outside the paper's statistical frame, preserves published-footnote/asserted-check distinctions and full dispositions. Infeasible checks remain blocked, not fulfilled by assertion. |
| Appraisal proposes a changed specification versus faithful path repair | Rerun3 and scientific-appraisal distinguish ordinary faithful path/environment repair with preserved original evidence from new empirical/specification variants requiring existing approval. No new authority. |
| Computational miss has plausible scientific explanation | Existing scientific-appraisal cause/impact evidence and first-run preservation remain. Small size alone cannot erase a miss, widen tolerance, or promote a category. |
| Every stage builds and updates note; later publication requested | cumulative-report1–5 and Zotero note maintain one local draft and report actual build failure as blocked. Complete rewrites intro/conclusion/disclosure from collected provenance; host review/merge and outward gates remain. No automatic frozen-note migration. |

The scenarios yield no observed instruction contradiction after the no-run
display was reconciled across rules/assessment/report guidance: it is a
visible explanation, not a new stored status or category. These walkthroughs
cannot establish scientific quality, actual compiler availability in a receiver,
or a runtime's ability to wake itself. Those are explicitly outside this unit.

## Byte and structural controls

A temporary Python source-control command used `git show <base>:<path>` and
current file bytes, with section/fence extraction and subprocess comparisons.
All comparisons below returned true; command exited0. It was a one-time
verification command, not a new shipped helper or prose-wording test.

- Every fenced schema/code example in assessment.md is byte-identical.
- Entire Comparison CSVs, Comparing two reproductions, Published assertions,
  and Auxiliary estimates sections are byte-identical to the base.
- The1584 approval body beginning “Before any robustness execution” and the
  entire1585 main-result reference are byte-identical.
- All six template binaries are byte-identical to base Git blobs.
- Only the five current command headings are present. Positive control on
  the base found the old four headings; source detection was not vacuous.
- Literal CSV stage enumeration remains reproduce/robustness; every changed
  path is inside this skill/catalog or ticket1590 evidence. No scientific
  folder or old case record changed.

## Commands and outcomes

All locked tool commands ran from the owned worktree with TMPDIR unset,
`UV_CACHE_DIR=$PWD/.tmp/uv-cache` and `RUFF_CACHE_DIR=$PWD/.tmp/ruff-cache`.
The initial default cache was read-only; the first own-cache attempt could
not resolve the locked DOIfetch source in sandbox DNS. Authorized elevated
`uv sync --frozen` with own cache and clone link mode then succeeded, without
dependency or lockfile edits. Native local fixture sockets/Git metadata required
the same authorized elevation; no product workaround was introduced.

| Command | Actual result |
|---|---|
| `make skills-catalog` | Passed; generated catalog updated from frontmatter. |
| `make -n lint` then `make lint` | Declared adherence runner inspected and executed;191 passed,3736 deselected,12.81s. |
| `make check-fast` |1966 passed,7 warnings,10.19s. Existing positional-maxsplit deprecation warnings, no failures. |
| `git diff --check` | Passed. |
| `uv run --frozen python3 scripts/touched-tests.py --base origin/main` | Exit4; selected:none; fallback:none; result:skipped(no source or test file changed). This is a skip, not a test pass. |
| `uv run --frozen python3 scripts/scoped-check.py --dry-run` | Exit2: no `.idh-checks.json`; no mapped scoped gate exists and no scoped pass is claimed. Parent must run declared merge checks. |

Reference-resolution phase: no changed .tex/.qmd/.bib. No trace supplied for
optional trace-path scan. Required distinct semantic adherence and wave
integration reports are supplied by parent after this stable product head;
their actual evidence is recorded separately before any PASS claim. Merge
gate/after-merge, actual rehearsal, and batch freeze remain caller/receiver-owned.

## Scope left open

1580's report-style ledger remains separate: W15/W17 absent in dispatch;
formatting, diagnostic, attributed-work-share, sourced menu, and other ledger
rows are not claimed delivered merely by this interface rewrite. Existing
approval, selection, empirical-footnote, scientific-appraisal, and miss/cause/
impact children retain their complete criteria.1591 must dispatch the exact
landed skill revision for real receiver rehearsal and batch freeze.1592 is
separately owned.1589 stays open until receiver evidence and integration;
closing this unit cannot close that tracker.
