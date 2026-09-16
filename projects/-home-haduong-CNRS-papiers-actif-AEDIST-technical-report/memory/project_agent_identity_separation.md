---
name: project-agent-identity-separation
description: "Post-conference task — give Copilot/HDMX-coding-agent a non-admin GitHub identity so `enforce_admins: true` actually protects against agent red-merges."
metadata: 
  node_type: memory
  type: project
  originSessionId: aacff427-fd62-410d-9b06-5e233b752256
---

Create a fine-grained PAT (or deploy key, or GitHub App) scoped to `MinhHaDuong/aedist-technical-report` only, with write-but-not-admin permissions. Configure Copilot in VSCode and the `HDMX-coding-agent` commit identity to authenticate with this token. Then classic branch protection with `enforce_admins: true` becomes meaningful: you (admin via MinhHaDuong) bypass; agents (write-only) are gated by CI.

**Why:** Morning 2026-05-23 incident exposed that the repo has exactly one GitHub collaborator: `MinhHaDuong` (admin). The `HDMX-coding-agent` name is a git-author *string* in commit objects, not a separate account — it pushes via MinhHaDuong's admin token. Same for Claude Code's `gh` CLI and Copilot in VSCode. So `enforce_admins: false` re-opens the morning's leak (Copilot auto-merged 3 red PRs). Without identity separation, the admin-bypass toggle is binary and useless: protection applies to everyone or no one.

**How to apply:** Deferred until after Econom'IA 2026 (2026-05-27). Until then, classic protection with `enforce_admins: true` is the working compromise — gate everything, accept the ticket-housekeeping PR overhead (see [[project-ci-chore-bypass-workflow]] for the complementary ergonomic fix). When implementing: prefer a fine-grained PAT first (lowest setup cost); upgrade to GitHub App only if multiple agents need different scopes.
