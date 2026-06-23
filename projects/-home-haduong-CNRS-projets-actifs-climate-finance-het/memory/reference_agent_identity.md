---
name: Agent GitHub identity
description: HDMX-coding-agent is a git-author alias only, not a separate GitHub account — all reviews and PRs appear under MinhHaDuong
type: reference
originSessionId: fdd2a4d5-0a79-4d3d-82ab-23e76c7bc5ba
---
`HDMX-coding-agent` is a git-commit author name (configured via `AGENT_GIT_NAME`/`AGENT_GIT_EMAIL` in `.env`), not a real GitHub account. Both `GH_TOKEN` and `AGENT_GH_TOKEN` authenticate as the personal account `MinhHaDuong`.

**How to apply:**
- All PRs, reviews, and merges on `MinhHaDuong/Oeconomia-Climate-finance` appear as `MinhHaDuong` regardless of which token is used.
- GitHub blocks self-approval → use `gh pr review --comment` (not `--approve`) to satisfy the merge-gate hook at `.claude/hooks/check-reviews.sh`.
- As of PR #722 (2026-04-21), the hook's reviewer allowlist is `{HDMX-coding-agent, MinhHaDuong}`; the `HDMX-coding-agent` entry is dead weight kept for documentation of intent.
- If a separate agent account is ever provisioned, update the hook allowlist and this memory together.
