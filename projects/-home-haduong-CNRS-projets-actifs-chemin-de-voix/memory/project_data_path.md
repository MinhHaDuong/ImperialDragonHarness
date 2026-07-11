---
name: project-data-path
description: "Training data lives at ~/data/projets/chemin-de-voix on doudou and /data/projets/chemin-de-voix on padme (mounted disk, from machine root)"
metadata: 
  node_type: memory
  type: project
  originSessionId: cc12a91e-6e67-476e-9156-1dfd3a6d4939
---

Data root differs per host:

- **doudou** (workstation): `~/data/projets/chemin-de-voix/`
- **padme** (GPU host): `/data/projets/chemin-de-voix/` (mounted disk, from machine root — NOT under `$HOME`)

The repo already mixes both forms: `scripts/train_lora.py` hardcodes the padme absolute path, while `scripts/train_queue_gpu*.sh` and `train_auteur_followup.sh` use `$HOME/data/projets/chemin-de-voix/corpus` (doudou-compatible). This is intentional — the scripts run on the host whose path form they use.

**Why:** Confirmed 2026-05-19. The original memory only knew about doudou; user clarified that ssh'ing to padme exposes `/data/projets/chemin-de-voix/` from machine root. README.md line 52 was both stale (`~/data/chemin-de-voix/` — wrong subpath) and pointed at a missing `setup-data.sh`. Fixed in worktree-t0242.

**How to apply:** Any path reference in tickets, scripts, or agent prompts must distinguish doudou vs padme. Don't `~`-expand padme paths and don't assume the doudou path works under ssh. Subpaths inside the root: `corpus/raw/`, `corpus/clean/`, `models/`, `generations/`. See also [[infra_padme]].
