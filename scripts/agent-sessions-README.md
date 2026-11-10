# agent-sessions

Raw transcripts of the AI agent sessions run on the author's hosts, kept beyond
the runtimes' own retention.

## Provenance

Written nightly by `scripts/transcript_archive.py` of the Imperial Dragon
Harness (systemd user timer `transcript-archive`, tickets 1383 and 1391).
Backfilled on 2026-10-31 from the cadens raw store (`raw/claude-local`, Claude
Code only), which held 2026-02 to 2026-05 sessions already deleted from the
live trees.

## Layout

    raw/<host>/<runtime>/<path relative to the runtime's own tree>.zst
    raw/<host>/launches.jsonl      which session launched which headless child
    raw/<host>/seat-raw/<seat id>-<seat>.raw   a headless gaze seat's output as received, up to 256 KiB
                                   re-derive one, no model call: gaze_seat.py replay --raw <file> --sha256 <hex> --runtime <door>
    spool/<host>/<runtime>[/<seat>]/   session files of doors that keep none, read by the archive
    README.md                      this file

One zstd file per source file, contents unmodified; the source mtime is stamped
on the copy.

## Runtimes

claude (Claude Code, with `subagents/` and `tool-results/`), codex, pi, aider,
vibe. The last three write through the spool.

Each runtime's source roots are defined once, in `transcript_spool.py`
(`NAMED_ROOTS`). Two runtimes have two roots, told apart by depth below
`raw/<host>/<runtime>/` (`source_of`): codex copies `sessions/` (dated
`YYYY/MM/DD/` tree) and, since 2026-11-10, `archived_sessions/` (flat, depth 1);
pi copies its live sessions (one directory per working directory) and its spool
(flat, depth 1). A Codex rollout copied from both roots is held twice; a reader
counts it once, keeping the copy with the greatest mtime, then size
(`one_per_rollout`).

## Retention

The runtimes prune their live trees by age. The archive keeps everything and
never deletes. A source that grew since its last copy is copied again.

## Privacy

Behavioural data of the author, sensitive under the GDPR. Directories 700,
files 600. It never leaves the hosts unencrypted. doudou pushes its `raw/doudou/`
to padme over ssh.

## Consumers

Harness: `trace_timeline.py`, the launch lines. cadens: its own ticket 0049
switches its reader to this store.
