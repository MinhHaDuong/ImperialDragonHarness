---
name: Orchestrator lessons — wave-1 execution
description: Process fixes from first orchestrator wave; worktree path, timestamps, MVP-critical classification
type: feedback
originSessionId: a1e1fc5e-956b-4f8a-bca4-4e2b976f870b
---
Always use `date -u +%Y-%m-%dT%H:%MZ` for ticket log entries — never hardcode a round hour like "17:00Z".
**Why:** Manual round-hour timestamps caused identical-file conflicts on every rebase in wave-1.
**How to apply:** Every ticket log line written by an agent must use the shell command for the real UTC time.

Trust the imagine phase's MVP-critical classification. Tickets flagged "nice to have" should be the first to drop when the user changes direction.
**Why:** Finite-time theory tickets (0001, 0002) were correctly abandoned at low cost because they were pre-flagged as non-critical.

Always do a scientific framing review before the first execute wave. Framing errors are cheapest to fix before any code exists.
**Why:** The "LLM is not ground truth / SWOT not ranking" correction saved multiple rework rounds.
