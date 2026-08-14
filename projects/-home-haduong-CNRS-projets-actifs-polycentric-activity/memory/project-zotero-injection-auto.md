---
name: project-zotero-injection-auto
description: "Zotero API injection implemented (harness PR #718, 2026-08-13) — zotero-import ends in `inject`, RIS is fallback"
metadata: 
  node_type: memory
  type: project
  originSessionId: a4553684-97f9-418a-ba2a-4f61c23b7dd5
  modified: 2026-08-13T19:36:07.728Z
---

Decided and implemented 2026-08-13 (author: « Implémente l'injection Zotero »,
after the manual click for Echenique & Saito): the `zotero-import` skill now
injects items and PDF attachments directly through the Zotero Web API
(`inject` subcommand on `~/.claude/scripts/zotero-import.py`), harness PR
#718. Credentials come from `~/.config/keys/zotero.env`
(`ZOTERO_RW_API_KEY`, `ZOTERO_USER_ID=95318`). The RIS + `xdg-open` path
remains the fallback when no RW key resolves.

Consequence: EDM acquisition tickets (e.g. [[0051]]-style fulltext debts,
the 0031 MIMO staging import) no longer park on a human confirmation click.
Metadata quality checks stay in the skill's probe/match/dedupe steps.
