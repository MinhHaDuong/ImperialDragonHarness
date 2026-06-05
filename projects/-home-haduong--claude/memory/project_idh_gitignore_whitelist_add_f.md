---
name: idh-gitignore-whitelist-add-f
description: "IDH .gitignore is a `*` whitelist — git add of tracked files under non-whitelisted dirs (rules/, projects/) refuses without -f; check-ignore says not-ignored"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9c19a8ad-7f76-4f61-8a96-84d3d6d01758
---

The ImperialDragonHarness repo's `.gitignore` ignores `*` and whitelists
specific dirs with `!` rules. Files under dirs WITHOUT a whitelist entry
(e.g. `rules/`, `projects/`) can still be tracked (force-added historically),
and `git check-ignore` reports them not-ignored — but a plain `git add <path>`
of a modified tracked file there refuses with "paths ignored by one of your
.gitignore files". Use `git add -f <path>`. Hit twice on 2026-06-04
(`projects/.../MEMORY.md` salvage, `rules/git.md` edit).
