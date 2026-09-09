---
name: Zotero library
description: Zotero user ID, API-key locations and scopes, main collection for Vietnamese energy decisions, endpoints
type: reference
---

Zotero userID: **95318**, username: `haduong`, display name: Minh Ha-Duong.

API keys stored in `~/.config/keys` (« comme toujours », auteur 2026-08-10 ; l'ancien emplacement `~/.claude/.env` est vide sur doudou) :
- `ZOTERO_API_KEY` — read-only (library + files + notes; groups read-only)
- `ZOTERO_RW_API_KEY` — read-write

Main collection for Vietnamese energy policy decisions: `T4X7ZNQL`.

Endpoints: items `https://api.zotero.org/users/95318/items`; file download
`https://api.zotero.org/users/95318/items/{itemKey}/file`; web library
https://www.zotero.org/haduong/library.

**Group file downloads need a key.** `GET /groups/<id>/items/<key>/file` returns 302 to the bytes with an API key and 404 anonymously, even when the files are fully synced; a PublicClosed group publishes metadata to the world and file bytes to members only. Measured 2026-09-07 on group 6659303 against group 305258 as a control, both identical. An anonymous probe therefore cannot tell "no bytes on the server" from "not allowed to read them", and one did produce a wrong finding, that the fixture group was not distributable.
