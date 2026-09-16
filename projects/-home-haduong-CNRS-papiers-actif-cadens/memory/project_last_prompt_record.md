---
name: last-prompt JSONL record type
description: Claude Code JSONL files contain type:last-prompt records that store raw slash invocations — not documented in harvester code
type: project
originSessionId: caf5fc44-2576-40d1-ae30-62303fa6a0b3
---
The local JSONL corpus (`~/.claude/projects/**/*.jsonl`) contains `type: last-prompt` records with structure:
```json
{"type": "last-prompt", "lastPrompt": "/skill-name args...", "sessionId": "..."}
```

These records capture slash invocations intercepted client-side before they reach the user message. They have **no timestamp** — use the last-seen timestamp from the same session as proxy.

The `ClaudeLocalSource` harvester skips these records intentionally (it only needs turn-level metrics). The `slash_extract.py` module reads them directly from JSONL files.

**Why:** Discovered during ticket 0022 implementation. Slash invocations in `type: user` message content yield zero hits on the live corpus.

**How to apply:** Any future analysis of prompt text, command usage, or session intent should walk `last-prompt` records, not user message content.
