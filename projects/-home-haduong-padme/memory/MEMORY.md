## Key insights

- padme is a layered monitoring system (L0 hardware → L4 planned rust loop) where higher levels can override lower; L3 is observe-only by design. Don't duplicate checks across levels.
- Deployment is via `/usr/local/bin` symlinks into the **main checkout working tree** — a merge isn't live until `git pull` runs in `/home/haduong/padme`, and if the primary is on a feature branch the cutover is gated on syncing it.
- Local LLM inference is **llama-server** (llama.cpp), not ollama: reasoning models (Qwen3) need `enable_thinking=false`, ollama GGUF blobs aren't llama.cpp-loadable, and llama-server 400s on context overflow where ollama silently truncated.
- The user is a KISS homelab sysadmin: bash for system scripts, python for LLM glue, rust for high-frequency infra; uv/apt only; don't wrap self-documenting CLIs in skills.
- Verify via `git show`/`git -C`, not the working tree, after worktree/isolation agents; long-running GPU/server processes need systemd (Bash-spawned ones get SIGTERM'd when the call returns). Worktree-isolated agents cannot call session-level tools (ExitWorktree) — the parent session must handle worktree lifecycle after agents return.
- When migrating a `.sh` script to `.py` in padme: critical stale-ref locations are (1) `.service` ExecStart, (2) `tools/README.md` deployment table + symlink + cron example, (3) `main-logbook.md` operational sections (ToC, architecture level, timer table, usage step, quarterly check). Historical bash-vs-python policy rows stay as-is with a "Résolu" annotation. Comment/string mentions (check-system-daily.sh threshold comment, reflect-quarterly.py string) are low-priority — not invocation paths.

## Entries

- [systemd linked vs enabled](project-systemd-linked-vs-enabled.md) — deploy order: disable first, then ln -sf, never enable on-demand units; systemctl disable removes ALL symlinks including manual ln -sf ones

- [Server management](project_server_management.md) — padme monitoring architecture: bash L2, python L3, rust L4 planned
- [LLM backend: llama-server](padme-llm-backend-llama-server.md) — local inference is llama-server (llama.cpp) :8080 serving Qwen3.6-35B-A3B; ollama removed (0010); config + gotchas
- [NVIDIA 580 hold posture](project-nvidia-580-hold-posture.md) — why padme pins proprietary 580 + the exact apt-mark hold set the quarterly baseline expects (HWE metas not bare; retire at 26.04)
- [Secure Boot disabled / fwupd-MOK gotcha](project-secureboot-disabled-fwupd-mok.md) — SB off since 2026-06-10 (ticket 0041); fwupd firmware updates can de-trust the nvidia DKMS MOK → no GUI; MOK Manager renders on the boot GPU
- [User profile](user_profile.md) — senior researcher, homelab sysadmin, KISS philosophy, prefers uv/apt-only
- [Language preferences](feedback_languages.md) — bash for system scripts, python for LLM integration, rust for high-frequency infra
- [No wrapper skills](feedback_no_wrapper_skills.md) — don't wrap self-documenting CLIs in skills; CLAUDE.md instructions + direct invocation
- [Worktree stale after agent](feedback_worktree_stale_after_agent.md) — verify via git show, not working tree, after isolation:worktree agents rename files
- [Host file writes: avoid heredoc](feedback_host_file_writes.md) — use printf or python3, not heredoc, for host file edits sent through chat (leading-space + first-line-split corruption)
