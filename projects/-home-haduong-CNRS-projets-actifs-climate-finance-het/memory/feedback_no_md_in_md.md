---
name: No markdown inside markdown fenced blocks
description: Never put markdown (with ## headings) inside ``` fenced blocks — extract to a real file instead
type: feedback
---

Never put markdown content (especially `##` headings) inside fenced code blocks
in a markdown document. Unindented `##` lines that are only "inside a block"
because of a ``` several lines above are fragile and visually confusing.

**Why:** The reader can't tell which `##` lines are document structure vs. example
content without carefully tracking fence boundaries. It breaks scanning.

**How to apply:** When you need to show a markdown template or example, extract it
to its own file (e.g., `docs/ticket-template.md`) and reference it. The file
serves as both documentation and a copyable starting point.
