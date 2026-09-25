---
name: feedback_mocks_use_real_values
description: A mock shown to the author for approval must carry real values from the data, never a plausible invention
metadata:
  type: feedback
---

On 2026-09-25 I showed the author a mock of the Documents row with the
title "Off-Grid Europe Mini-Grid 2025 (FR)", made up from the file name.
The author approved the mock; the coding agent then found the registry
title is "Solution Mini-Grid 2025" and had to flag the mismatch as a
possible data error.

**Why:** an approved mock becomes a spec; an invented value in it reads as
the author's decision and sends the next agent chasing a data "error".

**How to apply:** before showing a mock, read the real values it displays
(titles, dates, counts) from the served data; where a value is not yet
served, mark it as a placeholder ("<title from registry>"). Related:
[[feedback_read_before_cite]].
