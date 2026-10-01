---
name: reference_padme_backup
description: "padme's nightly restic backup to Hetzner, its config repo, and the failure found 2026-09-30"
metadata:
  node_type: memory
  type: reference
  originSessionId: 99c20e86-e272-4f1d-999a-588c6d03f2c1
  modified: 2026-09-30T20:42:51.059Z
---

padme backs up `/home/haduong`, `/data`, `/etc` nightly at 02:30 with restic to a Hetzner Storage Box (keep 7d/4w/12m/5y); config and scripts in `~/CNRS/projets/actifs/padme/tools/` (backup-to-hetzner.sh, restic-excludes.txt; log `/var/log/p620-checks/restic-backup.log`). `/data/mirrors` (RePEc etc.) is excluded. The DVC remote of climate-finance-het is on the same NVMe as the cache, so this restic copy is the only off-disk copy until the Zotero copy (ticket 1712) lands.

On 2026-09-30 the service had not saved a snapshot since ~13 Sept: `/etc/restic/excludes.txt` symlinked to the repo's old path `~/padme`. The author repointed it; snapshot b6e9a723 saved. Exit status 3 (files vanished mid-run) shows as systemd "failed" though the snapshot is saved. See [[project_jetp_spec_v1]].
