## Key insights

- Agent scope drift is the dominant failure mode: verify agents spiral, parallel agents contaminate branches, verify agents dirty the main repo. Defense: explicit "task complete after verdict" in prompts, worktree isolation, post-agent git status checks.
- Write-commit atomicity is a hard constraint imposed by beat's dirty-tree gate. Any skill writing tracked files without an immediate commit blocks the next beat cycle — treat it as a non-negotiable postcondition.
- Spec drift recurs because implementers copy peers, not the spec. erg verbs, headers, and skill architecture anti-patterns all trace to this. Adherence tests that grep the canonical spec are the ratchet.
- Credential architecture is a first-class design decision. BASH_ENV→bash-env.sh vs argv-leak, subscription auth vs funded direct-API key — both discovered through production failures. Every new secret-bearing feature needs an explicit credential path before implementation.
- This memory is the harness's operational runbook: invisible invariants and failure modes discovered at cost, not what the code does (that's git). Value compounds across sessions.

## Entries

- [Next move: git-erg migration](project_git_erg_migration_next.md) — Author's declared focus as of 2026-06-04; 0216 dogfood migration in git-erg; IDH tickets 0190/0191 are companions; check git-erg tickets ~0216 first
- [gh pr edit broken — use REST](feedback_gh_pr_edit_broken_use_rest.md) — gh pr edit hits a Projects-classic GraphQL deprecation; PATCH via gh api repos/.../pulls/N instead
- [Harness repo setup](project_harness_repo.md) — ~/.claude tracks ImperialDragonHarness, daily pull via systemd timer; each machine needs source line in ~/.bashrc
- [erg binary installation](project_erg_binary.md) — erg binary committed at tickets/erg in all repos; git pull to update; build from git-erg source if missing
- [BASH_ENV secret loading pattern](project_bash_env_secret_loading.md) — Secrets go via BASH_ENV→bash-env.sh (not CLAUDE_ENV_FILE); CLAUDE_ENV_FILE inlines KEY=VALUE into argv, leaking to ps -ef
- [erg verb drift recurs in skill examples](feedback_erg_verb_drift.md) — The `status` verb was removed from %erg v1; correct verbs are `created`, `note`, `closed`. Skills with log examples drift. Cross-check against spec-erg-v1.md, not other skills.
- [Rogue agent pattern — verify agents spiral](feedback_rogue_agent_pattern.md) — Re-verify agents can spiral into unscoped harness work after completing their task; add explicit "task complete after verdict" to prompt.
- [Verify forks can under-execute](feedback_verify_fork_under_execution.md) — A /verify fork can return a plausible partial result (no gate, no verdict comment, stale /tmp worktree); check 3 completion markers after every run, retry once; deterministic fix ticketed 0216.
- [Parallel execute agents contaminate branches](feedback_parallel_execute_branch_contamination.md) — Parallel isolation:worktree agents share git branch namespace; verify each PR's file list before /verify; re-execute sequentially from clean origin/main if contaminated.
- [Verify agents contaminate the invoking checkout](feedback_verify_agents_dirty_main_repo.md) — Contracts shipped (IDH PR #262: postcondition, narrowed staging, TASK DIRECTIVE); keep spot-checking git status + open PRs until ticket 0202 validates a clean raid cycle.
- [Fork skills start bare](feedback_fork_skills_bare_context.md) — context:fork gets only SKILL.md+args, no cwd, no conversation; doc-style body misread as documentation → ambient-cue drift; open with TASK DIRECTIVE, prefer Agent(isolation:worktree) for safety.
- [IDH gitignore whitelist needs add -f](project_idh_gitignore_whitelist_add_f.md) — Tracked files under non-whitelisted dirs (rules/, projects/) refuse plain git add despite check-ignore saying not-ignored; use git add -f.
- [erg spec headers are immutable](feedback_erg_spec_headers_immutable.md) — New erg headers require explicit user approval; prefer inverse lookups over new headers; erg binary must also be updated to accept them.
- [beat uses git checkout -B not worktrees](feedback_beat_checkout_model.md) — dirty main checkout carries into housekeeping branch; fix belongs in beat pre-flight, not in skill absorb
- [Skill commit discipline](feedback_skill_commit_discipline.md) — Skills writing tracked files must include git add/commit; uncommitted writes block next beat cycle via dirty-tree pre-flight
- [Skill architecture — no direct Anthropic API](feedback_skill_architecture.md) — Skills are SKILL.md + pure I/O helpers; never call anthropic.Anthropic() in helper scripts; Claude Code uses subscription auth, not funded direct-API key
- [Agnostic-guard catches ticket body paths](feedback_agnostic_guard_ticket_bodies.md) — Use ~/path not /home/user/path in ticket body examples; check-agnostic.sh scans tickets/ too
- [erg-pr-merge delete-branch race](feedback_erg_pr_merge_delete_branch_race.md) — Exit 1 after successful merge when GitHub deleteBranchOnMerge races the local cleanup; check PR state to confirm success
- [Module-level git paths break in worktrees](feedback_module_level_git_paths.md) — git rev-parse at import time resolves to worktree root; use argparse path arg with rev-parse as fallback
- [Unpushed main contaminates parallel worktrees](feedback_unpushed_main_contaminates_worktrees.md) — Push local main before launching parallel execute agents; unpushed commits become the worktree base, causing cross-contamination
- [Big artifacts go to /data/models](project_data_disk_model_store.md) — LLM weights/GGUFs never in homedir; /data/models/gguf/<family>/ is the writable store; LLAMA_CACHE=/data/models/cache is intended config — fix perms, don't redirect to homedir
