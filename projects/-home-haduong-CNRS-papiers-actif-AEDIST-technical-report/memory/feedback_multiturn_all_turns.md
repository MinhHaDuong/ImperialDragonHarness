---
name: multiturn_all_turns
description: Multiturn extraction must join all assistant turns, not just the last one
type: feedback
---

When extracting tables from multiturn conversations, join all assistant turns. The last turn may be a short follow-up or truncated fragment; the best table is often in an earlier turn.

**Why:** The last assistant turn in multiturn/claude-opus-4.6-run1 was 457 chars of preamble with an unclosed CSV block. The complete 75-row table was in turn 1.

**How to apply:** Any code that reads multiturn JSON should join all assistant content before searching for tables or structured data. Exception: verify.py may intentionally use the last turn for per-turn verification — check context.
