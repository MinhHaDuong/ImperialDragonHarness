---
name: feedback_no_shared_env_sync_during_sibling_agent
description: Never uv sync the shared /data env while a sibling background agent is mid-run — it thrashes their install fingerprint
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 12747467-454f-406d-aa17-ce1bab06ddc3
---

During the 0213 raid (parallel worktree Execute agents on a shared `/data` uv env),
finishing ticket 0217 myself I ran `uv sync` to install a dep for measurement.
Because the shared env is one env across all worktrees, and `openalex-corpus` is a
worktree-local path dep, my sync **flip-flopped that path binding** and disturbed
the concurrently-running 0216 agent's env — and busted the env fingerprint of the
tool I was measuring (pytest-testmon), producing a spurious `KeyError: 'lf'` crash
I briefly misdiagnosed as a real pytest-9 incompatibility. The 0216 agent even
observed "testmon uninstalled/reinstalled mid-session" — that was me.

**Why:** the shared env (see [[project_worktree_env_data]]) has no per-worktree
isolation; any `uv sync` from any worktree rewrites the single env's package set
and path-dep bindings, so a sync during a sibling agent's test run is a race.

**How to apply:** while any background agent is running against the shared env, do
NOT `uv sync`/`uv add`. If you must measure something needing a new dep, wait for
siblings to finish, or use an isolated throwaway venv (`uv venv .venv-tmp`), never
the shared one. When a tool crashes oddly mid-parallel-session, suspect env-thrash
before concluding a real incompatibility (diagnosis discipline). Related:
[[feedback_parallel_work]], [[feedback_worktree_isolation_is_path_based]].
