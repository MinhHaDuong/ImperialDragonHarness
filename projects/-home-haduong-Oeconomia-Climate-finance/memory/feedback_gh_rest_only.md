---
name: GitHub agent token is REST-only
description: Agent token (fine-grained PAT) has no GraphQL access — always use REST API
type: feedback
---

Always use GitHub REST API, never GraphQL, for the agent token (`AGENT_GH_TOKEN`).

**Why:** The token is a fine-grained PAT, which gets 0 GraphQL rate limit. GraphQL calls silently fail or error out.

**How to apply:** Use `gh api /repos/...` REST endpoints instead of GraphQL queries. For `gh` CLI commands, most default to REST already — but watch for operations like Projects v2 that try GraphQL under the hood.
