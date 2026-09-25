# DELETED 2026-09-25T14:00Z: feedback_enterworktree_no_venv_symlink
# Reason: DELETE — STALE — superseded. The incident (2026-09-21/22) was caused by core.hooksPath transiently pointing at a missing hooks dir. Current .githooks/post-checkout (commits 411b554f 2026-09-17, 3e0fc56f, db1882cf 2026-09-24) now automatically symlinks .venv and .dvc/cache and initializes JETP document snapshots for every new worktree, and this automation is documented in .claude/rules/worktree-setup.md. The manual workaround this entry prescribes is no longer necessary.
# Original content preserved in git history.
