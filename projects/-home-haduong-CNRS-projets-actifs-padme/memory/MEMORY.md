## Key insights

- Always commit policy docs (main-logbook.md) together with their implementing scripts — they are a unit.
- Never say "prêt à commit" without actually committing. Either commit directly or ask if the user wants to commit.
- Deployment is symlinks into the main checkout working tree: a merge is not live until `git pull` runs in `/home/haduong/padme`; systemd units must stay `linked` (never `enable`, disable-before-link).
- Privileged operations belong to the author: no sudo, ever. Produce the exact command for them to run; snapper's apt pre/post hook and the NVIDIA/kernel apt-mark holds make routine `apt upgrade` self-bracketing and safe.
- padme is a layered monitoring system (L0 hardware → L4 planned rust loop); higher levels can override lower, L3 is observe-only by design. Don't duplicate checks across levels.
- A stopped service is not necessarily an incident: the author stops llama-server manually during heatwaves. Confirm intent before restarting or ticketing.
- Machine state (interventions, upgrades, incidents) is recorded in the padme repo — `intervention-log.txt` + STATE.md via PR — never in the harness repo, which carries only shared rules and skills.

## Entries

- [Opérations privilégiées](project_padme_privileged_ops.md)
- [Accès distant par netbird](project_padme_remote_access_netbird.md)
- [Vérifier le prédicat, pas seulement le résultat](feedback_verifier_le_predicat_pas_seulement_le_resultat.md)
- [systemd linked vs enabled](project-systemd-linked-vs-enabled.md)
- [Server management](project_server_management.md)
- [LLM backend: llama-server](padme-llm-backend-llama-server.md)
- [NVIDIA 580 hold posture](project-nvidia-580-hold-posture.md)
- [Secure Boot disabled / fwupd-MOK gotcha](project-secureboot-disabled-fwupd-mok.md)
- [No sudo — ask the user](feedback_no_sudo.md)
- [User profile](user_profile.md)
- [Language preferences](feedback_languages.md)
- [No wrapper skills](feedback_no_wrapper_skills.md)
- [Worktree stale after agent](feedback_worktree_stale_after_agent.md)
- [Host file writes: avoid heredoc](feedback_host_file_writes.md)
