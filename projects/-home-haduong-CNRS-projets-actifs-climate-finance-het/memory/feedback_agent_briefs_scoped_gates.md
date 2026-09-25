---
name: feedback_agent_briefs_scoped_gates
description: "Every executor brief must forbid the full suite and /tmp venvs — hunt's own rule runs make check on any scripts/ diff"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 36288e08-760c-498d-809d-4ea0d872d521
  modified: 2026-09-23T18:58:02.425Z
---

Every executor brief states the scoped gates AND forbids the rest: targeted tests (pytest -n 4 max), `make jetp-ledger-check` where relevant, `make check-fast` and `make lint` once each; never `make check` or an unscoped `pytest tests/` (in a worktree it fails at the corpus preflight anyway, and it runs ex post on main via /lair; long runs go to padme). No venv or large file in /tmp: it is a 12 GiB tmpfs shared with the Zotero indexing sitter, which refuses to work below 8 GiB free (a 1.1 GiB stray venv stalled it on 2026-09-23). Never `uv sync` the shared env while another agent runs.

**Why:** listing the wanted gates is not enough — hunt's contract calls the full `make check` for any diff under `scripts/`, so two parallel executors both launched the full suite on doudou (author: "Watch your subagents. Both launched the full pytest").

**How to apply:** paste these rules into every Agent prompt that runs code; see [[feedback_gate_proportionate_to_risk]].

**Merged from `feedback_no_shared_env_sync_during_sibling_agent` (2026-09-25):** Why: the shared /data env has no per-worktree isolation; a sync mid-run flipped the openalex-corpus path dep and crashed a sibling's testmon (0213 raid).
