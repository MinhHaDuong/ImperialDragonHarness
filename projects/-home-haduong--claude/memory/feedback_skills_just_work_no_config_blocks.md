---
name: skills-just-work-no-config-blocks
description: Author directive — skills must Just Work in the launch directory; discovery over per-repo CONFIG blocks
metadata:
  type: feedback
---

Skills must Just Work (tm) in whatever project directory they are launched — no per-repo CONFIG block to hand-author before a run (directive 2026-06-06, while planning the 0219 raid).

**Why:** A hardcoded CONFIG block (the 0182 fang-audit shape: pairing table, RUN_TEST, canaries baked into the script) makes every new target repo a pre-authoring chore and rots as the repo evolves. The 0184 `test-quality.py` pattern is the precedent: pluggable runner/adapter, works in any repo, knobs are CLI flags with defaults.

**How to apply:** Derive repo specifics at run start — a discovery phase reads the launch repo (Makefile, pyproject.toml, go.mod, test tree) and builds the pairing table / test command / language heuristics. Discovery-by-reading is NOT the banned "name heuristic" (0182's `X_test→X.go` glob that broke on non-1:1 pairs); it is informed derivation, and explicit inputs remain as optional *overrides*, not prerequisites. When evolving a skill guarded by adherence tests that enforce the old explicit-CONFIG design (0182's test_config_block_declares_explicit_knobs etc.), revise those tests deliberately under this directive — do not treat them as immovable. Related: [[workflow-agents-session-bound]] — Just-Works only helps if the session is rooted in the target repo.
