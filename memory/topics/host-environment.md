# Environment: hosts, services and external tools

Scope: the author's two machines (padme, doudou), their shells, permissions,
credentials, data locations, and the Zotero and DOIfetch tools the harness
drives. Rules: `rules/guards.md`, `rules/coding-python.md`, `rules/zotero.md`.

## Current guidance
Hosts (dated measurements and author statements).
- padme: Threadripper PRO 3975WX, 32 physical cores / 64 threads (`lscpu`, 2026-10-30); shared with arena coders. State concurrent load with any timing. padme runs no sshd.
- padme disk: `/` and `/home` one btrfs; `/scratch` unsnapshotted ext4 (TMPDIR); snapper held no home snapshots 2026-10-30, timeline timer stopped until the backup disk. `tmp-sweep.timer` (6 h) deletes `/tmp` entries idle > 24 h; skips worktree `.tmp/`.
- doudou alone runs the Nextcloud client; padme syncs nothing; sync problems are doudou's (author, 2026-10-30). The CNRS carnet, missions and papers folders live on doudou, outside git: their pointer lines are author acts [4afd][source13]. Non-login `ssh` PATH omits `~/.local/bin` [source1]; uv: one subvolume for cache+env or `UV_LINK_MODE=clone`.

Data (author ruling 2026-10-31, tracker 1401): `DATASETS_DIR` both hosts, `MIRRORS_DIR` padme only, in `~/.config/environment.d/50-datasets.conf`. Transcript archive `$DATASETS_DIR/ours/agent-sessions` (`raw/<host>/<runtime>/`, `launches.jsonl`, `spool/<host>/`) [source2][source3]; doudou rsyncs to padme (PR 2120). The runtime roots have one definition, `scripts/transcript_spool.py` (1520); the context audit reads this host live and other hosts from the archive, with no ssh (1519) [075f][source14].

Credentials. Agent sessions use `GH_CONFIG_DIR=~/.config/gh-agent`, a narrow token: no settings writes, no workflow-file pushes, no issue close or delete [erg][source15]; expires ~2027-10-27, then sync `~/.config/keys/github.env` per host and re-login. Secrets to `curl` via stdin, never argv. A bench passing its environment to `sudo --preserve-env` logged a token in padme's system journal; the author left it as is [erg][source15].

Zotero (`scripts/zotero.py`, local API only, never sqlite/Web API/cache; tests on a private Xvfb or skip, no mocks) [source6][source7]. Identity: Zotero's own attachment md5 first, then identifiers (.bib, url/eprint, page text), title last (1502); identifier inequality alone is no proof of another work; embedded titles are hints ([rulings][source16]). Receipts: `<staging>/.receipts.jsonl` (1503) [f7aa][source17]. The project-specific filename suffix list left the shared helper (PR 2370). Writes reach existing items only as reports; reconcile on demand, not in Molt. Zotero 10 takes local writes (9.x not); ask the author to open Zotero [source9]. DOIfetch: not in `idh install`; `scripts/doifetch.sh` pins v0.4.0 (1513) via `uvx`; pass `--output-dir` on every launch; failed download exits 69; batch `.txt` only [source10][fc10][source18].

## Hazards
- `ssh host bash -s < script`: a stdin-reading command swallows the script, exit 0; use `< /dev/null` [source12].
- `grep` is a ripgrep function honouring `.gitignore`; use `/usr/bin/grep` for credential sweeps. Use `python3 -m pytest`.
- A sweep is blind when positive `-g` globs drop `-t py`; fire a positive control first. Dotfile "to EOF" replacement dropped lines; use an end marker. A tool output once displayed an API key (rotated). The local API ignores an `md5=` filter on attachments; `report-duplicates` took 63 s for 8,850 attachments [f7aa][source17].
## Open questions
- Silent fallback to `~/data` if `/data/datasets/ours` vanished on padme (gaze note, PR 2086), below the floor.

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- [Relocation lessons](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md), [Cycle 3, key displayed](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md), [Zotero architecture](../journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md), [Zotero train](../journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md), [exact match](../journal/2026/2026-10-16-zotero-verbs-exact-match.md), [settings](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md), [monitoring closure](../../tickets/closed/1382-monitoring-redesign-tracker-no-online-re.erg), [2026-11-07 batch](../journal/2026/2026-11-07-raid-train-controls.md), [1514 statements](../journal/2026/2026-11-10-roar-pr2418-zotero-statements-ticket-1514.md), [false red, suffix list](../journal/2026/2026-11-09-weekly-ticket-audit-and-false-red.md), [fleet audit](../journal/2026/2026-11-10-roar-raid-45e130-fleet-audit-trace-runtimes.md)
- Off the page, in their episodes: one-suite timing at `-n 24` (2026-10-29), backfill counts (~3.4 k padme, ~3.1 k doudou), compression dropped (median 0.4 MB), `settings.shared.json` shape, `gaze_seat.py:482`.
- Legacy `../reference_zotero.md`; provenance: [source inventory](../../design/memory-v8/source-inventory.md).

[source1]: ../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md
[source2]: ../journal/2026/2026-10-31-agent-sessions-store-1391.md
[source3]: ../journal/2026/2026-10-31-monitoring-and-data-locations.md
[source6]: ../journal/2026/2026-10-16-zotero-local-only-decisions.md
[source7]: ../journal/2026/2026-10-16-zotero-pyzotero-and-display-leak.md
[source9]: ../journal/2026/2026-10-14-zotero-local-api-preference.md
[source10]: ../journal/2026/2026-10-29-doifetch-out-of-install.md
[source12]: ../journal/2026/2026-10-27-raid-prep-wave0-and-1206-doudou.md
[source13]: ../journal/2026/2026-11-09-raid-4afdb3-post-skill-gaze-close.md
[source14]: ../journal/2026/2026-11-10-roar-raid-075fa8-audit-reads-archive.md
[source15]: ../journal/2026/2026-11-09-erg-claims-rollout-session.md
[source16]: user-rulings.md#on-tools-and-evidence
[source17]: ../journal/2026/2026-11-10-raid-f7aac3-staging-recognition-and-receipts.md
[source18]: ../journal/2026/2026-11-10-raid-fc1083-doifetch-pin-v0-3-0.md

## Fallback
