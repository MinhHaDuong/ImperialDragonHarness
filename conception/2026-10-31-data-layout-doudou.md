# ~/data on doudou

The laptop's bulk data, organised by **lifecycle**, like `/data` on padme (the
server; see its README). Doudou is a work laptop: it keeps datasets, not
mirrors.

## Categories

| Path | What | Lose it? | Back up | Variable |
|---|---|---|---|---|
| `datasets/ours/` | data we produce and keep: `agent-sessions/` (agent transcripts, archived nightly then pushed to padme; private, mode 700), Archives CIRED numérisées, ISTEX extract, VIET DATA, … | irreplaceable | yes | `DATASETS_DIR` |
| `datasets/external/` | third-party data fetched or bought once, frozen: BP, Enerdata, IEA, UNSD, WRI, World Bank, Vietnam maps and statistics | often irreplaceable | yes | `DATASETS_DIR` |
| `projets/<name>/` | a project's own working data and DVC caches | per project | per project | the project's own config |
| `cache/` | tool and model caches (`cache/huggingface`) | regenerates itself | no | `HF_HOME` |
| `envs/` | Python environments | rebuildable | no | — |
| everything else (`acceptance-arena*`, `scratch-*`, `golden-*`, `redstate*`, `menagerie-*`, …) | scratch and bench work | disposable | no | — |
| `Zotero/` | the live Zotero data directory | irreplaceable | yes (Zotero's own) | — |

`/data` on doudou holds only system-level caches and environments
(`cache/`, `envs/`, `jupyter/`), set in `~/.bashrc`.

## Rules

- **No mirrors here.** The RePEc mirror (removed from doudou 2026-10-31) lives
  on padme in `/data/mirrors/`; work that needs it runs there. `MIRRORS_DIR` is
  deliberately unset on doudou, so code that needs a mirror stops with a clear
  message.
- **Code never hardcodes these paths.** It reads `$DATASETS_DIR`, declared in
  `~/.config/environment.d/50-datasets.conf` (systemd user services and desktop
  sessions load it; a script run over plain `ssh` reads that file itself), and
  fails when unset.
- `datasets/ours/` content that is private never leaves the hosts unencrypted.
- New category? Decide its lifecycle first (frozen, replica, cache, project),
  then its place.

History: layout settled 2026-10-31 (harness tracker 1382).
