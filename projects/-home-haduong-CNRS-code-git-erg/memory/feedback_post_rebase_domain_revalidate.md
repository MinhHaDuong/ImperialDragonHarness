---
name: post-rebase-domain-revalidate
description: "a conflict-free rebase can silently drop hunks when upstream rewrote the same file; re-run the domain validator (erg check) after every rebase, before push"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 28935cc7-f899-4c7d-abd7-a4079017615a
---

During the 0216 dogfood migration (cadens), rebasing the migration branch
onto origin/main completed "successfully" with zero conflicts — yet
upstream's edit of tickets/0037 silently reverted that file to `%erg v1`,
undoing the migration hunk. Only re-running `erg check` caught it.

**Why:** git's 3-way merge can resolve same-file changes by discarding one
side without flagging a conflict. "Rebase succeeded" certifies nothing
about semantic state.

**How to apply:** after ANY rebase (or merge) and before pushing, re-run
the domain validator on the touched corpus — `erg check tickets/` for
ticket stores, `make check-fast` for code. Idempotent fixers (`erg
migrate`) make repair one command. Sibling of [[rebase-fails-silently-
after-large-rename]] (same-tree no-op variant).
