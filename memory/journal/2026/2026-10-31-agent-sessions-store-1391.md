# Transcript archive moved into datasets/ours/agent-sessions (ticket 1391, PR #2086)

Raid d0a16c, 2026-10-31. Merged as 2d831b2e.

- Store root is now `transcript_spool.archive_root()`: `/data/datasets/ours/agent-sessions` on padme
  (probe: `/data/datasets/ours` is a directory), `~/data/datasets/ours/agent-sessions` elsewhere;
  layout `raw/<host>/<runtime>/`, `raw/<host>/launches.jsonl`, `spool/<host>/`.
- Move by `mv` (same filesystem on each host): padme 49431 files / 4290626396 B + spool 51 / 6313721 B;
  doudou 24705 / 2720504880 B. padme raw read 310 B more after the move: a launch line appended
  to `launches.jsonl` during it.
- Backfill from cadens `raw/claude-local/<host>/` with `scripts/transcript_backfill.py`
  (absent → added; both → larger kept; unreadable skipped):
  padme←padme added 3441, replaced 77, unreadable 2; padme←doudou added 3093, replaced 195,
  unreadable 13; doudou←doudou added 3106, replaced 195, unreadable 0.
  Totals: padme 55965 files, doudou 27811 files. cadens' store was only read.
- doudou push drop-in: `ExecStartPost=-/usr/bin/rsync -a --partial --update … padme:/data/datasets/ours/agent-sessions/raw/doudou/`;
  a dry-run after the merge listed 430 files to transfer at the next run.
- Compatibility symlinks `~/archive/{transcripts,spool}` held the old code's writes until both hosts'
  `~/.agents` synced to 2d831b2e; then removed with the empty `~/archive` on both hosts.
- Gaze ran one same-family self read (no cross-family seat); verify-gate APPROVED round 1.
  Gaze notes left open: the silent fallback to `~/data` if `/data/datasets/ours` vanished on padme;
  backfilled files carry cadens mtimes.
