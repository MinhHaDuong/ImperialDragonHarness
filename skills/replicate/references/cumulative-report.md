# Cumulative local report

This procedure runs after every stage, including a scope or approval stop.
It adds no command or publication authority. Read all written sections, compare
claims with current evidence, and retain contradiction-driven revisions before
building. Apply `report-style.md` for captions, checklist additions, robustness
counts, and truthful signature/disclosure. Reuse valid computations; a coherence reread is still required.

1. Choose the I4R template from `templates/INDEX.md`, using the
   context the folder already holds: the template I4R named in the assignment
   first. Otherwise use the kind of work and the paper's field and journal:
   choose Commentary from Forensic Report for forensic commentary on specific
   problems; choose Psychological Science Phase 2 for a reproduction report
   in that I4R project; use General for other reproduction and robustness
   reports. Psychology alone does not establish Phase 2 membership. If the
   context leaves the specific templates equally applicable, use General and
   explain the uncertainty. Copy the chosen Word or
   LaTeX files into `report/` if absent and record in `manifest.json`
   `template{name, record, version, reason}`; the reason is one sentence naming
   the evidence. The template governs the format, with Identification added immediately after
   the introduction under the cumulative stage contract. Where it is silent, follow
   `rules.md`.
   No template fits (a format or field none covers)? Say so, give the reason,
   and propose an adapted structure for this replication in
   `report/structure.md`, starting from the closest template and naming each
   section changed. Record the closest template with `"adapted": true`. Never
   add a new generic template to the skill. A person confirms the adapted
   structure before using that adapted structure; retain an available local opening and
   record the adaptation blocker meanwhile.
   Optionally read each record's `links.latest` on Zenodo (needs the network)
   and report a newer version; do not switch to it.
2. Write and compile the cumulative report in `report/` after each stage,
   stopping at the latest written section. Inventory begins the opening and
   provision assessment; identify adds Identification immediately after it;
   rerun adds Computational Reproducibility; challenge adds Robustness
   Reproduction (same data, alternative analytical decisions); complete
   writes the conclusion and rewrites the introduction and AI Disclosure.
   Keep relevant template-specific preregistration/other sections where
   evidence applies. Preserve their source and state unavailable evidence.
   Use the template's documented build route; inspect the compiled artifact
   and unresolved references. Record actual build/artifact status and blocker.
   A failed build or absent compiler cannot be reported as a compiled output. Name the paper's method in the summary
   (rule 8). Include all six rows of the Reproducibility Table, derived from
   `assessment.json`, with each evidence basis and any "not yet assessed"
   status visible (`assessment.md`). Show unexecuted rows as “not yet assessed — not yet run”
   when no execution evidence exists, with reasons; retain any verified
   provision-based impossibility and label its distinct basis. Unknown provision
   is “not yet assessed”, rather than a failed computation. Distinguish provision-based
   impossibility from observed execution failure. Show only discrepancies
   in the detailed statistic comparisons, rounding values to three digits
   from `out/reproduce.csv` and `out/robustness.csv`. This comparison display
   rule does not suppress or round the stored auxiliary artifact. Identify
   auxiliary estimates separately with their provenance and lack of numeric
   comparator; exclude them from match/discrepancy totals and score denominators.
   Report independent recomputations under `independent-recomputation.md`
   separately from author-code comparisons: production outcomes and strict
   printed-comparison outcomes, denominators, failed/not-run reasons, and
   stable target/scope/run provenance. Reconcile linked ledger targets and
   reruns without double counting; retain required unknown coverage and missing
   author code. This evidence supplies no canonical/selected scoring success
   or combined reproduced numerator.
   Report range/inequality assertions separately as confirmed, not confirmed,
   or unresolved, with target, source, boundaries, and coverage evidence. Keep
   their totals separate from numeric comparison counts and category derivation;
   include unresolved assertions even when detailed statistic lists show only
   discrepancies. Retain applicable empirical footnote evidence and explain
   bibliographic exclusions, unquantified assertions, and unresolved coverage
   under § Empirical footnote applicability in that reference, with declared
   whole-paper/selected scope visible. Put each robustness result beside its original estimate.
   Disclose AI assistance. If selected-target work was requested, also show its
   separately labelled six-row table and target declaration. Keep any reference
   comparison scoped and distinguish printed categories from inferences under
   `assessment.md`; mismatched or unknown scope supplies no
   unqualified agreement score.

3. Maintain one local `report/<citekey>-replication.html` note draft from the
   compiled report's current evidence, stage/status, scope, and blockers. Do not
   claim an unavailable build succeeded; a pending draft states that limitation.
   Follow the skill's Zotero note section for frontmatter and host outward gates.
4. Collect AI provenance from the start in existing README/report records:
   host and harness repositories and commits (including the skill version),
   stage/role, actual observed identity or unavailable, calls and work-share
   evidence where measurable, source/exposure boundaries, and reviewer limits.
   Requested model pins do not prove served identity. Complete uses these
   records to finalize AI Disclosure; missing historical evidence stays missing.
5. Carry `acquisition.md` producer inventory and actual replay evidence into
   the report, including unreplayed reasons and separately proposed temporal
   extensions. Distinguish in-frame/out-of-frame checks and their original
   estimates, applicability, approval, and actual dispositions under
   `report-style.md`; unavailable evidence never fulfills the outside-frame
   proposal obligation. Preserve all signed-plan dispositions: completed, failed, blocked, withdrawn,
   adverse, and inconclusive results, reasons, and amendments. Scope limits and
   missing execution stay visible through complete. Keep computational misses
   beside separately evidenced cause/impact judgments under
   `scientific-appraisal.md`; scientific plausibility never rewrites a frozen row.
   Apply `discrepancies.md` for the comparison type, prespecified diagnostics,
   second-digit counts, and sourced specification-selection discussion after
   a key-result reversal.

Local report order follows the science. Identification is source-based and
runs no new estimates; its threats lead to approved challenge checks. Deep
literature is separate. The report exists from inventory rather than waiting
for a final command. One resumed request updates one note draft, without
publishing it or mutating historical notes/frozen artifacts.
