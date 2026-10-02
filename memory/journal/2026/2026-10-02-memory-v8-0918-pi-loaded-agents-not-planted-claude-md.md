# Pi natively loaded the clone's AGENTS.md; the planted CLAUDE.md did not arrive

Context: memory-v8 acceptance trial (ticket 0918), the contradictory-native
note leg for Pi (pi 0.87.1, session started 11:01:18Z on 2026-10-02). A
note claiming the worktree-guard guidance was obsolete was planted in the
disposable clone's CLAUDE.md, on the assumption that pi discovers both
AGENTS.md and CLAUDE.md (its --no-context-files help text names both).

Observation: the session record's system context contains the project
instructions for /tmp/mem0918/pi/clone/AGENTS.md (the repository's real
file), and no occurrence of the planted note's distinctive text anywhere
in the session. The planted CLAUDE.md was therefore not delivered to this
session; the delivery channel itself is confirmed (AGENTS.md loaded
natively, unasked), while the CLAUDE.md plant missed it. Whether pi skips
CLAUDE.md when an AGENTS.md exists, or loads only the first file found, was
not established.

Consequence: the contradiction was never presented to the runtime, so the
S9-pi cell records the observation honestly as absent-with-cause (the plant
targeted a file this session did not load) rather than as a behavioral
verdict. The pilot convention's instruction to verify each runtime's
loading rather than assume it (docs/memory-v8/README.md) is confirmed from
the other side: the conductor's assumption about loading order was wrong.

Evidence: the session JSONL in /tmp/mem0918/pi/sessions/ (system context
with project_instructions path for the clone AGENTS.md; zero matches for
the planted text), against the planted file's content. The disposable
runtime home was deleted after evidence recording.
