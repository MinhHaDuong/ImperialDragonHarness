---
name: Technical report rewrite plan
description: Structural decisions for technical-report.qmd rewrite — reproducibility note framing
type: project
---

Rewrite technical-report.qmd with these decisions:

1. **Framing**: Title/abstract reframed as "reproducibility note" — companion to scripts, data, and config files.
2. **Two-part structure**: Part I = Corpus construction, Part II = Analysis.
3. **Core vs. Full** distinction must appear early (not buried mid-document).
4. **Variable geometry**: a flag/profile to include only sections describing figures, tables, or assertions actually used in the manuscript. Complete version includes ALL figures and ALL tables.
5. **Concrete numbers**: Don't say "the QA script reports X" — provide the actual numbers.
6. **No repetition**: Repro section currently repeats corpus building — deduplicate.

**Why:** Tech report is the reproducibility artifact for reviewers and future users. Must be self-contained, precise, and well-structured.

**How to apply:** When editing technical-report.qmd, check each section against these 6 criteria. The variable geometry flag could use Quarto conditional includes or a Quarto profile.
