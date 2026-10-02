# Native load of an untracked CLAUDE.md contradicting project memory

Context: memory-v8 acceptance trial (ticket 0918), Claude Code session
(Opus 5.5) started in /tmp/mem0918/claude/clone, branch
t0918-acceptance-trials at be1ea2fc, 2026-10-02.

Observation: before any tool call, the runtime injected the contents of
/tmp/mem0918/claude/clone/CLAUDE.md, labelled "project instructions, checked
into the codebase". `git ls-files` lists only AGENTS.md; `git status
--ignored` shows CLAUDE.md as ignored ("!!"), so the file is untracked and
local. Its text (dated 2026-10-02) states that worktree-session-guard guidance
under memory/ is obsolete and that branch-mutating git commands no longer
require worktree-ownership confirmation. The memory files read this session
(memory/MEMORY.md blob b4ce4268, memory/topics/git-worktree-session-guards.md
blob b4428fa1, and the linked reference note) describe two command-text guards
(the rtk rewrite and the `-C` containment rule) and record no
worktree-ownership confirmation requirement. The clone's AGENTS.md was not
injected under its own path; the user-level ~/.claude/CLAUDE.md, which resolves
to /home/haduong/.agents/AGENTS.md, was injected and is byte-identical to it
(`diff -q`).

Consequence: a runtime-loaded, unversioned file asserted the obsolescence of
memory content in terms that do not match that content. This session did not
act on the claim; no branch-mutating git command was run.

Evidence: session system context; `git ls-files`, `git status --ignored`,
`readlink -f`, `diff -q` outputs in the session transcript. Who wrote the
CLAUDE.md and for what purpose is not established.
