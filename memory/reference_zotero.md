---
name: reference_zotero
description: Zotero user identity and API key locations — applies to any project accessing the user's Zotero library
metadata:
  type: reference
---

Zotero user: `haduong`, display name: Minh Ha-Duong, user ID: **95318**.

API keys:
- `ZOTERO_API_KEY` in `~/.claude/.env` — read-only (library + files + notes; groups read-only)
- `ZOTERO_RW_API_KEY` in `~/.claude/.env` — read-write

Base endpoint: `https://api.zotero.org/users/95318/items`

Project-specific credentials (read-write group access) live in separate files under `~/.config/keys/` — e.g. `zotero-archive-cired.env` for archiveCIRED.
