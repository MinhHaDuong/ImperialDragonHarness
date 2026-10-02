# Prescribed capture slug collided with an existing entry

Context: Step 4 of ticket 0918's acceptance trial prescribed `scripts/memory-capture.sh "$PWD" public memory-v8-smoke`, with the missing-helper observation on stdin.

Observation: The helper printed `memory-capture: refusing to overwrite an existing entry: memory/journal/2026/2026-10-02-memory-v8-smoke.md (journal is append-only; corrections are new entries)` and exited with code 1.

Consequence: The prescribed capture did not write its entry. The step-3 observation was subsequently captured under the new slug `memory-v8-0918-missing-read-index`. The conflict was between the trial's exact slug and an already occupied journal destination.

Evidence: Session exec_command results for the prescribed invocation and subsequent capture. The existing entry's authorship and originating session were not investigated. docs/memory-v8/README.md requires a new descriptive slug on collision and prohibits overwriting journal entries.
