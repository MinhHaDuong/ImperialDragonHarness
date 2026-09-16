---
name: reference_finegrained_pat_scope_check
description: Only a private repo proves a fine-grained PAT is repo-bounded — public repos are readable by every fine-grained token
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9856e923-9da4-4c61-80c6-d279c7bce8d9
  modified: 2026-07-28T07:18:06.904Z
---

`AGENT_GH_TOKEN` for climate-finance-het is a **fine-grained PAT** bounded to
`MinhHaDuong/climate-finance-het` (installed 2026-07-28, ticket 0470). It lives
in `~/.config/keys/github.env` under `AGENT_GH_TOKEN_CLIMATEFINANCE` and reaches
the environment through the rename-on-export `KEYS=` entry
`github:AGENT_GH_TOKEN_CLIMATEFINANCE=AGENT_GH_TOKEN` — the suffix names the
repository the token is bounded to, because a fine-grained PAT is per-repository
and the keystore will hold one per project. See
[[reference_keystore_keys_selection]].

**To prove the scope is bounded, hit a private repo.** A fine-grained PAT can
read every *public* repository implicitly, whatever its selected-repositories
list. So `gh api repos/CIRED/cired.digital` resolving proves nothing, and
`gh api user/repos --jq length` is not a scope check either. Use a repo that is
private to the owner — `MinhHaDuong/{cadens,padme,fuzzy-corpus}` each 404 under
the scoped token and resolve under the classic one.

Verify under `env -i`, never in an inherited shell: `BASH_ENV` re-injects the old
value ([[feedback_bash_env_reinjects_secrets]]). Both application paths need
separate proof — the `BASH_ENV` loader for `make`, and `pipeline_loaders` →
`pipeline_keystore` for `dvc repro` and bare `uv run`
([[feedback_credential_migration_all_entry_points]]). Note
`pipeline_keystore` reads `$KEYS` from the environment and does *not* load
`.env` itself, so importing it alone exports nothing; import `pipeline_loaders`.

Write access needs its own check, and a reversible one exists: create
`refs/heads/<probe>` at an existing SHA via `gh api -X POST .../git/refs`, then
`-X DELETE` it. A read-only token passes every read check and then locks the
agent out at the next push.

**Expiry is a scheduled outage.** Fine-grained PATs cannot be non-expiring
(366 days maximum). When it lapses every forge operation fails with a 404 that
reads like a permissions bug, not an expired credential. The account-wide
classic PAT is still in the keystore under `AGENT_GH_TOKEN`, unreferenced by
this project, kept because other projects may select it.
