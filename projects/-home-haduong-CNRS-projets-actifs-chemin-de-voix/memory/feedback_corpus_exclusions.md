---
name: Corpus exclusions — third-party content principle
description: docs/ contrib/ and similar dirs hold third-party content; exclusions live in scripts/exclude-paths.conf
type: feedback
originSessionId: f58b9bc8-e325-49d0-8494-e53e72422e60
---
Add path fragments to `scripts/exclude-paths.conf` (one per line, comments with #).

**Why:** Directories like `/docs/`, `/contrib/`, `/Documentation/`, `/coursebooks/` etc. typically contain third-party content (conference programmes, course readings, external references) — not the author's own prose. Pattern matching is case-sensitive substring on the full source path; iterative 50-file sampling validates each new pattern is AUTEUR-safe.

**How to apply:** Edit `scripts/exclude-paths.conf`, then `uv run python scripts/decontaminate_corpus.py --execute` to remove the corresponding corpus files. The walk cache auto-invalidates via _CONFIG_FP. Watch for case-sensitivity gotchas (e.g. `/attic/` vs `/Attic/`, `.pdf` vs `.PDF` — both forms must be added if both occur).
