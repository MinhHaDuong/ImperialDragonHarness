---
name: project_oeconomia_rr_pipeline
description: "Oeconomia R&R (major) revision plan — version ladder, tracking tickets, status as of 2026-06-18"
metadata: 
  node_type: memory
  type: project
  originSessionId: d9527d89-290e-4640-95bd-64bb3ccc5fa8
---

Œconomia returned **Reject-in-current-form / Revise & Resubmit (major)** on
2026-05-24 (editor Delcey + R1 + R2). Decision PDF in `rewrite for Economia/`.
Three drumbeats: AI-sounding prose (define-by-negation, empty closers — editor's
priority), "economists" under-specified (Table 2 has no econ journals), quant
unjustified/unframed. All ~60 remarks triaged into tracker **0133** + children
0134–0143 (audit-verified complete).

**Version ladder** (gated by version-tracker tickets; closing a tracker unlocks
the next via Blocked-by):
- v2.0.1 ✅ Vannes Charles Gide communication — de-anon + render; uploaded. Branch `vannes-v2.0.1`.
- v2.0.2 light fixes — 0140 safe subset (DAC/GNI/GEF acronyms done, PR #796).
- v2.0.3 prose ratchet — tracker **0154** (0147 harness, 0148 brief+polarity, 0149 initialize+triage). Build BEFORE content.
- v2.0.4 decisions — tracker **0155** (0142 structure, 0150 economists framing, 0151 indeterminacy thesis; needs-human, I draft options).
- v2.0.5 implementation — tracker **0156** (0134–0143 content, 0152 response letter, 0153 resubmit+Zenodo/HAL deposit).

Pipeline restructuring: PR #800 (branch `t0133-revision-pipeline`). Plan file:
`~/.claude/plans/swift-dancing-conway.md`.

Vannes is a separate track: full conference paper (the same manuscript, de-anon,
French presentation header) — see [[project_gide_conference.md]]. Resubmission uses
the submission-branch Revision lifecycle + `release/revision-runbook.md` §4 response
template. See [[feedback_version_increment_planning]].
