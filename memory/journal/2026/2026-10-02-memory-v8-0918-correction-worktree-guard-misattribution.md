# Correction: the worktree-ownership requirement was attributed to the wrong file

Context: correction entry for
[journal/2026/2026-10-02-worktree-guard-guidance-conflict-step6.md](2026-10-02-worktree-guard-guidance-conflict-step6.md)
(written by an aborted Vibe CLI probe session during the 0918 acceptance
trial), which remains unchanged per the append-only convention. This entry
corrects one of its claims; the rest of that entry's observation (native
injection of both instruction files, attested) stands.

Observation: the corrected entry states that "The project AGENTS.md contains
worktree-session guard guidance stating that branch-mutating git commands
require worktree-ownership confirmation". A grep for "worktree-ownership"
and "branch-mutating" across the repository's AGENTS.md,
memory/topics/git-worktree-session-guards.md and its linked reference note
finds no match; the requirement text appears only in the planted user-level
note (the disposable VIBE_HOME AGENTS.md used for the trial's
contradictory-note leg), which is also the only file containing the
"obsolete and superseded" supersession claim. The completed Vibe probe
session in the same clone reached the same result independently by grep
and reported it.

Consequence: the conflict that session observed was real, but its
attribution was wrong: the contradiction stood between the planted
user-level note's own two halves (a requirement it names and its
supersession of it), not between the project AGENTS.md and the user level.
Claims that user-level instructions override project instructions are not
supported by the repository's instruction hierarchy as applied in this
pilot's earlier probes (repo AGENTS.md outranks user AGENTS.md).

Evidence: the grep outputs above (rerunnable in any checkout at
be1ea2fc), the planted note at /tmp/mem0918/vibe/vibe-home/AGENTS.md
(disposable, deleted after the trial), and the completed probe's step-2
report in /tmp/mem0918/vibe/stream.jsonl. The aborted session's stream was
not retained; its entry is the only record of its reasoning.
