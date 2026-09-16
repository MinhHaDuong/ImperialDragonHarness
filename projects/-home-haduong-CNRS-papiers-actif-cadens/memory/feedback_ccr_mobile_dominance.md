---
name: Managed-agent surface is mobile-dominant
description: 86% of the user's managed-agent sessions are Android-originated; mobile supervision is the dominant pattern, not CLI. The paper now uses "managed-agent" not "CCR".
type: feedback
originSessionId: 35c8b6cf-a45d-4464-98ce-71e58d3245e1
---
When framing anything about the user's Claude Code workflow — in paper prose, in memos, in discussion — do not default to desktop/CLI as the primary mental model.

**Empirical basis (captured 2026-04-22):** 105 managed-agent sessions, 90 (86%) originated from `origin: android`, 15 (14%) from `origin: web_claude_ai`. Median wall-clock duration 77 min, p95 26 h, max 91 h. Measured at the **event** level (what the paper cites), Android's share is **89%** (20,089 of 22,543 assistant events) because Android sessions carry more events per session. Cite the correct denominator for the claim: sessions → 86%, events → 89%.

**Terminology (2026-04-23):** "CCR" (Claude Code Remote) has been removed from the paper and replaced throughout with "managed-agent". Do not reintroduce the CCR acronym in paper prose.

**Why:** The paper's framing treats laptop + workstation CLI as the primary surface. This is measurable under-specification: the user does most supervision from their phone, dispatching long-running managed agents. Any prose implying "user at keyboard all day" mis-describes what they do.

**How to apply:** When writing or reviewing paper prose about the user's workflow, when interpreting fan-out / M(N) / regime distributions, or when suggesting analysis directions — start from "phone-first supervision of managed agents" as the default model, and name CLI as one surface among three. If a draft implicitly assumes "user at keyboard all day", flag it as a framing bug.
