---
name: DOIfetch sync procedure
description: How to sync PDFs and missing references between the project and the external DOIfetch tool
type: project
---

The DOIfetch tool lives **outside the repo** at `/home/haduong/CNRS/code/DOIfetch/` (never checked in).

**Sync procedure (run whenever bib or articles change):**

1. **Copy new PDFs** from DOIfetch output into the project:
   ```bash
   # Find new files not yet in docs/articles/
   comm -23 <(ls /home/haduong/CNRS/code/DOIfetch/papers/ | sort) \
            <(ls "docs/articles/" | sort)
   # Then copy the missing ones
   cp "/home/haduong/CNRS/code/DOIfetch/papers/<file>.pdf" docs/articles/
   ```

2. **Regenerate missing references list:**
   ```bash
   uv run python scripts/gen_missing_references.py
   # Writes docs/missing_references.txt
   ```

3. **Push missing references back to DOIfetch:**
   ```bash
   cp docs/missing_references.txt /home/haduong/CNRS/code/DOIfetch/references/missing_references.txt
   ```

**Why:** DOIfetch is an external tool (out of repo) that fetches PDFs by DOI/ISBN/URL. It reads `references/missing_references.txt` as its input queue and writes fetched PDFs to `papers/`. The project's `gen_missing_references.py` script generates that input from `content/bibliography/main.bib` vs `docs/articles/`.
