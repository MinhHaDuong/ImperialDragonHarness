# Environment: hosts, services and external tools

Scope: the author's two machines (padme, doudou), their shells, permissions,
credentials, data locations, and the Zotero and DOIfetch tools the harness
drives. Rules: `rules/guards.md`, `rules/coding-python.md`, `rules/zotero.md`.

## Current guidance
Hosts (dated measurements and author statements).
- padme: Threadripper PRO 3975WX, 32 physical cores / 64 threads (`lscpu`, 2026-10-30); shared with arena coders — one suite at `-n 24` took ~30 s alone, 57 s with a second suite (2026-10-29). State concurrent load with any timing.
- padme disk: `/` and `/home` one btrfs; `/scratch` unsnapshotted ext4 (TMPDIR); snapper held no home snapshots 2026-10-30, timeline timer stopped until the backup disk. `tmp-sweep.timer` (6 h) deletes `/tmp` entries idle > 24 h; skips worktree `.tmp/`.
- doudou alone runs the Nextcloud client (`~/CNRS`, `~/Media`, `~/perso`); padme syncs nothing; name excludes in `sync-exclude.lst`, read at client start. Sync problems are doudou's (author, 2026-10-30). Non-login `ssh` PATH omits `~/.local/bin` ([episode](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md)); uv: one subvolume for cache+env or `UV_LINK_MODE=clone`.

Data locations (author ruling 2026-10-31, tracker 1401): per host by lifecycle in `~/.config/environment.d/50-datasets.conf` — `DATASETS_DIR` both, `MIRRORS_DIR` padme only. One store under the "our data" folder: transcript archive `$DATASETS_DIR/ours/agent-sessions` (`raw/<host>/<runtime>/`, `launches.jsonl`, `spool/<host>/`), backfilled from cadens (~3.4 k padme, ~3.1 k doudou; 1391, PR 2086 [store](../journal/2026/2026-10-31-agent-sessions-store-1391.md)); doudou's drop-in rsyncs to padme (PR 2120). Monitoring (1382 open): four steps, 40-85 USD; median transcript 0.4 MB so compression dropped; padme archive timer first run 23 912 files / 8.6 GB; the August hole was doudou's 1 260 transcripts. [redesign](../journal/2026/2026-10-31-monitoring-and-data-locations.md), [raid 8ad75a](../journal/2026/2026-10-31-raid-8ad75a-monitoring-redesign.md)

Credentials. Agent sessions use `GH_CONFIG_DIR=~/.config/gh-agent`, a narrow fine-grained token (no admin); settings writes 403, the author's acts; token expires ~2027-10-27 — after rotation sync `~/.config/keys/github.env` per host and re-login. `settings.shared.json`: `Bash` plus named tools, no deny block ([episode](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md)). Secrets to `curl` via stdin, never argv.

Zotero (`scripts/zotero.py`, pyzotero, local only; rulings 2026-10-15/16): local API only, never sqlite/Web API/cache; writes reach existing items only as reports; tests on a private Xvfb or skip, no mocks ([1](../journal/2026/2026-10-16-zotero-local-only-decisions.md), [2](../journal/2026/2026-10-16-zotero-pyzotero-and-display-leak.md)); exact identifier or PDF md5 matching ([3](../journal/2026/2026-10-16-zotero-verbs-exact-match.md)); Zotero 10 takes local writes (9.x not); ask the author to open Zotero, faster ([preference](../journal/2026/2026-10-14-zotero-local-api-preference.md)); reconcile on demand, not in Molt. DOIfetch: not in `idh install`; `scripts/doifetch.sh` via pinned `uvx`, failed download exits 69, batch `.txt` only ([episode](../journal/2026/2026-10-29-doifetch-out-of-install.md)).
## Hazards
- `ssh host bash -s < script`: a stdin-reading command swallows the script, exit 0, no output; use `< /dev/null` ([episode](../journal/2026/2026-10-27-raid-prep-wave0-and-1206-doudou.md)).
- `grep` is a ripgrep function honouring `.gitignore`; use `/usr/bin/grep` for credential sweeps. Use `python3 -m pytest`, not bare `pytest`.
- A sweep is blind when positive `-g` globs drop `-t py`; fire a positive control first (2026-10-31). Dotfile "to EOF" replacement dropped lines; use an end marker. A tool output once displayed an API key (rotated).
## Open questions
- Silent fallback to `~/data` if `/data/datasets/ours` vanished on padme (gaze note, PR 2086); `gaze_seat.py:482` calls `spool_dir()` outside its try (below the ticket floor).
## Retired

- Per-skill Zotero transport choice and Web API reads: replaced by local-only (2026-10-15/16).
- Delegated GitHub admin (2026-10-21): superseded by the narrow token (2026-10-27).
- padme "3945WX/12 cores": contradicted by `lscpu` 2026-10-30.
- Separate cadens transcript store (`cadens-harvest`): merged into the one `datasets/ours/agent-sessions` store (1391).
- Doudou Nextcloud trash emptying "in progress, outcome unknown" (2026-10-30): dropped; sync is doudou's concern (author, 2026-10-30).

## Sources

- [Relocation lessons](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- [Cycle 3, key displayed](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- [Zotero architecture, PR #1143](../journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md)
- [Zotero train](../journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md)
- Legacy `../reference_zotero.md`; provenance: [source inventory](../../conception/memory-v8/source-inventory.md).
