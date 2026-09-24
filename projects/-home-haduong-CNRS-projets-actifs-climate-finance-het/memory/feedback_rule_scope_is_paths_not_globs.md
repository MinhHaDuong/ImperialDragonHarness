---
name: feedback_rule_scope_is_paths_not_globs
description: "A .claude/rules file scoped with `globs:` loads in every session; only `paths:` scopes it — check with /context, not with a test that parses the header"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 927971ee-78e9-43c1-b08a-d1f151a487be
  modified: 2026-09-23T20:00:22.457Z
---

Three project rules here (writing, script-io, oeconomia-style) declared
`globs:` frontmatter and loaded at every session start anyway; the runtime
honours only `paths:`. The always-loaded budget test counted `globs:` as scoped,
so it passed at 197 lines while the real resident total was 323 against a
300-line budget. Fixed 2026-09-23 in PR #1469 (test red at 323 first); the
author confirmed with `/context` that the three files left the startup context.
aedist had rules with no header at all (fixed in its PR #1173).

**Why:** a guard that reads the declaration agreed with the declaration; only
the runtime's own report (`/context`) showed what loads.

**How to apply:** scope a rule with `paths:`. To verify a scoping change, run
`/context` in a fresh session before touching files, then touch a matching file
and watch the rule arrive. Related: [[feedback_static_guard_cannot_replace_an_invariant]],
[[feedback_dead_skill_names_route_to_neighbours]].
