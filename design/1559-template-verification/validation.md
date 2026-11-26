# Ticket 1559 validation

Checked 2026-11-26 in the ticket worktree. The implementation was reused by
cherry-picking commit `6c6822dc786c3b7bd2b6919b960de6bad737a886`, preserving its
author and co-author. The follow-up clarifies applicability and adds verification
evidence. The previous locked worktree was left untouched.

## Provenance and assets

`zenodo.json` is generated from the three public Zenodo API records and local
file reads. All six files match both byte size and MD5. It records the titles,
versions, publication dates, creators, and CC-BY 4.0 licenses. Reading all three
LaTeX archives confirmed the index's section skeletons and four-file contents.
No external project was edited.

## Checks

- `git diff --check`: passed.
- `make lint`: 191 passed, 3725 deselected.
- `make check-fast`: 1955 passed; seven pre-existing deprecation warnings.
- The skill-creator `quick_validate.py` rejects the existing `argument-hint`,
  `disable-model-invocation`, and `user-invocable` frontmatter keys. Those
  repository extensions are unchanged; the harness frontmatter tests pass.
- Reference resolution: no changed `.tex`, `.qmd`, or `.bib` source files;
  the vendored archives are unmodified upstream assets.

The semantic reviewer was a separately launched collaboration worker
`/root/templates/adherence`, requested as `gpt-6-luna`, medium effort, OpenAI
family. The tool launch and completed report were observed; the underlying
runtime identity was not exposed. Its scenario checks were readings of the
instructions, not an end-to-end replication or report-generation run.
The report follows verbatim (its initial report-destination description refers
to the first brief; the completed artifact was read from `.panel/adherence-semantic.md`).

```yaml
reviewed_rules:
  - rule_section: "AGENTS.md — project memory boundary and assigned-project scope"
    evidence: "Reviewed diff is confined to the replicate skill, its references, vendored template files, and design verification evidence. No memory or other project was modified. Runtime identity observed: delegated reviewer /root/templates/adherence; underlying model/runtime identity and masked fields unavailable."
  - rule_section: "rules/guards.md — project files only; no credentials"
    evidence: "Read-only review; no project or forge mutation. Report destination is the authorized /tmp/t1559-semantic.md. No credentials displayed."
  - rule_section: "rules/git.md — read-only branch discipline and non-destructive inspection"
    evidence: "Confirmed worktree root and inspected git diff/status only. No branch, index, commit, or forge mutations."
  - rule_section: "rules/workflow.md — trust, verify, diagnosis discipline"
    evidence: "Semantic review cites concrete skill/index lines and the checked Zenodo metadata/checksum manifest. No tests or broad survey were run, as instructed."
  - rule_section: "rules/authoring-skills.md and skills/harness-doctor/references/authoring-skills.md — authoring constraints"
    evidence: "The changed skill names no model, capability tier, or runtime-specific tool; the new routing instructions are in the skill body, with template-specific material in a referenced index. No frontmatter changed."
  - rule_section: "replicate report-template routing and fallback"
    evidence: "skills/replicate/SKILL.md:172-192 selects from the index using assignment, work type, field, and journal; explains uncertainty; specifies manifest provenance; and requires person confirmation before writing an adapted report. rules.md fallback is explicitly retained at lines 183-184. Generic psychology does not imply Phase 2 membership (line 178). Scenario outcomes: ordinary economics reproduction → General, record 23226406, version 1, reason: economics reproduction with no named/specific template; Psychological Science Phase 2 reproduction → Psychological Science Phase 2, record 23214112, version 1, reason: I4R project membership; forensic commentary on a psychology paper → Commentary from Forensic Report, record 23597737, version 1, reason: forensic commentary on specific problems; explicit I4R General assignment for Phase 2 → General, record 23226406, version 1, reason: assignment explicitly names General; qualitative field study requiring ethnographic evidence not covered by the templates → propose adapted structure in report/structure.md from closest template (General), identify changed sections, record General with adapted:true, and wait for a person's confirmation before writing. INDEX.md records template names, records, versions, use cases, skeletons, checksums and CC-BY attribution (lines 3-13, 17-33). design/1559-template-verification/zenodo.json records all three record metadata and matching checksums."
semantic_findings: []
```
