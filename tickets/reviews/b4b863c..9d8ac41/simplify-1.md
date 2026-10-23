---
review-evidence: 1
kind: review
seat: simplify
verdict: approve
family: openai
worker: /root/gaze1633_simplify (runtime identity not observed by controller)
base: b4b863c676065cf81f28fc33657254a68112b104
head: 9d8ac41ef3607d1a14e2ae3c1c5a3150a2970383
patch-id: 636d7a10c09a511c4f0378f8ad8da238e7f628b6+8e48e454340dace13428be998873d4aeba7449c6
criteria-hash: dad170fcdd7e9573
policy-version: d22229237f55ca28
recorded: 2026-10-23T11:06:26Z
---

# Simplification review — PR 1633

Verdict: **CLEAN**

Reviewed HEAD: `9d8ac41ef3607d1a14e2ae3c1c5a3150a2970383` (matched the requested anchor before and after review). Base: `origin/main` at the review snapshot. Reviewer: Codex (`gpt-6-luna`, medium), native route; same OpenAI family as the primary reviewer. Route and identity were supplied by the launch prompt; no independent runtime attestation was available in this seat. Review was read-only; no tests were run.

I found no safe simplification that clearly reduces complexity while preserving the ticket intent. The 543-line `manuscript_review.py` is the main apparent target, but its separate preparation, native trace parsing, evidence validation, bounded redirect traversal, immutable resume, execution, and ledger export correspond to explicit engine requirements and observed trial failures. Splitting it into a framework or adding generic abstractions would add structure without removing a mechanism. The single CLI route and one reader followed by one bounded verifier are already constrained choices.

I considered extracting the repeated BibTeX declared-entry count guard from `scripts/bib-merge.py` and `scripts/validate-refs.py`. It is a short guard in two standalone commands, each declaring the same parser dependency; a shared module would add another runtime file/import for little reduction. Keeping the checks local is simpler at this scale.

Other tempting reductions were also retained: `scripts/keystore.py` is reused by the remaining probe after retiring its former owner; its explicit checks preserve the credential reader contract. `track_changes_pdf.py`'s pinned supplementary-input handling and `ingest_letter.py`'s round/disposition fields support specific failure cases and existing ledger reuse. The manuscript review's explicit source and redirect checks prevent unrelated retrievals or URL-only redirects from being treated as evidence. None is redundant with the neighboring mechanism it might appear to replace.

Examined groups and paths:

1. Engine extraction, launch/recovery/run: `skills/manuscript-review/manuscript_review.py`, `skills/manuscript-review/SKILL.md`, `skills/manuscript-review/references/reader-prompt.md`.
2. Engine finding/source/redirect validation: same engine and protocol, including `validate_stage`, `fetched_texts`, `durable_trace`, resume, and export paths.
3. Engine behavior tests: `tests/test_manuscript_review.py`.
4. Engine execution/recovery tests and sourced brief: `tests/test_manuscript_review.py`, `skills/manuscript-review/SKILL.md`, `references/reader-prompt.md`.
5. Bibliography merge: `scripts/bib-merge.py`, `tests/test_bib_merge.py`, `skills/conference-submission-prep/runbooks/bib-merge.md`.
6. Reference validation: `scripts/validate-refs.py`, `tests/test_validate_refs.py`, `skills/related-work-note/runbooks/validate.md`.
7. Revision ledger: `skills/ingest-decision-letter/ingest_letter.py`, `tests/test_ingest_decision_letter.py`, `skills/ingest-decision-letter/SKILL.md`.
8. PDF helper: `skills/track-changes-pdf/track_changes_pdf.py`, `tests/test_track_changes_pdf.py`, `skills/track-changes-pdf/SKILL.md`, `skills/pdf-finish/SKILL.md`.
9. Zotero/note/search contracts: `skills/zotero/references/{backfill,import}.md`, `skills/reading-note/SKILL.md`, `skills/reading-note/references/template.md`, `skills/related-work-note/SKILL.md`, `skills/biblio-saturation/SKILL.md`, `skills/critical-lit-review/SKILL.md`.
10. External/conference entry points and retired executor: `skills/external-peer-review/SKILL.md`, `skills/conference-submission-prep/SKILL.md`; inspected removed `peer_review.py`, `references/openrouter.md`, and `tests/test_external_peer_review_skill.py` at `origin/main`.
11. Retired reference/tests, guarded keystore/probe: `scripts/keystore.py`, `scripts/probe-memory-symlink.py`, `tests/test_keystore.py`, `tests/test_probe_memory_symlink.py` and their diffs.
12. Dependency declaration and lock: `pyproject.toml`, `uv.lock`, `tests/test_deps_declared.py`.
13. Audit narrative, probes, source reuse, retirement: `docs/audits/2026-10-23-skills-metier/{README.md,probes.py,evidence.json,execution.md,retirement-inventory.md,coarse-ink.md}`.
14. Named model reports and metadata: all Astra/Fable review and metadata files under `docs/audits/2026-10-23-skills-metier/reviews/` (read report identity/scope and outcome headers).
15. Trial/archive/handoff receipts: `train.json`, `trial-attempts.json`, `trial3-revalidation.json`, `trial-ledger-handoff.json`, `archive-receipt.json`.
16. Tickets and generated catalog: open tracker 1198, closed tickets 1199–1205 and `skills-catalog.md`.

Limits: this is a structural simplification review, not a correctness or scientific-quality verdict. I did not run tests, inspect external Zotero contents, or revalidate the manuscript trial; the recorded receipts were used only to understand design constraints. No actionable simplification finding.

## Controller provenance and disposition

Native seat /root/gaze1633_simplify completed; requested gpt-6-luna/medium, independent runtime attestation unavailable.