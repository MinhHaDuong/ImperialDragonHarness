# Adherence verdict for ticket 1579

Reviewed implementation: `aedbd7e6d9805545d2f8b84a4d97e5198d7950cd`.

```yaml
adherence: PASS
mechanical_runner: ran
mechanical_command: make lint
mechanical_declaration: Makefile:32
reference_resolution: skipped (no tex/qmd/bib changes)
semantic_review:
  applicable: true
  status: ran
  reason: skill/schema/report instruction changes
  worker_id: 01a21cb0-046f-7561-8cda-e65d07050046
  model: gpt-6.1-sol
  family: OpenAI
  effort: medium
  route: native headless Codex subscription, read-only, API-key variables removed
  launch_evidence: observed runtime header below
  completion_evidence: valid completed semantic YAML report below
mechanical_failures: []
escalation: null
```

Lint, fast checks, catalog drift, existing ticket/skill agnostic guards, and
canonical preservation checks passed. The semantic worker found one
non-blocking positional-reference nit (original report preserved below).
Resolution: replaced “schema above” with a link to the named comparison CSV
section; manually verified the heading and its Markdown anchor. No wording
matching test was added. Final gaze reviews this correction with the final
head. No substantive instruction, schema, or scoring behavior changed.

No cross-family independence is claimed. Native writer identity stays masked
under runtime-identity.md; the header below belongs only to the distinct
semantic-review process, with its host-specific workdir explicitly redacted.

```text
OpenAI Codex v0.172.0
--------
workdir: [redacted: host-specific worktree path; identity fields preserved]
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a21cb0-046f-7561-8cda-e65d07050046
--------
```

## Original semantic report and finding

