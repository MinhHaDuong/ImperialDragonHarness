---
name: padme monitoring architecture
description: Multi-level monitoring stack — bash mechanistic, python reflective (llama-server), rust conscious loop planned
type: project
originSessionId: 373c4915-d420-4c58-8931-74f68c620ede
---
padme has a layered monitoring architecture:
- **Level 0-1**: Hardware/OS (BIOS, systemd, btrfs, fan2go)
- **Level 2**: Mechanistic bash scripts (check-resources.sh daily, quarterly-check.sh, backup-restic.sh). Threshold-based, no reasoning.
- **Level 3**: Reflective python agent (reflect-monitoring-history.py, daily 07:30). Feeds L2 history to local **llama-server** (Qwen3.6-35B-A3B, OpenAI `/v1/chat/completions` on :8080), reasons about trends/correlations. Read-only, never acts. Migrated off Ollama in ticket 0010 (2026-06-08); see [[padme-llm-backend-llama-server]].
- **Level 4**: High-frequency conscious loop in Rust — planned, not yet implemented. Higher-order reasoning/override capability.

**Why:** Higher levels CAN override lower — cybernetics principle user explicitly endorsed. L3 currently observe-only by design (cautious start).
**How to apply:** When discussing monitoring, respect the layered architecture. Don't duplicate checks across levels.

Deployment model (verified 2026-06-06): L2 scripts run from `/usr/local/bin/*.sh` symlinks pointing at the **main checkout working tree** (`/home/haduong/padme/tools/`). A merged fix is NOT live until `git pull` runs in `/home/haduong/padme`. Desktop alerts come from `desktop-monitor-notify.sh` via XDG autostart at login (not a timer). Bash checks carry their own smoke tests: `check-resources.sh --smoke-test`, plus the stdin hook in `btrfs_chunk_check` — extend these rather than testing in throwaway shell sessions ([[padme-monitoring-fails-loud]] incident, ticket 0014).
