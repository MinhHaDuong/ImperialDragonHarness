# Adherence verdict for 1577

Implementation head: `4e4a52ce9d381e0a07deab32c93208154c0670e5`.

```yaml
adherence: PASS
mechanical_runner: ran
mechanical_command: make lint
mechanical_declaration: Makefile:32
reference_resolution: skipped (no tex/qmd/bib changes)
semantic_review:
  applicable: true
  status: ran
  reason: skill instruction changes
  worker_id: 01a21c7d-58b5-7d31-b67a-b780b1a62aa7
  model: gpt-6.1-sol
  family: OpenAI
  effort: medium
  route: native headless Codex subscription, read-only, API-key variables removed
  launch_evidence: runtime header below
  completion_evidence: completed valid YAML report below
mechanical_failures: []
semantic_findings: []
escalation: null
```

`make lint`: passed after rebase. `make check-fast` and
`make check-skills-drift`: passed. The source/scenario audit is
[validation-exposure-1577.md](validation-exposure-1577.md). The historical mapping
table rows and canonical assessment/rules files were byte-compared against
base `1596cb9024aaed48e088b7b04121078c1f662c70`: identical.

A native subagent launch was refused by the thread limit. The distinct native
subscription process completed instead. The launcher observed this header;
its model identity does not rely on the reviewer's self-report. Same-family
review adds verification, with no cross-family independence claim.

```text
OpenAI Codex v0.172.0
--------
workdir: /home/haduong/.agents/.claude/worktrees/t1577-266508-7397
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a21c7d-58b5-7d31-b67a-b780b1a62aa7
--------
```

## Semantic report

