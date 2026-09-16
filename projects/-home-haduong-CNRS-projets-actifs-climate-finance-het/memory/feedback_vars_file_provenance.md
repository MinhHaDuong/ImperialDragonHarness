---
name: Check the vars registry before touching metadata-files
description: Stale vars files can exist on disk; always verify which file the pipeline actually generates
type: feedback
originSessionId: ffb7544c-0aee-4a39-b094-7dcb6ec24e41
modified: 2026-07-28T21:00:23.918Z
---
When a `.qmd` frontmatter has `metadata-files: [X-vars.yml]`, verify X against the `DOC_VARS`/`DOC_VARS_FILE` keys and the Makefile render dependencies before changing it.

**Why:** PR #737 renamed `companion-paper` → `multilayer-detection`. A stale `companion-paper-vars.yml` remained on disk, making it look like a valid alternative. A session summary incorrectly recommended switching to it. The PR #756 `/verify` pass caught the regression.

**How to apply:** Before editing `metadata-files`, run `grep '"<stem>"' scripts/analysis/_vars_registry.py` and `grep '<stem>-vars.yml' Makefile`. The file in frontmatter must match.

**Update 2026-07-28:** ticket 0357 (PR referenced in [[feedback_split_contract_needs_parity]]) split the registry out of `compute_vars.py` into `scripts/analysis/_vars_registry.py` — `DOC_VARS` and `DOC_VARS_FILE` are defined there and merely imported into `compute_vars.py` (`from _vars_registry import DOC_VARS, DOC_VARS_FILE`). Grepping `compute_vars.py` for a stem literal no longer finds it; grep the registry file instead. Also assert parity between the two dicts per [[feedback_split_contract_needs_parity]] — a document declared in one but not the other fails silently in one direction.
