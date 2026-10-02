# Retired dream index reader invoked by an acceptance-trial step

Context: memory-v8 acceptance trial (ticket 0918), Claude Code session, branch
t0918-acceptance-trials at be1ea2fc, 2026-10-02. A trial step prescribed
`python3 skills/dream/read-index.py --help`.

Observation: the command printed "python3: can't open file
'/tmp/mem0918/claude/clone/skills/dream/read-index.py': [Errno 2] No such file
or directory" and exited with status 2. `skills/dream/` contains only SKILL.md.

Consequence: a procedure still naming the legacy reader fails at the
interpreter, before any script logic runs; nothing was read or written.

Evidence: `git log -- skills/dream/read-index.py` ends at dc750a13 "Retire
legacy native/shared-store memory machinery"; docs/memory-v8/legacy-retirement.md
line 9 records its removal. The outcome is consistent with that adopted
retirement. Whether the trial step intended to probe the retirement is not
known to this session.
