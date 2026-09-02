---
name: stay-on-max-plan-billing
description: "Claude instances on the author's machines run on his Max subscription (OAuth login), never on the API key in ~/.config/keys/anthropic.env, unless he says otherwise"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 10ff81b6-272d-48c9-ad4c-0fbd7153aec2
  modified: 2026-09-01T09:21:55.135Z
---

Provisioning a Claude Code instance on padme (2026-09-01), its OAuth session was
expired and `~/.config/keys/anthropic.env` was available; the plan drifted toward
launching on the API key. The author intervened: "we stay on the Max plan right?"

**Why:** subscription and API are different budgets; a long autonomous campaign on the
API key is real money he did not decide to spend. The key in `~/.config/keys/` exists
for scripted API calls, not as a fallback identity for Claude Code.

**How to apply:** when a machine's Claude auth is expired, ask him for one interactive
`claude login` there rather than substituting the API key — and do not copy
`~/.claude/.credentials.json` between machines: refresh-token rotation can break the
session the copy came from.
