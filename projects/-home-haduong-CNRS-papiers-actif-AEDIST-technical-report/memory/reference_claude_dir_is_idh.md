---
name: claude-dir-is-idh-checkout
description: ~/.claude on doudou IS the live ImperialDragonHarness git checkout — no separate clone needed for IDH work
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9f2627e7-d2c9-4b17-8993-714c70f8b232
---

`~/.claude` on doudou is a git clone of
`https://github.com/MinhHaDuong/ImperialDragonHarness` — the installed harness
(skills/, scripts/, rules/, tickets/, settings.json) *is* the repo working tree.
Searching for a directory named "ImperialDragon*" misses it (2026-06-04: led to a
redundant /tmp clone during ticket 0412).

**How to apply:** for IDH work (skills, rules, harness tickets), branch inside a
clone of the same origin and PR; after merge, the live harness updates via
`git -C ~/.claude pull`. Check `git -C ~/.claude status` before assuming the live
copy is clean. [[erg-id-collision-across-branches]]
