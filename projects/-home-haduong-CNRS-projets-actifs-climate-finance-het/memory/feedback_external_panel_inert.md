---
name: feedback_external_panel_inert
description: "Reviewer preference and safe project-specific panel setup; inspect seat status and verify findings"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 69fadc0c-d582-4ce1-adea-c507e9c40443
  modified: 2026-09-14
---

Use DeepSeek V4 through OpenRouter for the external reviewer and Terra as a local/session reviewer; exclude Luna (user preference, 2026-09-14; stable until contradicted). Copilot credits were unavailable in this session: this is temporary, not a permanent prohibition. Recheck that availability after 2026-09-28.

For this project, use a temporary roster with `credential-env: OPENROUTER_API_KEY`, the alias selected by the project's default-deny `KEYS=` configuration. Set `REVIEWERS_REPO` to the target project worktree; `REPO_ROOT` does not configure the reviewer runner. Disable fallback to the sibling project's IDH credential. Never source the entire provider credential file, and do not alter shared credentials or the shared roster for a project-specific run.

The historical July 2026 panel failure was caused by a roster naming the unselected IDH credential and by the runner resolving its own harness repository. The old claim that harvest silently reports success when no seat ran is stale: current harvest reports seat status. Read that status and distinguish successful review from preflight failure; an unavailable seat is not a clean review.

Calibrate reviewer findings against the actual reviewed tree. During PR #1365, DeepSeek's review at `da77` ran but its two findings were false positives. The final `73f` review failed preflight on reasoning-parameter incompatibility and supplied no successful final external review. Terra found the real frozen-baseline overwrite bug and reviewed its fix. These observations do not establish permanent model quality rankings. Recheck runner/model compatibility before reuse; compatibility observation expires 2026-09-28.
