# Environment: hosts, services and external tools

Scope: the author's two machines (padme, doudou), their shells, permissions,
credentials, and the Zotero and DOIfetch tools the harness drives. Rules: `rules/guards.md`, `rules/coding-python.md`, `rules/zotero.md`.

## Current guidance

Hosts (author statements and measurements, dated).
- padme: Threadripper PRO 3975WX, 32 physical cores, 64 threads (`lscpu`,
  `nproc` = 64, checked 2026-10-30).
  Reason in physical cores. Shared with arena coders: one suite at `-n 24`
  took ~30 s alone, 57 s with a second suite plus coders (2026-10-29); state
  concurrent load with any timing.
- padme disk: `/` and `/home` share one btrfs; `/scratch` is unsnapshotted
  ext4 (`TMPDIR`). The `home_haduong` snapper config held no snapshots on
  2026-10-30; the hourly timeline timer was stopped by the author until the
  backup disk arrives (restarts on reboot). Measure with `btrfs filesystem du -s`;
  deleting files frees little while a snapshot holds them.
- padme `tmp-sweep.timer` (every 6 h) deletes `/tmp` entries idle over 24 h;
  reports in `~/.local/state/tmp-sweep/`; skips worktree `.tmp/`, `/scratch/tmp`.
- doudou alone runs the Nextcloud client (on `~/CNRS`, `~/Media`, `~/perso`);
  padme syncs no files. Excludes are by name in
  `~/.config/Nextcloud/sync-exclude.lst`, read at client start, so restart
  after editing. Sync problems are doudou's, not padme's (author, 2026-10-30).
- A non-login `ssh` PATH omits `~/.local/bin`; use a login shell before calling a tool missing ([episode](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md)).
- uv: one subvolume for cache and env, or `UV_LINK_MODE=clone`.

Credentials and permissions.
- Agent sessions use `GH_CONFIG_DIR=~/.config/gh-agent` with a narrow
  fine-grained token (no administration); settings writes return 403 and are
  the author's acts (author, 2026-10-27). The token expires about 2027-10-27;
  after regeneration, sync `~/.config/keys/github.env` to each host and
  re-login the agent config on padme and doudou.
- `settings.shared.json`: `Bash` plus named tools, no deny block
  ([episode](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md)).
- Pass secrets to `curl` via stdin (`-H @-`), never argv.

Zotero (`scripts/zotero.py`, pyzotero, local only). Author rulings
2026-10-15/16: local API only, never sqlite, no Web API, no cache; writes
reach existing items only as reports. Tests start Zotero on a private Xvfb or
skip, no mocks ([1](../journal/2026/2026-10-16-zotero-local-only-decisions.md),
[2](../journal/2026/2026-10-16-zotero-pyzotero-and-display-leak.md)).
Matching is exact normalised identifier or PDF md5; title hits are candidates
([3](../journal/2026/2026-10-16-zotero-verbs-exact-match.md)). Zotero 10 accepts local writes (9.x does not). Ask the author to open Zotero; it is
faster ([preference](../journal/2026/2026-10-14-zotero-local-api-preference.md)).
Reconcile runs on demand, not in Molt
([episode](../journal/2026/2026-10-15-molt-zotero-reconcile-removed.md)).
Web API group file downloads need a key (anonymous 404, 2026-09-07); keys are under `~/.config/keys`.

DOIfetch is not installed by `idh install`: `scripts/doifetch.sh` runs it via
pinned `uvx`; failed download exits 69; batch input is `.txt` only
([episode](../journal/2026/2026-10-29-doifetch-out-of-install.md)).

## Hazards

- `ssh host bash -s < script`: a stdin-reading command swallows the script,
  exit 0, no output; use `< /dev/null`. A mis-quoted ssh heredoc ran doc text as shell on doudou
  ([episode](../journal/2026/2026-10-27-raid-prep-wave0-and-1206-doudou.md)).
- `grep` is a ripgrep function honouring `.gitignore`; use `/usr/bin/grep`
  for credential sweeps. Use `python3 -m pytest`, not bare `pytest`.
- Dotfile block replacement "to EOF" dropped lines on padme; use an end marker.
- A tool output once displayed an API key (rotated).

## Open questions

- Snapshots pinning old venv copies is the entry's reading, unverified.
- Doudou Nextcloud trash emptying (2026-10-30) was in progress; outcome unknown.

## Retired

- Per-skill Zotero transport choice and Web API reads: replaced by local-only (2026-10-15/16).
- Delegated GitHub admin (2026-10-21): superseded by the narrow token (2026-10-27).
- padme "3945WX/12 cores": contradicted by `lscpu` on 2026-10-30.

## Sources

- [Relocation lessons](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- [Cycle 3, key displayed](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- [Zotero architecture, PR #1143](../journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md)
- [Zotero train](../journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md)
- Legacy `../reference_zotero.md`; provenance: [source inventory](../../conception/memory-v8/source-inventory.md).
