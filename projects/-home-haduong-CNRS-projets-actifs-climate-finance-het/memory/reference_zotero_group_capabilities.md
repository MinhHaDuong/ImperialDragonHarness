---
name: reference_zotero_group_capabilities
description: "What the author's Zotero setup can do for the JETP group library (M4): key scope, storage, no API group creation, PublicClosed for files"
metadata:
  node_type: memory
  type: reference
  originSessionId: 2d60f2a1-01f1-453b-a627-5228aea3a0c3
  modified: 2026-09-29T09:14:38.438Z
---

Checked 2026-09-29 for the JETP document store (tickets 1510, 1511, milestone M4):

- `~/.config/keys/zotero.env` holds `ZOTERO_API_KEY` (read only) and
  `ZOTERO_RW_API_KEY`, whose scope is `groups.all: library + write`: it covers any
  new group with no new key. Check with `GET /keys/current`, never print the key.
- The author has an unlimited Zotero Storage plan; group files count against the
  owner's quota.
- The Web API v3 cannot create a group or change group settings: that is one
  manual step on zotero.org or in the desktop client.
- Open public groups allow no file sharing; a PublicClosed group shares metadata
  publicly and files with members only. The existing PublicClosed group "Semantic
  search challenge fixture" is configured that way.

Do not underestimate the automation already in place: ask or probe the key
before listing human blockers (the author corrected this). Related:
[[feedback_check_for_existing_library]], [[feedback_verify_before_advising]].
