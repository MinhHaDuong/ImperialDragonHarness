---
paths:
  - "**/SKILL.md"
  - "**/skills/**/*.md"
last-reviewed: 2026-10-27
---
# Writing skills — stub

Full guide, with the reasons: `skills/harness-doctor/references/authoring-skills.md`. Enforced here:
- The route skill decides the worker: a skill names a role and a need, never a model (`tests/test_skill_frontmatter.py`).
- Name capabilities, not tools; a runtime-specific line goes behind `<!-- harness-extension-point -->` (`scripts/check-agnostic.sh`).
- Discoverability first in `description:`, and free-text frontmatter is quoted (`tests/test_skill_descriptions.py`, `tests/test_skill_frontmatter.py`).
- Also in the full guide, unenforced: declared concurrency, split by exclusivity, no name the runtime binds, skill not command, test one before blasting.