```yaml
reviewed_rules:
  - rule_section: "rules/git.md — Reading state you will act on"
    evidence: >-
      Plumbing verified HEAD and branch t1579-auxiliary-estimates both equal
      aedbd7e6d9805545d2f8b84a4d97e5198d7950cd. Base
      7a4ce909985c8d9ab05e3ccfd3883068970f4649 resolves and is an ancestor
      of the reviewed head. Working tree is clean.

  - rule_section: "rules/guards.md — Project boundary, credentials, and memory"
    evidence: >-
      Review reads stayed within this repository. The six-file diff contains
      skill documentation, its child-ticket log, and review records; no
      credentials, foreign-project changes, or memory promotion appear.

  - rule_section: "rules/git.md — Branch and commit; Commands that destroy silently; Merging"
    evidence: >-
      Review concerns the named task branch. The head commit explains the
      separation from scored comparisons and preservation of existing decisions.
      This review performed no git mutations, synchronization, or merge;
      landing requirements are outside this review's authority.

  - rule_section: "AGENTS.md — Project memory; Skills catalog; Agent profiles"
    evidence: >-
      Read memory/MEMORY.md and relevant skill/runtime themes. Skill name,
      description, category, and ordering metadata are unchanged, so catalog
      regeneration is not triggered. No profiles or tool grants change.

  - rule_section: "rules/workflow.md — Trust, Verify, Monitor; Diagnosis discipline"
    evidence: >-
      Independent source comparison confirmed assessment/coverage/selected-target
      text and manifest/intake text are byte-identical to base. Comparison
      columns, statuses, and tolerance text are byte-identical apart from the
      appended auxiliary-display clarification. These are source-preservation
      results, not evidence of scientific execution.

  - rule_section: "rules/workflow.md — Check scope; Delegation; Autonomous action"
    evidence: >-
      This is the requested distinct semantic adherence review, not gaze or a
      full gate. No additional agents, edits, forge writes, scientific runs,
      or paid APIs were used. Full diff and all six changed documents were read.

  - rule_section: "rules/workflow.md — Cross-project work; Ticket discipline"
    evidence: >-
      Parent 1575 records receiving authority and accepts B5 as child 1579
      (tickets/1575-replicate-stata-transcription-caveats-refe-o.erg,
      Receiving Imagine). Child 1579 states the narrowed documentation scope.
      The diff neither changes the source project nor closes the parent.

  - rule_section: "tickets/AGENTS.md — Append-only logs and artifact placement"
    evidence: >-
      tickets/1579-replicate-preserve-unprinted-estimates-o.erg:8 appends a
      dated implementation entry without rewriting earlier entries.
      Supporting records live under tickets/reviews/t1579-20261127/ and
      are referenced from the ticket.

  - rule_section: "rules/authoring-skills.md; full guide — Worker routing and capabilities"
    evidence: >-
      Added skill instructions name artifacts, roles, and evidence requirements,
      without model pins, capability tiers, or new runtime-specific tool calls.
      The model observation in runtime-identity.md:3 is an identity record,
      not worker-selection policy.

  - rule_section: "skills/harness-doctor/references/authoring-skills.md — Discoverability, frontmatter, splitting, concurrency, and toolkit principles"
    evidence: >-
      Existing quoted frontmatter and verb structure remain unchanged.
      No new command, helper, dependency, batch API workflow, or multi-step
      execution procedure is introduced. The shared auxiliary contract is
      referenced from reproduction and reporting rather than duplicated.

  - rule_section: "Full authoring guide — Explicit measurement limits; AGENTS.md — Reviewer identity"
    evidence: >-
      assessment.md:467-481 requires inspected comparator-absence evidence,
      actual run provenance, and separate failed/blocked records.
      runtime-identity.md:3-5 keeps native-writer identity runtime-masked
      and assigns externally observed review headers only to their own
      processes; such headers cannot establish the writer's identity.

  - rule_section: "Parent 1575 B5; child 1579 — Auxiliary retention and provenance"
    evidence: >-
      assessment.md:451-474 specifies separate full-precision auxiliary.csv
      rows with stable key, run ID, producer, specification, source route,
      scope, statistic, and value. README bindings include source version,
      inputs/representations, environment, execution log, model/sample/SE
      choices, and inspected evidence for comparator absence.

  - rule_section: "Child 1579 — Canonical scoring separation"
    evidence: >-
      assessment.md:476-478 excludes auxiliary rows from reproduce.csv,
      match/discrepancy counts, all comparison/score denominators, ACRe
      main-result criteria, and selected-target scoring. The auxiliary schema
      has no comparison status or original-value field.

  - rule_section: "Child 1579 — Missing comparators and actual failures"
    evidence: >-
      SKILL.md:252-256 and assessment.md:478-481 explicitly distinguish
      comparator absence from missing inputs or execution failure, while
      preserving actual failed/blocked attempts and reasons in run and
      coverage/disposition records. Blank auxiliary values are prohibited
      at assessment.md:474.

  - rule_section: "Parent 1575 standing rulings; child 1579 — Inventory and held decisions"
    evidence: >-
      assessment.md:483-489 preserves required inventory targets and unresolved
      comparisons, leaves qualitative/footnote inventory and comparator/tolerance
      questions undecided, and grants no new specification, translation
      eligibility, or unsigned robustness authority.

  - rule_section: "Child 1579 — Canonical schema, ACRe, tolerance, and signing preservation"
    evidence: >-
      Byte comparison confirmed unchanged canonical assessment, six-row,
      selected-target, manifest, and comparison-schema contracts.
      SKILL.md:238-251 retains printed-digit tolerance and main-result rules;
      SKILL.md:337-345 retains human signing and disposition requirements.
      rules.md:66-70 prevents a reproduced robustness baseline from becoming
      an invented printed comparator for reproduction scoring.

  - rule_section: "rules/workflow.md — Full logical propagation; child 1579 — Broad CSV/report/count wording"
    evidence: >-
      assessment.md:3-7 and :424 narrow scored-state/schema wording to
      comparison files. SKILL.md:73 distinguishes auxiliary storage;
      :238-244 adds retention; :381-387 separates report presentation;
      :436-439 restricts discrepancy counts. rules.md:49-51 and :66-70
      propagate the scoring and storage boundaries. Remaining out/*.csv
      references at SKILL.md:21-22 describe write locations, not aggregation.

  - rule_section: "Child 1579 — Validation boundary and scenario evidence"
    evidence: >-
      source-scenario-audit.md:10-16 covers produced unprinted values,
      broad aggregation, comparator absence, mixed success/failure, a printed
      comparator positive control, unresolved required targets, and held
      authority. This review independently checked source preservation;
      numerical execution and project hygiene checks were not run.

  - rule_section: "rules/lang/en.md — English conventions"
    evidence: >-
      Added headings use sentence case; technical CSV capitalization is
      appropriate. Added prose consistently uses forms such as 'identifier'
      and 'labelled' compatible with the surrounding documents, and uses
      serial commas in substantive lists, including assessment.md:468-469.

  - rule_section: "rules/prose/_all.md — LLMism guards; Elements of Style"
    evidence: >-
      The new contract uses concrete fields and operational requirements,
      separates provenance, exclusions, and authority into distinct paragraphs,
      and makes no empirical numerical claims. One positional cross-reference
      violates the explicit cross-reference rule, recorded below.

semantic_findings:
  - rule_section: "rules/prose/_all.md — Elements of Style: Cross-reference by label"
    concern: >-
      'The comparison-column schema above' uses a positional reference where
      the rule explicitly requires a labelled reference. The intended schema
      is identifiable, so this is a documentation nit, not a scoring defect.
    file: "skills/replicate/references/assessment.md"
    line: 454
    severity: nit
    suggested_test: >-
      Manually verify that a link to the 'Comparison CSVs' section resolves
      to the canonical comparison schema. No wording-matching test is needed.
```