---
name: verify-artifacts-after-python-fix
description: "After fixing Python plotting code, always rebuild and verify the output PDFs before committing — stale pre-fix PDFs in the working tree look modified but are wrong"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 98c497f0-7c8d-4069-ae74-bb341ac4bdf5
---

When a Python fix is applied to a script that generates PDFs, the PDFs already present in the working tree may be the *regressed* versions (built with the broken code before your fix). They show as `M` in `git status` but are incorrect.

**Why:** In the 2026-05-27 post-conference review session, `slides/conference-day-final` merge had regressed `plot_exp2_arms_split.py`. The Python fix was applied and the pre-fix PDFs were committed together. The PDFs actually *shrank* (more content removed → smaller file), which is the wrong direction. A full rebuild was needed in a follow-up commit.

**How to apply:** After editing a Python plot script, always run the relevant make target or `uv run python -m aedist.plot_...` to regenerate artifacts *before* staging them. Check that PDF file size changed in the expected direction (more visual content → larger file). Don't commit PDFs from the working tree that were modified before your Python fix.
