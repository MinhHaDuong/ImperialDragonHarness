# Memory v8 runtimes verified — 0924 smoke evidence

Smoke evidence for ticket 0924: one real headless session per runtime
(Claude Code 2.1.286, Codex 0.159.3, Pi 0.87.1) against a disposable clone
of this repository ran the same verification task — recall the two
worktree-session guards from the project memory, search the journal for
"gaze panel", write findings outside the repository, and record a public
capture through this script. All three read `memory/MEMORY.md` and the
worktree theme before their first write, found the same journal entry
(`2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md`) with ordinary
tools, and captured a public entry through this script with their runtime
slug; no native-profile sync was needed and no runtime required plumbing.
Evidence docs: 2026-10-02-memory-v8-runtime-claude-code.md,
2026-10-02-memory-v8-runtime-codex.md, 2026-10-02-memory-v8-runtime-pi.md
(under docs/), each recording versions, evidence channels and limits; the
sessions' own capture entries stayed in the disposable clones. Blind-spot
F5 was probed first: all three runtimes answered a trivial headless
prompt with exit 0 and verified output from a detached executor.
