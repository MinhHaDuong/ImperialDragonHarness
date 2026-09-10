---
name: reference-no-recall-channel-fires
description: "the resident index is the only door to a memory body — no automatic recall fires on this runtime, measured over 5 753 traces with a positive control"
metadata:
  type: reference
---

# The resident index is the only door

The platform's memory instructions describe recall in the present tense: a
body's `description:` frontmatter "is used to decide relevance during recall",
and recalled memories arrive inside `<system-reminder>` blocks. **On this
runtime nothing fires.**

Measured 2026-09-10 over all 5 753 local session traces, two probes because a
channel injecting only summaries would be invisible to the first:

- 25 distinctive mid-body sentences: 51 hits in a tool_result, 11 in a Write,
  2 incidental. Zero injections.
- 40 `description:` lines: 113 in a tool_result, 20 in a Write, 4 incidental.
  Zero injections.

Positive control: 32 of the 40 description lines appear somewhere in the
traces, so the probe sees the text it looks for.

**What follows, and it inverts the obvious remedy.** An entry dropped from an
index is not demoted, it is unreachable. Shortening a resident index by
unlisting entries silently deletes them. A two-level scheme therefore needs its
second level named by a resident line — about 60 bytes — not left to a recall
that does not happen. A pure `[[wiki]]` graph is worse than it looks for the
same reason: traversal needs an entry point and the entry points were to come
from recall.

Corollary: `description:` is written by every memory write and read by nothing
here, so any ranking keyed on retrieval frequency has no input signal.

Re-run before trusting this a year out — it is a claim about a runtime, and
runtimes change. The probes live in the method section of
`docs/2026-09-10-dragon-memory-design.md` §2.4.

See also [[feedback_subagent_traces_dilute_every_rate]].
