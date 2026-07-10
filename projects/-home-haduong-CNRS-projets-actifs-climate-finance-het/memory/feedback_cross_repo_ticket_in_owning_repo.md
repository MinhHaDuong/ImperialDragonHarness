---
name: feedback_cross_repo_ticket_in_owning_repo
description: "File a follow-up ticket in the repo that OWNS the target file, not the consuming project that discovered the need"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 12747467-454f-406d-aa17-ce1bab06ddc3
---

During the 0213 test-tiers raid I found the global harness rule
`~/.claude/rules/coding-python.md` needed a cost-based marker-table update, and
filed CFH ticket 0220 for it — in **climate-finance-het's** tracker. That file
belongs to the **ImperialDragonHarness** repo, not CFH. The author caught it:
"did you create the ticket in IDH?" — I had not. The result was a dangling
cross-repo reference: a reminder invisible to anyone working in the repo that
would actually do the work.

**Why:** a ticket filed in the consuming project can only be seen/actioned there,
but the work (and its `/hunt`, its PR gates) happens in the owning repo. IDH has
its own `~/.claude/tickets` erg store — the correct home. See
[[project_imperial_dragon.md]] (generic harness = ImperialDragonHarness repo;
project `.claude/` keeps project residuals only).

**How to apply:** when a follow-up's target file lives in another repo, file the
ticket in THAT repo's tracker (branch + PR there — its main is read-only too and
it has required CI checks: validate-tickets/skill-lint/guards/pytest). Close the
consuming-repo ticket as "migrated to <owning-repo> <id>" if one was already
filed. Fix for 0220: re-filed as IDH 0269 (IDH PR #446), closed CFH 0220 migrated
(CFH #983). Related: [[feedback_no_shared_env_sync_during_sibling_agent]].
