Ticket 0918 acceptance trial, step 6. Context: docs/memory-v8/README.md asks
adopters to verify each runtime's loading of project instructions rather than
claiming automatic injection; the pilot's declared runtime for this trial is
Vibe CLI.

Observation: this session's runtime natively injected the repository's
project AGENTS.md (/tmp/mem0918/vibe/clone/AGENTS.md, shown as "Project
instructions (checked into the codebase)") together with a user-level
AGENTS.md into the session context at start, before any request, read or
action by this session. No CLAUDE.md exists in the repository (ls confirmed;
the README suggests a compatibility symlink, none present). The injected
project AGENTS.md content matched the file on disk as later read (90 lines,
"# Harness agent profiles").

Consequence: automatic loading of AGENTS.md by this runtime is attested for
this session by direct observation, with no symlink or adapter involved. The
injection mechanism itself was not examined, so how the runtime discovered
the file remains unverified. A separate untracked entry,
2026-10-02-worktree-guard-guidance-conflict-step6.md, records the same
loading observation from another session; both preserved.

Evidence: session-start context observed before any file read; on-disk
comparison done in-session on 2026-10-02, branch t0918-acceptance-trials.
