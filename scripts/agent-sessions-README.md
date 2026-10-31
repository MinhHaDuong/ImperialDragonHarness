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
    spool/<host>/<runtime>[/<seat>]/   session files of doors that keep none, read by the archive
    README.md                      this file

One zstd file per source file, contents unmodified; the source mtime is stamped
on the copy.

## Runtimes

claude (Claude Code, with `subagents/` and `tool-results/`), codex, pi, aider,
vibe. The last three write through the spool.

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
