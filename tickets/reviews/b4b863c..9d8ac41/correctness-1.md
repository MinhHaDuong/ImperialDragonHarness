---
review-evidence: 1
kind: review
seat: correctness
verdict: approve
family: openai
worker: 01a16864-955e-7dc3-a224-92ba62a3de55
base: b4b863c676065cf81f28fc33657254a68112b104
head: 9d8ac41ef3607d1a14e2ae3c1c5a3150a2970383
patch-id: 636d7a10c09a511c4f0378f8ad8da238e7f628b6+8e48e454340dace13428be998873d4aeba7449c6
criteria-hash: dad170fcdd7e9573
policy-version: d22229237f55ca28
recorded: 2026-10-23T11:06:26Z
---

# Correctness review — PR 1633

**Perspective:** Correctness. **Anchor:** `9d8ac41ef3607d1a14e2ae3c1c5a3150a2970383` (matched before review and immediately before report write). **Base:** `origin/main`. **Route:** Luna / medium requested by the orchestration brief; concrete runtime model identity is unavailable in this seat's exposed evidence, so no model identity is asserted. Same-family review only; no cross-family independence claim.

## Finding

- **Low confidence, non-blocking — `consider:`** The reader and verifier can satisfy localized manuscript evidence with any non-empty passage attached to a real page. `validate_evidence()` checks only `(document, page)` membership and that `passage` is non-empty (`skills/manuscript-review/manuscript_review.py:125-132`); both review and verification rely on that check at lines 230 and 258. A fabricated or unrelated quote can therefore be emitted into a run that passes the evidence-shape check. This does not establish a scientific error, and the documented limitation says the runner checks execution rather than truth, but the persisted `evidence` field can look stronger than its mechanical validation. A small follow-up could compare text-layer quotations against the pinned page text and label figure descriptions as model-reported visual evidence. The present contract may reasonably leave this judgment to the reader/verifier.

No blocking correctness defect found in the reviewed implementation. The tool-backed reader, bounded source pass, strict source retrieval receipts, redirect handling, immutable failed-attempt recovery, round-scoped ledger integration, and migration away from the old executor agree with the stated criteria. The actual public trial and its recorded archive receipts are present; they establish execution and storage, not scientific truth or improvement.

## Review coverage

Read all 16 groups listed in `.panel/1633/groups.md`, including base versions of removed files: engine and prompt; engine tests; bibliography merge and reference validator; revision ledger; PDF helper; Zotero and note/search contracts; retired executor and tests; keystore/probe; dependency declaration and lock; audit narrative and probes; named review records; trial and archive receipts; all seven child tickets and tracker; generated catalog. Cross-checked changed callers and the retirement inventory. The tree remained at the anchor.

## Verification

Ran the focused touched behavior suites:

```text
/home/haduong/.agents/.venv/bin/python -m pytest -q \
  tests/test_manuscript_review.py tests/test_ingest_decision_letter.py \
  tests/test_bib_merge.py tests/test_validate_refs.py \
  tests/test_track_changes_pdf.py tests/test_keystore.py
173 passed, 1 skipped in 5.81s
```

`git diff --check origin/main...HEAD` passed. No live model, credential, Zotero API, or scientific-truth probe was run in this seat. The trial evidence was read as recorded artifacts; the archived Zotero payload was not independently fetched.

**Verdict: concerns.**

## Controller provenance and disposition

{"role": "/root/gaze1633_correctness", "session_id": "01a16864-955e-7dc3-a224-92ba62a3de55", "model": "gpt-6-luna", "effort": "medium", "evidence_type": "session_meta.agent_path + latest turn_context"}
The raw concerns verdict above is preserved. Its sole low-confidence `consider:` is informational, with no required change. Structural evidence checks do not certify scientific truth; visual descriptions cannot universally be matched to text-layer quotations. The controller retains the documented reader/verifier responsibility. The machine verdict approve means no required revision, not absence of this consideration.

### Adherence evidence

adherence: PASS
escalation: null
semantic_review:
  applicable: true
  status: ran
  reason: Architectural concerns remain across the changed research and publication
    workflow; semantic review handed to caller per semantic=caller.; semantic worker
    launched by the caller completed
  rule_sources:
  - AGENTS.md
  - rules/guards.md
  - rules/workflow.md
  - rules/authoring-skills.md
  - rules/coding-python.md
  - rules/coding-bash.md
  - rules/zotero.md
  - rules/manuscript-build.md
  - rules/prose/_all.md
  - rules/prose/workpackages.md
  worker_id: 01a16865-f0ef-7922-b6ca-01cf6babdac7
  model: gpt-6-luna
  family: OpenAI
  effort: medium
  route: native codex gpt-6-luna/medium
  launch_evidence: collaboration.spawn_agent /root/gaze1633_semantic; session_meta
    + latest turn_context
  completion_evidence: /home/haduong/.agents/.claude/worktrees/review-1633/.panel/1633/adherence-semantic.md
mechanical_failures: []
semantic_findings: []
untested_rules: []
