# Roar: raid 075fa8, PR 2434 (ticket 1520), one definition of the transcript roots

Date: 2026-11-10. Project: harness. Raid 075fa8 (tickets 1520, 1519), team
lead claude-opus-5-5.

## Events

- The Blind-Spot pass (opus) found a third copy of the runtime roots,
  `scripts/trace_corpora.py` (used by trace-stats, trace-friction,
  trace-wall-time), which neither ticket named. It also found a Codex
  double count: once `archived_sessions/` is copied, the archive can hold one
  rollout twice, and Codex turns carry no message id for
  `drop_inherited_turns` to dedup. The raid recorded both as annotations on the
  tickets. Exit criteria stayed unchanged.
- PR 2434 landed `NAMED_ROOTS`, `named_roots`, `named_root`, `source_of`,
  `one_per_rollout` and `codex_home` in `scripts/transcript_spool.py`. The
  archive, `trace_timeline`, `trace_corpora` and `trace-compact-audit` now take
  their roots from it. The audit's Claude Code root now honours
  `CLAUDE_CONFIG_DIR`.
- Gaze answered REVIEWED with seats `panel` at 2b8665c12. That rested on
  `make check` plus gaze's own read of the diff; no independent seat saw it.
  verify-gate round 1 ruled APPROVED at 3ddbefd1f (the head plus the close
  commit). The gate re-ran `make check` (3668 passed, 132 skipped) and 242
  tests of the trace_corpora users.
- `raid_land.py` merged it at ca6511b62 and read it back as MERGED. The
  attribution block was not derivable: the gaze answer on notes carried no
  `reviewer:` lines, so `--capture-unit pr:2434` captured nothing.
- The first real run of the changed archive code is the nightly timer of
  2026-11-11 on padme. doudou copies its `archived_sessions/` from its first
  nightly run after its checkout syncs.

## References

- PR 2434; tickets/closed/1520-the-transcript-archive-copies-every-root.erg
- Gate verdict entry 20261110T135102154Z-padme-2cf7c663, review rv-20261110-pr-2434-fbc8
