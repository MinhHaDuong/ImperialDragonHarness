---
name: feedback_agent_specs_detail
description: Parallel agents need detailed architectural specs, not vague goals
type: feedback
---

When launching parallel agents on related tasks, give each agent a detailed spec: module names, content lists, seam rationale, line targets per module.

**Why:** Three agents launched with "split X under 800 lines" all took the lazy path (extract one function, re-export, done). Three agents launched with "create syllabi_harvest.py (~300L) containing search+fetch, syllabi_process.py (~400L) containing classify+extract+normalize" produced quality architecture.

**How to apply:** Before launching implementation agents, do the architectural thinking yourself (or via a Plan agent). The implementation agent's job is execution, not design. Include module names, approximate line counts, content assignments, and the rationale for each seam in the prompt.
