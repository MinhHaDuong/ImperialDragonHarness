---
name: feedback_import_is_a_merge_not_a_copy
description: "Bringing outside skills into the harness is a merge: audit overlap with existing skills and rules, then fold, retire or rewrite; a gate-passing copy is a dump"
metadata:
  type: feedback
---

On 2026-10-01 eight claude.ai-uploaded skills were copied into `skills/` (PR #1075) and only edited until the gates passed. The author: "it looked like a dump, not like a careful merge". The redo (tracker 0992, PRs #1077-#1083) started from a read-only overlap audit against existing skills and `rules/`, which found duplicated procedures (reading-note's RDF export vs zotero-import), doctrine restated from `rules/doctype/slides.md`, a venue skill missing the author's diamond-OA filter, an out-of-field skill, and four trigger collisions. Outcome: two skills retired, two merged, four rewritten, one new rule; 3,800 lines became under 700.

**Why:** a gate checks form, not fit. Passing lint says nothing about whether a body duplicates, contradicts or out-sizes what the harness already has.

**How to apply:** any import (claude.ai uploads, another repo's skills, a pillaged technique) starts with an overlap audit and a per-item verdict (keep-rewrite / fold-into / split / retire), the author's calls batched into one question round, one child ticket per verdict, and a cross-PR review by a different model before merging. Related: [[feedback_local_evidence_gate_for_pillaged_techniques]], [[feedback_verify_sibling_prs_jointly]].
