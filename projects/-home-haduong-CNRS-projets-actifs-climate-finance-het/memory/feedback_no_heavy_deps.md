---
name: No heavy deps for simple tasks
description: Don't introduce heavy dependencies (jupyter, etc.) when a simpler approach exists
type: feedback
---

Don't introduce heavy dependencies for simple tasks. The inline Python approach for a single template variable pulled in jupyter (~1,200 lines in uv.lock). A hardcoded YAML variable was the right answer.

**Why:** User immediately spotted the bloat and asked to revert. Heavy deps slow installs and widen attack surface for no benefit.

**How to apply:** Before adding a dependency, check if the problem can be solved with what's already available (YAML, Lua filters, shell). Only add deps when the functionality genuinely requires them.
