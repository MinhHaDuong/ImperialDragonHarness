---
name: feedback_external_panel_inert
description: "Reviewer preference and safe project-specific panel setup; inspect seat status and verify findings"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 69fadc0c-d582-4ce1-adea-c507e9c40443
  modified: 2026-10-01
---

Use DeepSeek V4 through OpenRouter for the external reviewer and Terra as a local/session reviewer; exclude Luna (user preference, 2026-09-14; stable until contradicted).

For this project, use a temporary roster with `credential-env: OPENROUTER_API_KEY`, the alias selected by the project's default-deny `KEYS=` configuration. Set `REVIEWERS_REPO` to the target project worktree: without it reviewers.sh reviews the harness repo, and `REPO_ROOT` does nothing. Disable fallback to the sibling project's IDH credential. Never source the entire provider credential file, and do not alter shared credentials or the shared roster for a project-specific run.

Harvest reports seat status: read it, and distinguish a successful review from a preflight failure. An unavailable seat is not a clean review; before trusting an empty harvest, confirm a seat ran (findings file present, .err absent).

Calibrate reviewer findings against the actual reviewed tree, and recheck runner/model compatibility before reuse. On PR #1365 DeepSeek's two findings were false positives and Terra found the real bug; one PR does not rank models.