```yaml
reviewed_rules:
  - rule_section: "Review scope and pinned revision"
    evidence: "Read the complete diff from 1596cb9024aaed48e088b7b04121078c1f662c70 to 4e4a52ce9d381e0a07deab32c93208154c0670e5. HEAD and t1577-validation-exposure both resolve to the requested head. Review used local reads only; no edits, mutations, scientific execution, API calls, or delegation."

  - rule_section: "AGENTS.md — Harness agent profiles; Agent profiles"
    evidence: "The added guidance names executors, helpers, and signers without prescribing models or capability tiers (skills/replicate/SKILL.md:87-102). No profile contracts or tool grants change."

  - rule_section: "AGENTS.md — Harness instructions; Project memory; Project memory boundary"
    evidence: "Read memory/MEMORY.md and memory/topics/skills-docs-and-hooks.md. The audit resides under design/replicate/validation-exposure-1577.md:1-36; the ticket references it at tickets/1577-replicate-separate-calibration-and-valid.erg:8. No memory or cross-project files change."

  - rule_section: "AGENTS.md — Skills catalog"
    evidence: "The diff leaves skill name, description, category, and order unchanged. No catalog regeneration trigger is introduced."

  - rule_section: "rules/guards.md — Guards"
    evidence: "All five changed files belong to the assigned harness repository. No credentials, external-project writes, memory promotion, or context-limit workaround appear in the diff. Replicator evidence is cited by path and commit rather than modified."

  - rule_section: "rules/git.md — Branch and commit"
    evidence: "The named branch contains one commit for the exposure/calibration change. Its message explains replacing the probe-only boundary with coverage across verbs. The five changed files form one documentation change; no main-branch mutation was performed in this review."

  - rule_section: "rules/git.md — Commands that destroy silently; Reading state you will act on"
    evidence: "Used read-only git diff, log, status, and rev-parse. Revision identity came from single-value rev-parse output. No stash, checkout, ref update, forge mutation, or local-main synchronization was attempted."

  - rule_section: "rules/git.md — Merging"
    evidence: "This is a pinned semantic review, not a merge or gate verdict. No rebase, merge, push, or cleanup was performed; prior execution of lifecycle procedures cannot be established from this diff."

  - rule_section: "rules/workflow.md — Posture; Trust, Verify, Monitor"
    evidence: "The audit distinguishes development evidence from independent validation and includes ordinary reproduction and eligible fresh-paper positive controls (design/replicate/validation-exposure-1577.md:23-27). The review checks those claims against the changed instructions without scientific reruns."

  - rule_section: "rules/workflow.md — Cycle; Session start; Worktree paths"
    evidence: "The review opened in Verify and confirmed the assigned worktree root. The implementation audit identifies its documentation-only scope at design/replicate/validation-exposure-1577.md:3. No worktree creation or writes were required."

  - rule_section: "rules/workflow.md — Sync before starting work; Check scope"
    evidence: "The requested comparison remains the supplied base/head pair. No fetch or other mutation was performed under the explicit read-only instruction. This report makes no claim that current main was synchronized or that a project gate passed."

  - rule_section: "rules/workflow.md — Escalation protocol; Diagnosis discipline"
    evidence: "Unknown exposure cannot support blind validation (skills/replicate/SKILL.md:93-94). Later freezes cannot retroactively establish prospective choices (skills/replicate/references/validation.md:17-24). Historical findings are separated from current estimator/scoring authority (skills/replicate/references/gavard-scotch-mapping.md:13-28)."

  - rule_section: "rules/workflow.md — Delegation; Cross-project work"
    evidence: "Helpers receive purpose, exposure, and exclusions before retrieval (skills/replicate/SKILL.md:92-93). Replicator sources remain references, with no receiver-project modifications. This review spawned no agents."

  - rule_section: "rules/workflow.md — Ticket discipline for multi-request work"
    evidence: "Ticket 1577 identifies parent 1575 and its sequential delivery boundary (tickets/1577-replicate-separate-calibration-and-valid.erg:14-17,41-44). The diff implements only accepted B1/B4 scope and neither closes the parent nor resolves its held methodology questions."

  - rule_section: "rules/workflow.md — Micro-turn discipline; Autonomous action"
    evidence: "Navigation and reads were batched. The change updates the shared contract, validation reference, and affected historical mapping together. No additional tickets, guards, wording tests, or unrelated implementation were introduced."

  - rule_section: "rules/authoring-skills.md — Role, capabilities, discoverability, and frontmatter"
    evidence: "New instructions describe capabilities and responsibilities without runtime tool names or model assignments (skills/replicate/SKILL.md:87-102). Quoted description and argument-hint frontmatter remain unchanged at skills/replicate/SKILL.md:5-8."

  - rule_section: "Referenced authoring guide — Skill naming and invocation"
    evidence: "No skill is added or renamed, no legacy command is introduced, and no new runtime-specific invocation syntax appears. The added shared reference is explicitly discoverable as references/validation.md at skills/replicate/SKILL.md:100 and :209."

  - rule_section: "Referenced authoring guide — Concurrency and splitting"
    evidence: "The new workflow establishes sequential dependencies: exposure check before retrieval, freeze before unused-target evaluation, and renewed freeze before reevaluation (skills/replicate/SKILL.md:87-93; skills/replicate/references/validation.md:10-22). One validation reference serves multiple verbs rather than duplicating their contracts."

  - rule_section: "Referenced authoring guide — Toolkit principles and measurement limits"
    evidence: "No automated helpers, dependencies, or batch API calls are added. Unknown exposure and retrospective choices are disclosed explicitly (skills/replicate/references/validation.md:21-24,35-36); the historical example grants no new translation or execution authority (:19-20)."

  - rule_section: "rules/lang/en.md — English"
    evidence: "Added headings use sentence case. New lists use serial commas, including skills/replicate/references/validation.md:14 and :31. Compound modifiers include answer-bearing, same-paper, fresh-paper, and held-out. No inconsistent spelling, decimal notation, or academic data agreement was introduced."

  - rule_section: "rules/prose/_all.md — LLMism guards"
    evidence: "The added prose states concrete retrieval boundaries, freeze contents, exclusions, and disclosure requirements (skills/replicate/references/validation.md:3-44). No prohibited stock opener, padded rhetorical list, hedging stack, or em-dash chain was introduced."

  - rule_section: "rules/prose/_all.md — Elements of Style"
    evidence: "Instructions use direct actions such as Record, Pass, Freeze, Exclude, and Preserve. Paragraphs separate calibration, evaluation, and fresh-paper eligibility. Internal cross-references use section titles; historical numerical findings remain unchanged, and new table identifiers describe sources rather than new empirical measurements."

  - rule_section: "tickets/AGENTS.md — Ticket format and append-only history"
    evidence: "The only ticket change appends a timestamped implementation log at tickets/1577-replicate-separate-calibration-and-valid.erg:8. Existing headers, ID, body, and history remain intact; the audit artifact lives in design/ rather than a ticket sidecar."

  - rule_section: "Ticket 1577 — Exposure and helper propagation"
    evidence: "The worked-example pointer now requires the exposure check before retrieval (skills/replicate/SKILL.md:31-34). The shared section records executor/helper/signer exposure and passes exclusions before helper retrieval (:87-102), covering all verbs."

  - rule_section: "Ticket 1577 — Calibration, unused targets, and fresh validation"
    evidence: "The reference freezes calibration targets, alternatives, choices, identifiers, and hashes before unused-target evaluation; it separates results and preserves post-hoc history (skills/replicate/references/validation.md:10-24). Fresh-paper selection and cohort eligibility are separate requirements (:28-44), including explicit Weschle/Atanasov exclusions."

  - rule_section: "Ticket 1577 — Ordinary reproduction and historical preservation"
    evidence: "Disclosed ordinary reproduction/appraisal remains permitted (skills/replicate/SKILL.md:97-99; skills/replicate/references/validation.md:42-44). The Gavard mapping gains exposed/calibrated and historical labels while retaining its dated numerical findings and case table (skills/replicate/references/gavard-scotch-mapping.md:11-49)."

  - rule_section: "Parent 1575 — Accepted scope and standing authority"
    evidence: "Assessment schema and binding rules files are unchanged. Existing half-unit tolerance, canonical/selected scope separation, person-written signature, and publication gates remain at skills/replicate/SKILL.md:104-118,223-233,316-318,397-407. Added preservation clauses at :101-102 and references/validation.md:23-24 leave held translation/scoring decisions unresolved."

  - rule_section: "Ticket 1577 — Source/scenario audit and validation boundary"
    evidence: "design/replicate/validation-exposure-1577.md:7-17 records pinned source references; :23-27 compares failure scenarios and positive controls; :31-36 records preserved boundaries. The complete diff contains documentation and one ticket log entry only. Hygiene-check execution and external source contents are not independently attested by this semantic review."

semantic_findings: []
```