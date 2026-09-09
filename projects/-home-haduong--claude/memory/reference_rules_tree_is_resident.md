---
name: reference-rules-tree-is-resident
description: "The runtime loads ~/.claude/rules/**.md itself — no `paths:` frontmatter means the body is in every system prompt; the pointer-table design was never in force"
metadata: 
  node_type: memory
  type: reference
  originSessionId: aceca52d-6c71-4a74-ae75-85a9b713e441
  modified: 2026-09-09T17:45:00.000Z
---

**Mechanism, isolated 2026-09-09** (the 2026-09-09 morning observation left it
open, and guessed "presumably a runtime auto-load" — that guess was right).

Claude Code walks `~/.claude/rules/` at session start and sorts each `.md` on
one question: does its frontmatter declare `paths:`?

- **no `paths:` → resident.** The body is in the system prompt of every session,
  in every project, under "user's private global instructions for all projects".
- **`paths:` → conditional.** The body arrives only when the session touches a
  matching file.

Evidence, in the CLI bundle (2.1.266) and in the tree itself: the directory walk
filters on the presence of frontmatter globs; `claudeMdExcludes` documents
`**/some-dir/.claude/rules/**` as an exclusion target; the `/init` prompt tells
users `.claude/rules/` files "are loaded automatically alongside CLAUDE.md and
can be scoped to specific file paths using `paths` frontmatter". And the
observation fits exactly: `state.md` was the one body absent from the prompt,
and the one file that carried `paths:`.

**Not verified live** — writing to `~/.claude` was blocked in the container that
isolated it. The canary test: two files in `~/.claude/rules/`, one with
`paths: ["*.py"]`, each with a distinct sentence; ask a fresh session in a
non-Python directory which it can see. Expected: the unscoped one only.

What it cost, before the fix:

- ~39 200 resident tokens per session, **28 590 of them rules (73%)**.
- The index (`rules/README.md`) described in full what the runtime already
  shipped in full — and was itself resident *and* cat-ed a second time by
  `on-start.sh`. Nothing "read them on demand": `workflow.md` was opened 50
  times in 101 days and 5 730 sessions, `git.md` 23, because they were there.
- `inject_rule_on_edit.py` re-injected 1 069 rule bodies in that window, all
  already resident.

Fixed the same day: `paths:` on the eight path-expressible bodies (resident
28 400 → 21 600 tk), index reduced to what is *not* resident, `on-start.sh` cat
removed, `tests/test_rules_resident_budget.py` caps the set.

**The general lesson, worth more than the numbers.** A design can be void rather
than merely under-used, and the test suite will not say so: the guard on this
one asserted that the *hook* did not leak bodies, and passed for months while
the runtime loaded all of them. It watched the one channel that was innocent.
Before trusting a guard, ask which channel it reads and whether the thing it
denies could arrive by another.

Why it still matters: on a runtime without this auto-load (the Pi and Codex
adapters, tickets 0800/0802) the resident set must be injected by the adapter or
made genuinely on-demand. **What an adapter must ship is exactly the resident
set** — a mechanical definition where there was a judgment call. Numbers and
method: `scripts/census/`, `HANDOFF-2026-09-09.md`, ticket 0572.
