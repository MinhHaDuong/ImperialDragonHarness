---
name: feedback_arch_not_linecount
description: God module splits must improve architecture, not just pass line-count tests
type: feedback
---

When splitting god modules, the goal is readability and modularity — not getting to 799 lines.

**Why:** First attempt at splitting utils.py/collect_syllabi.py/compare_clustering.py just extracted random functions to pass the 800L wall. User rejected all three. Second attempt with proper architectural specs (seams by concern, domain-oriented naming, all modules under 500L smell threshold) produced quality code.

**How to apply:** When splitting a file, first identify the real seams (different reasons to change). Name modules by domain (pipeline_io, syllabi_harvest), not by parent (utils_pool). Target the 500L smell threshold, not the 800L wall. Give parallel agents detailed specs with module names, content lists, and line targets.
