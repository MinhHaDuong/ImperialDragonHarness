# Capture helper refused a slug colliding with the 0923 smoke entry

Context: memory-v8 acceptance trial (ticket 0918), Claude Code session,
branch t0918-acceptance-trials at be1ea2fc, 2026-10-02. A trial step
prescribed `scripts/memory-capture.sh "$PWD" public memory-v8-smoke` with a
factual entry on stdin.

Observation: the helper printed "memory-capture: refusing to overwrite an
existing entry: memory/journal/2026/2026-10-02-memory-v8-smoke.md (journal is
append-only; corrections are new entries)" and exited with status 1. The
existing file is tracked (last touched in d832d426, ticket 0923) and holds the
0923 smoke evidence.

Consequence: no file was written; the existing 0923 smoke entry stayed
unchanged (working tree clean for that path afterwards). The entry text
offered under that slug was later captured under the slug
retired-read-index-invoked-in-trial.

Evidence: helper stdout/stderr and exit status in the session transcript;
`git log -- memory/journal/2026/2026-10-02-memory-v8-smoke.md`. The collision
arises because the fixed slug and today's date match an entry captured earlier
the same day; whether the trial designed the collision is not known to this
session.
