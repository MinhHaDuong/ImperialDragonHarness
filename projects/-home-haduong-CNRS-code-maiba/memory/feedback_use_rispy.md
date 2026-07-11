---
name: Use rispy for RIS parsing
description: User explicitly requires using the rispy library instead of writing a custom RIS parser — YAGNI principle
type: feedback
originSessionId: 6c9f06c6-a3f7-479b-b581-076baff198c3
---
Use the `rispy` library for RIS parsing instead of writing a custom parser.

**Why:** Writing a custom RIS parser is a textbook YAGNI violation when a maintained library (`rispy`) exists. The user called this out explicitly.

**How to apply:** In ticket 0001 and any RIS-related code, depend on `rispy` for reading/writing RIS files. The `maiba.ris` module should be a thin wrapper over rispy, adapting its output to the `Item` pydantic model. Don't reimplement what rispy already does.
