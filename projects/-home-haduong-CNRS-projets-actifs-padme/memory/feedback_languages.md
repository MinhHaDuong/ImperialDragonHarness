---
name: language preferences per domain
description: bash for system scripts, python for LLM/API integration, rust for high-frequency infra
type: feedback
originSessionId: 373c4915-d420-4c58-8931-74f68c620ede
---
Use bash for mechanistic system scripts (monitoring, backups). Use python for LLM integration (JSON encoding of arbitrary text is fragile in bash). Rust planned for high-frequency infrastructure loops.

**Why:** Bash JSON encoding broke on multilingual text with special chars. User confirmed python acceptable for daily LLM agent. User wants rust for the high-frequency conscious loop (startup time, performance).
**How to apply:** Don't write LLM API calls in bash. For new system scripts, bash is fine. For anything touching LLM APIs or complex data, use python.
