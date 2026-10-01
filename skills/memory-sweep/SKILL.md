---
name: memory-sweep
description: "Review a project's repository memory for stale or contradictory claims."
disable-model-invocation: false
user-invocable: true
---

# Memory sweep — project memory maintenance

Resolve the project repository and read its AGENTS.md and `memory/MEMORY.md`.
If the destination or convention is unavailable, report it and stop. Do not
write to the installed harness, another project, or a native memory directory.

Review relevant `memory/topics/` against source episodes, current documentation
and user corrections. Mark or revise stale and contradicted claims, preserve
provenance and update the index so it points to current themes. Existing rules
can be referenced; do not create, propose or edit rules, AGENTS.md or skills.
Crystallisation requires a separate explicit user request with its destination.

Journal entries remain append-only. Add a dated correction rather than changing
or deleting an experience. Do not apply destructive TTLs to the journal or turn
list caps into rule promotions. Never store credentials.

Check that `memory/MEMORY.md` has at most 100 lines, including headings and
blank lines; move detail into topics before committing if needed.

Commit only the reviewed memory changes on a project branch and follow its
integration policy. Preserve unrelated changes and report failed writes or
commits. During roar, use its factual capture step instead of this sweep; do
not derive lessons from task wrap-up.
