## Key insights

- Deployment is symlinks into the main checkout working tree: a merge is not live until `git pull` runs in `/home/haduong/padme`; systemd units must stay `linked` (never `enable`, disable-before-link).
- Privileged operations belong to the author: no sudo, ever. Produce the exact command for them to run; snapper's apt pre/post hook and the NVIDIA/kernel apt-mark holds make routine `apt upgrade` self-bracketing and safe.
- padme is a layered monitoring system (L0 hardware → L4 planned rust loop); higher levels can override lower, L3 is observe-only by design. Don't duplicate checks across levels.
- A stopped service is not necessarily an incident: the author stops llama-server manually during heatwaves. Confirm intent before restarting or ticketing.
- Machine state (interventions, upgrades, incidents) is recorded in the padme repo — `intervention-log.txt` + STATE.md via PR — never in the harness repo, which carries only shared rules and skills.

## Entries

- [systemd linked vs enabled](project-systemd-linked-vs-enabled.md) — deploy order: disable first, then ln -sf, never enable on-demand units; systemctl disable removes ALL symlinks including manual ln -sf ones
- [Server management](project_server_management.md) — padme monitoring architecture: bash L2, python L3, rust L4 planned; script names verified 2026-07-22
- [LLM backend: llama-server](padme-llm-backend-llama-server.md) — local inference is llama-server (llama.cpp) :8080 serving Qwen3.6-35B-A3B; ollama removed (0010); config + gotchas; stopped during heatwaves by design
- [NVIDIA 580 hold posture](project-nvidia-580-hold-posture.md) — why padme pins proprietary 580 + the exact apt-mark hold set the quarterly baseline expects (HWE metas not bare; retire at 26.04)
- [Secure Boot disabled / fwupd-MOK gotcha](project-secureboot-disabled-fwupd-mok.md) — SB off since 2026-06-10 (ticket 0041); fwupd firmware updates can de-trust the nvidia DKMS MOK → no GUI; MOK Manager renders on the boot GPU
- [No sudo — ask the user](feedback_no_sudo.md) — never run sudo; give the author the exact command and read the output; reaffirmed 2026-07-22
- [User profile](user_profile.md) — senior researcher, homelab sysadmin, KISS philosophy, prefers uv/apt-only
- [Language preferences](feedback_languages.md) — bash for system scripts, python for LLM integration, rust for high-frequency infra
- [No wrapper skills](feedback_no_wrapper_skills.md) — don't wrap self-documenting CLIs in skills; CLAUDE.md instructions + direct invocation
- [Worktree stale after agent](feedback_worktree_stale_after_agent.md) — verify via git show, not working tree, after isolation:worktree agents rename files
- [Host file writes: avoid heredoc](feedback_host_file_writes.md) — use printf or python3, not heredoc, for host file edits sent through chat (leading-space + first-line-split corruption)
