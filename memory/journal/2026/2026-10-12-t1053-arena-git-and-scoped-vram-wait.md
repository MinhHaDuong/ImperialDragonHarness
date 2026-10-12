# 2026-10-12 — ticket 1053: arena under git, scoped vram-wait

Context: `/raid 1053` on a `deferred` ticket. The raid stopped at Phase 1:
the code lives in `~/arena` on padme, which was not a git repository, and
every exit criterion needs live GPU runs. The author chose to put the arena
under git (1a) and to coordinate the smoke with the parallel 1048 session.

Events:
- `~/arena` on padme became a local git repo (no remote): baseline
  `ce3b61d`, fixes on branch `t1053-pass-aware-cap` (`b03b205`). Run
  outputs, logs, `*-before-*` backups and the 1048 session's files
  (`qual*.sh`, `needle.py`, `qual-gemma-*`, `qual.pid`) are ignored.
- The lifetime cap was in `runner.py:34` (`MAX_ATTEMPTS`), not in
  `drive2.py` as the ticket stated.
- GPU access was serialized with the 1048 session by cross-session
  messages; that session holds inbound messages for approval, so each
  message was delayed before delivery. Production llama-server :8080
  was never stopped by this session.
- The first smoke of the scoped `vram-wait` stalled: an arm that is not up
  yields an empty pid list, and `vram-wait` with no arguments fell back to
  the global 800/600 MiB thresholds, which a resident arm A never meets.
  Fixed with an explicit `--pids` marker.

Outcome: wrap-up teardown (`local_arms_down(exclude="a")`) with arm A
resident took 0 s, previously ~15 min; a live-holder control kept
blocking. The per-pass cap was checked on copies of the logic only:
0470-c/k/l (2 lifetime attempts) count 0 under a new pass. Ticket 1053
stays open pending a real re-pass and review of the arena branch.
Evidence PR: #1364.
