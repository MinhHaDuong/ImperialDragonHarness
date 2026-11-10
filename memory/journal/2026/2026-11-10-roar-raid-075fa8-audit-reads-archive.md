# Roar: raid 075fa8, PR 2438 (ticket 1519), the context length audit reads the other hosts from the archive

Date: 2026-11-10. Project: harness. Raid 075fa8, wave 2. It builds on PR 2434
(ticket 1520). Team lead claude-opus-5-5, executor claude-opus-5-5.

## Events

- PR 2438 removed the ssh path of ticket 1516: `FLEET_HOSTS`, the remote run,
  `--hosts`, `--aggregates-only` and the JSON `schema` key. The audit now reads
  this host live and every other host from `raw/<host>/<runtime>` of this host's
  archive, decompressing in memory through `trace_events.zstd_lines`. Each
  archived host is named with its newest file's date and the surfaces its copy
  holds. A grep of main for ssh and host names in the script returns nothing;
  the same grep form finds `zstd` 5 times.
- An mtime prefilter against the window start skips files before
  decompression, on the live walk too. Measured on padme at 0e11560c1 (load
  average 13.9): the default run took 53.3 s, `--local` 34.4 s, and a run with
  the archive root unresolvable 31.7 s, all exit 0. The `--local` baseline on
  19f1fb5a was 54.66 s.
- Default run: doudou's copy is dated 2026-11-08. It holds Claude Code 26873
  files, Codex sessions 1335 and Pi 48. It holds no Codex archived sessions and
  no Pi spool.
- Breach of the brief, reported by the executor: while running its tests red
  against the pre-change script, the default path probably opened one ssh
  command to doudou, the read-only remote audit run of ticket 1516. Nothing was
  written. No log confirms it either way.
- Scope step: `trace_events.zstd_lines`/`open_lines` now split on `\n` only.
  `str.splitlines()` also cut JSONL records at a raw U+2028/U+2029. The executor
  measured 84 unparsable lines on doudou's copy in the window, against 0 after
  the change. The gate ruled it a scope overflow (TICKETED). The raid filed
  record ticket 1521 and closed it in the same PR.
- Gaze answered REVIEWED: a self seat plus a cross-family red-team seat
  (gpt-6.1-sol). The red team's minor note, not adopted: the prefilter assumes
  no event is stamped later than its file's mtime. verify-gate round 1 ruled
  APPROVED at 23432a170. It merged at 0e11560c1, and the after-merge record on
  that tip passed.

## References

- PR 2438; tickets/closed/1519-context-length-audit-reads-the-other-hos.erg,
  tickets/closed/1521-transcript-readers-split-lines-on-newlin.erg
- memory/evidence/attribution/2026-11-10-review-attribution-pr2438.md
