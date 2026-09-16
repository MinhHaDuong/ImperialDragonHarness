---
name: Table-as-contract for M/V splits
description: When splitting analyze+plot scripts, use CSV tables as the contract — no Python import coupling
type: feedback
---

When splitting a script that mixes analysis and visualization, use the output table (CSV) as the contract between the analysis script and the plot scripts. Do not create Python import coupling between them.

**Why:** The user challenged whether the model function and the table were redundant — they were. Positions and all renderer inputs can be reconstructed from the table + existing Phase 2 contract files. Import coupling would violate the 1-fig-1-script rule and create hidden dependencies.

**How to apply:** For M/V splits, the analyze_ script writes a table with all computed columns (including layout positions if applicable). Plot scripts read the table + any Phase 2 contract files they need. Each script is independently runnable via its Makefile target.
