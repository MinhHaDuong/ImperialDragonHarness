# Environment: hosts, services and external tools

Scope: the author's two machines (padme, doudou), their shells, permissions,
credentials, data locations, and the Zotero and DOIfetch tools the harness
drives. Rules: `rules/guards.md`, `rules/coding-python.md`, `rules/zotero.md`.

## Current guidance
Hosts (dated measurements and author statements).
- padme: Threadripper PRO 3975WX, 32 physical cores / 64 threads (`lscpu`, 2026-10-30); shared with arena coders — one suite at `-n 24` took ~30 s alone, 57 s with a second suite (2026-10-29). State concurrent load with any timing.
- padme disk: `/` and `/home` one btrfs; `/scratch` unsnapshotted ext4 (TMPDIR); snapper held no home snapshots 2026-10-30, timeline timer stopped until the backup disk. `tmp-sweep.timer` (6 h) deletes `/tmp` entries idle > 24 h; skips worktree `.tmp/`.
- doudou alone runs the Nextcloud client (`~/CNRS`, `~/Media`, `~/perso`); padme syncs nothing; name excludes in `sync-exclude.lst`, read at client start. Sync problems are doudou's (author, 2026-10-30). Non-login `ssh` PATH omits `~/.local/bin` ([episode][source1]); uv: one subvolume for cache+env or `UV_LINK_MODE=clone`.

Data locations (author ruling 2026-10-31, tracker 1401): per host by lifecycle in `~/.config/environment.d/50-datasets.conf` — `DATASETS_DIR` both, `MIRRORS_DIR` padme only. One store under the "our data" folder: transcript archive `$DATASETS_DIR/ours/agent-sessions` (`raw/<host>/<runtime>/`, `launches.jsonl`, `spool/<host>/`), backfilled from cadens (~3.4 k padme, ~3.1 k doudou; 1391, PR 2086 [store][source2]); doudou's drop-in rsyncs to padme (PR 2120). Monitoring tracker 1382 is closed: the author confirmed the interactive timeline. Compression was dropped because the median transcript was 0.4 MB; memo § 5 retains its deferred items and triggers. [Monitoring][source3]; [closure][source4].

Credentials. Agent sessions use `GH_CONFIG_DIR=~/.config/gh-agent`, a narrow fine-grained token (no admin); settings writes 403, the author's acts; token expires ~2027-10-27 — after rotation sync `~/.config/keys/github.env` per host and re-login. `settings.shared.json`: `Bash` plus named tools, no deny block ([episode][source5]). Secrets to `curl` via stdin, never argv.

Zotero (`scripts/zotero.py`, pyzotero, local only; rulings 2026-10-15/16): local API only, never sqlite/Web API/cache; writes reach existing items only as reports; tests on a private Xvfb or skip, no mocks ([1][source6], [2][source7]); exact identifier or PDF md5 matching ([3][source8]); Zotero 10 takes local writes (9.x not); ask the author to open Zotero, faster ([preference][source9]); reconcile on demand, not in Molt. DOIfetch: not in `idh install`; `scripts/doifetch.sh` via pinned `uvx`, failed download exits 69, batch `.txt` only ([episode][source10]).
The 2026-11-07 Zotero filename batch is report-only and labelled pre-correction. The AJAE follow-up returned candidates, not exact identities; sanitized evidence and the corrected suffix are linked in [train][source11]. No library writes occurred.

## Hazards
- `ssh host bash -s < script`: a stdin-reading command swallows the script, exit 0, no output; use `< /dev/null` ([episode][source12]).
- `grep` is a ripgrep function honouring `.gitignore`; use `/usr/bin/grep` for credential sweeps. Use `python3 -m pytest`, not bare `pytest`.
- A sweep is blind when positive `-g` globs drop `-t py`; fire a positive control first (2026-10-31). Dotfile "to EOF" replacement dropped lines; use an end marker. A tool output once displayed an API key (rotated).
## Open questions
- Silent fallback to `~/data` if `/data/datasets/ours` vanished on padme (gaze note, PR 2086); `gaze_seat.py:482` calls `spool_dir()` outside its try (below the ticket floor).

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- [Relocation lessons](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- [Cycle 3, key displayed](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- [Zotero architecture, PR #1143](../journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md)
- [Zotero train](../journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md)
- Legacy `../reference_zotero.md`; provenance: [source inventory](../../conception/memory-v8/source-inventory.md).


[source1]: ../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md
[source2]: ../journal/2026/2026-10-31-agent-sessions-store-1391.md
[source3]: ../journal/2026/2026-10-31-monitoring-and-data-locations.md
[source4]: ../../tickets/closed/1382-monitoring-redesign-tracker-no-online-re.erg
[source5]: ../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md
[source6]: ../journal/2026/2026-10-16-zotero-local-only-decisions.md
[source7]: ../journal/2026/2026-10-16-zotero-pyzotero-and-display-leak.md
[source8]: ../journal/2026/2026-10-16-zotero-verbs-exact-match.md
[source9]: ../journal/2026/2026-10-14-zotero-local-api-preference.md
[source10]: ../journal/2026/2026-10-29-doifetch-out-of-install.md
[source11]: ../journal/2026/2026-11-07-raid-train-controls.md
[source12]: ../journal/2026/2026-10-27-raid-prep-wave0-and-1206-doudou.md

## Fallback
