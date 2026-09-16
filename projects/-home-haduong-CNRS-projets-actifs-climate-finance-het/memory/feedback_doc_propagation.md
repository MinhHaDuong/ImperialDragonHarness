---
name: Doc propagation is mandatory
description: Always run doc propagation agent when reviewing PRs that touch scripts/ or pipeline logic
type: feedback
---

PRs that change pipeline behavior must update downstream docs in the same PR or explicitly defer with justification. The doc propagation review agent is mandatory, not optional.

**Why:** PRs #278 and #281 merged without updating stale references in `content/_includes/corpus-construction.md` and `content/data-paper.qmd` (hardcoded counts like "15 institutions", "~130 courses", "manual catalog of readings from 15 specific syllabi"). The user caught this during review of #281.

**How to apply:** When reviewing any PR that touches `scripts/`, always launch a doc propagation agent. Check `content/`, `docs/`, `README.md`, `STATE.md` for stale references to changed behavior. Request changes if docs would mislead a reader.
