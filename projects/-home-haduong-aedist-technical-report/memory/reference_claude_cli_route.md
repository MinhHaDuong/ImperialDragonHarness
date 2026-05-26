---
name: claude-cli-route
description: "The claude-code-cli route (ticket 0160, PR"
metadata: 
  node_type: memory
  type: reference
  originSessionId: de20a516-38a3-4ccc-b4a4-236f555d39aa
---

Added in ticket 0160 / PR #395 (2026-05-21).

**When to suggest it:**
- A sweep would consume ANTHROPIC_API_KEY budget that the user prefers to bill
  via their existing Claude Code subscription.
- A capability check / smoke test where T=0 reproducibility is not required.
- The user wants to compare a Claude model alongside other models without
  setting up a separate API key.

**How it works:**
- Subprocess wrapper: `claude --print --bare --output-format json
  --allowedTools "" --no-session-persistence --model <id>` with the prompt on
  stdin (and `--append-system-prompt` for system messages).
- Bills against `result["cost_usd"]` from the CLI's JSON, not
  `compute_cost(usage, model)`.
- Registry entries: `claude-sonnet-4-6-cli`, `claude-opus-4-7-cli` in
  `experiments/models.yaml`. Add more via the same template.
- Example sweep config: `[sweeps.sweep_smoke_claude_cli]` in
  `experiments/experiments.toml`.

**Limitations:**
- No temperature / seed / max_tokens control — CLI defaults only.
- Single-turn only (no multi-turn / conversation history).
- `reasoning_tokens` not surfaced separately by the CLI's JSON.
- Therefore NOT suitable for controlled sweeps (Exp 1 baseline-style work
  needs T=0 reproducibility, MoE rep budget enforcement, etc.) — only
  for capability checks and ad-hoc probes.

Discoverable via the "Model routes" table in `README.md` and the
example sweep in `experiments.toml`.
