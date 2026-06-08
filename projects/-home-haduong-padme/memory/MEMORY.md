## Key insights

- padme is a layered monitoring system (L0 hardware → L4 planned rust loop) where higher levels can override lower; L3 is observe-only by design. Don't duplicate checks across levels.
- Deployment is via `/usr/local/bin` symlinks into the **main checkout working tree** — a merge isn't live until `git pull` runs in `/home/haduong/padme`, and if the primary is on a feature branch the cutover is gated on syncing it.
- Local LLM inference is **llama-server** (llama.cpp), not ollama: reasoning models (Qwen3) need `enable_thinking=false`, ollama GGUF blobs aren't llama.cpp-loadable, and llama-server 400s on context overflow where ollama silently truncated.
- The user is a KISS homelab sysadmin: bash for system scripts, python for LLM glue, rust for high-frequency infra; uv/apt only; don't wrap self-documenting CLIs in skills.
- Verify via `git show`/`git -C`, not the working tree, after worktree/isolation agents; long-running GPU/server processes need systemd (Bash-spawned ones get SIGTERM'd when the call returns).

## Entries

- [Server management](project_server_management.md) — padme monitoring architecture: bash L2, python L3, rust L4 planned
- [LLM backend: llama-server](padme-llm-backend-llama-server.md) — local inference is llama-server (llama.cpp) :8080 serving Qwen3.6-35B-A3B; ollama removed (0010); config + gotchas
- [Pending reboot: kernel 6.17.0-35](project_pending_reboot_kernel_635.md) — installed 2026-06-06, reboot pending; post-reboot checks + re-hold kernel metas (TTL 2026-06-20)
- [User profile](user_profile.md) — senior researcher, homelab sysadmin, KISS philosophy, prefers uv/apt-only
- [Language preferences](feedback_languages.md) — bash for system scripts, python for LLM integration, rust for high-frequency infra
- [No wrapper skills](feedback_no_wrapper_skills.md) — don't wrap self-documenting CLIs in skills; CLAUDE.md instructions + direct invocation
- [Worktree stale after agent](feedback_worktree_stale_after_agent.md) — verify via git show, not working tree, after isolation:worktree agents rename files
