Ticket 0918 acceptance trial, step 4. Context: the trial prescribed the exact
capture command `scripts/memory-capture.sh "$PWD" public memory-v8-smoke`
with the step 3 outcome on stdin.

Observation: the helper refused the capture and wrote nothing, printing
"memory-capture: refusing to overwrite an existing entry:
memory/journal/2026/2026-10-02-memory-v8-smoke.md (journal is append-only;
corrections are new entries)" and exiting 1. The occupied slug belongs to a
tracked, committed entry — the ticket 0923 deliberate public smoke capture
dated the same day — not to any write by this session.

Consequence: the prescribed exact command could not capture the step 3
outcome; the append-only collision guard behaved as documented, and no
plaintext of the offered entry reached the working tree. Whether the trial
design intended this collision, or whether the trial predates knowledge of
the 0923 entry, is unknown to this session.

Evidence: helper stderr and exit code captured in this session on 2026-10-02;
the occupying file inspected at HEAD be1ea2fc (last touched by d832d426).
