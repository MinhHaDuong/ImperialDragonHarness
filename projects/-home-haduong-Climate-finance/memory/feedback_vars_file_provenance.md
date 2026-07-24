---
name: Check compute_vars.py before touching metadata-files
description: Stale vars files can exist on disk; always verify which file the pipeline actually generates
type: feedback
originSessionId: ffb7544c-0aee-4a39-b094-7dcb6ec24e41
---
When a `.qmd` frontmatter has `metadata-files: [X-vars.yml]`, verify X against `scripts/compute_vars.py` DOC_VARS keys and the Makefile render dependencies before changing it.

**Why:** PR #737 renamed `companion-paper` → `multilayer-detection`. A stale `companion-paper-vars.yml` remained on disk, making it look like a valid alternative. A session summary incorrectly recommended switching to it. The PR #756 `/verify` pass caught the regression.

**How to apply:** Before editing `metadata-files`, run `grep '"<stem>"' scripts/compute_vars.py` and `grep '<stem>-vars.yml' Makefile`. The file in frontmatter must match.
