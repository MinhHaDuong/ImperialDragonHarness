# /data on padme

Bulk storage outside the snapshotted home. Organised by **lifecycle**, not by
project: what a thing is decides where it lives and whether it is backed up.
Doudou (the laptop) follows the same scheme under `~/data/` (see its README).

## Categories

| Path | What | Lose it? | Back up | Variable |
|---|---|---|---|---|
| `datasets/ours/` | data we produce and keep: `agent-sessions/` (agent transcripts, harness + cadens; private, GDPR-sensitive, mode 700) | irreplaceable | yes | `DATASETS_DIR` |
| `datasets/external/` | third-party data fetched or bought once, frozen (licensed extracts, downloads) | often irreplaceable | yes | `DATASETS_DIR` |
| `mirrors/` | live replicas of remote sources, re-synced (`RePEc/`, 111 GB; sync logs beside it) | rebuildable by re-syncing | no | `MIRRORS_DIR` |
| `models/` | model weights and model caches (`gguf/`, `safetensors/`, `cache/huggingface`) | re-downloadable | no | `HF_HOME`, `LLAMA_CACHE` |
| `cache/`, `uv-cache/` | tool caches (uv, ruff, mypy, arena) | regenerates itself | no | `UV_CACHE_DIR`, … (`/etc/environment`) |
| `projets/<name>/` | a project's own working data and DVC remotes/caches (`dvc/`, `dvc-cache/`) | per project | per project | the project's own config |
| `arena-store/` | arena benchmark artifacts | per arena policy | no | arena config |
| `padme-traces/` | hardware/system snapshots of padme | historical record | yes | — |

`~/data/` on padme holds scratch and bench work directories (acceptance
arenas, golden runs, `projets/` symlinks into `/data/projets`); nothing there is
a dataset.

## Rules

- **Code never hardcodes these paths.** It reads `$DATASETS_DIR` or
  `$MIRRORS_DIR` (declared per host in `~/.config/environment.d/50-datasets.conf`,
  which systemd user services and desktop sessions load; a script run over plain
  `ssh` reads that file itself) and fails with a clear message when unset.
- `MIRRORS_DIR` exists on padme only. A mirror is never copied to the laptop:
  work that needs it runs on padme.
- A result built from a mirror records the mirror's sync date (its rsync log),
  because the mirror changes under you.
- `datasets/ours/` content that is private never leaves the hosts unencrypted.
- New category? Decide its lifecycle first (frozen, replica, cache, project),
  then its place.

History: layout settled 2026-10-31 (harness trackers 1382 and 1401, ticket 1391 and the
`DATASETS_DIR` migration).
