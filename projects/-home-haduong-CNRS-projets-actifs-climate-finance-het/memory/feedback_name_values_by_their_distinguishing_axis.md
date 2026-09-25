---
name: feedback_name_values_by_their_distinguishing_axis
description: "Controlled-vocabulary values are named by the axis that distinguishes them, short (≤2 words), audited for accretion; the author rejected 'http-*' since everything is HTTP"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1679e82f-eedf-4fbf-a394-26b7d1cd905d
  modified: 2026-09-25T09:00:09.297Z
---

2026-09-25, JETP `collection_method`: the values had accreted one per ticket
(`script`, `browser-session`, `browser-manual`, `local-record`) and
`browser-session` was wrong (an HTTP client carrying cookies, no browser). My
first realignment named them `http`, `http-author-session`, … The author:
"tout est http non ?" — the protocol distinguishes nothing. They then shortened
`script-author-session` to `script-cookies` and pointed out that
`archive-copy` and `local-record` were closer than their names said
(→ `archive-record` / `local-record`). Final: `script`, `script-cookies`,
`browser-automated`, `browser-manual`, `archive-record`, `local-record`
(ticket 1183).

**Why:** the author reads vocabulary as ontology; a name built on a shared
property, or a three-word name, signals the list was not thought through.

**How to apply:** before proposing values, list the axes that actually vary
(client, identity, origin of the bytes), name each value by the axis that
separates it from its neighbours, keep existing names where they already fit,
cap at two words, and make siblings visibly siblings. See [[feedback_design_for_target_schema_not_legacy]].
