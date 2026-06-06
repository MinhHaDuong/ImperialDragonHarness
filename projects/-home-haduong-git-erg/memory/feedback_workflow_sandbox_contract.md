---
name: workflow-sandbox-contract
description: "Workflow-tool scripts — no process global, args may arrive as a JSON string, schemas must tolerate stringified numbers, decorative agents must degrade not die"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff83e53f-129c-436d-b421-d6c97d72674d
---

Three Workflow-tool runtime traps hit on 2026-06-05 running fang-audit (cost: one dead 1.36M-token run, recovered via resumeFromRunId):

1. **No Node `process` global** — `process.env.HOME` in a workflow script dies at parse-time. Pass HOME (or pre-expanded absolute paths) via `args`.
2. **`args` may arrive as a JSON-encoded string** even when passed as an object in the tool call — a `typeof args === 'object'` guard silently drops the whole config. Scripts must `JSON.parse` string args.
3. **The tool layer can serialize integers as strings** (`"5"` not `5`), so `{type:'integer'}` schema values force StructuredOutput rejection loops until the engine throws. Use `type: ['integer','string']` + `parseInt` script-side.

**Why:** an uncaught `agent()` throw anywhere outside `pipeline()`/`parallel()` kills the entire run — fang-audit died at its decorative churn agent with all 27 audit agents already complete.

**How to apply:** wrap decorative/terminal `agent()` calls in try/catch and degrade (churn→0, guard→null/SUSPECT). On failure, recover with `resumeFromRunId` — but keep CONFIG byte-identical to the failed run (cache keys are per-call (prompt, opts)); fixing a config value before resume invalidates every cached prompt that embeds it. Fixes are in [[fang-audit skill]] PR ImperialDragonHarness#309, ticket 0223.
