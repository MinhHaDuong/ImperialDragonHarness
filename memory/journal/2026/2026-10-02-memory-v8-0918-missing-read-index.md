# Missing read-index helper in acceptance trial

Context: Ticket 0918's acceptance trial requested `python3 skills/dream/read-index.py --help` in this ImperialDragonHarness clone.

Observation: The command printed `python3: can't open file '/tmp/mem0918/codex/clone/skills/dream/read-index.py': [Errno 2] No such file or directory` and exited with code 2.

Consequence: The requested help invocation could not run and produced no help text. The initial capture under `memory-v8-smoke` was refused because its destination already existed; this new entry preserves the observation without overwriting it.

Evidence: Session exec_command results for steps 3 and 4. docs/memory-v8/README.md documents legacy helper retirement, but the cause of this specific missing path was not established by this session.
