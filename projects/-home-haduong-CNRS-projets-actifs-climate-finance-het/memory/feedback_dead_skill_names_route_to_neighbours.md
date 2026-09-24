---
name: feedback_dead_skill_names_route_to_neighbours
description: "An instruction naming a skill that no longer exists gets resolved to its nearest living neighbour — AGENTS.md's dead `/verify (full loop)` made /gaze the default gate on every PR"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 927971ee-78e9-43c1-b08a-d1f151a487be
  modified: 2026-09-23T20:00:27.035Z
---

AGENTS.md carried an old copy of the harness workflow: seven of its skill names
were dead (/start-ticket, /celebrate, /end-session, /new-ticket, /verify,
/memory, /autonomous). "Gate each PR via `/verify`, the full loop" was read as
`/gaze`, so docs, data and ticket PRs all drew the full battery (~75 min, ~1M
tokens on 0872 vs an 11-min checklist on 0873). aedist and maiba carried the
same copy. Fixed 2026-09-23: climate-finance-het #1469/#1470, aedist
#1172/#1173, maiba #55, harness #991.

**Why:** a copied workflow drifts silently when the harness renames skills,
and a dead name fails soft — the agent substitutes, it does not error.

**How to apply:** project AGENTS.md holds only repo-specific rules and points
at `~/.claude/rules/` for the workflow; never re-copy harness content. When a
skill is renamed, grep every repo's AGENTS.md and `.claude/rules/` for the old
name. Related: [[feedback_rule_scope_is_paths_not_globs]],
[[project_proportionate_verify_pilot]].
