---
name: email
description: "Read local mail: live Evolution cache and ~/.mail archives. Load when the user asks to read, search, summarize, or reply-draft their email/inbox, or mentions mail messages."
user-invocable: true
---

# Email — reading local mail from files

There is no mail connector. All mail lives on disk in maildir-style layouts and is read with `bash` + `read_file`.

## Locations

- **Live mail** — Evolution cache, sharded maildirs:
  `~/.cache/evolution/mail/<account-hash>/folders/<Folder>/cur/<2-hex>/<uid>`
  - The `<account-hash>` directory is not stable across account reconfigurations. Pick the hash whose `folders/` subdirectories actually contain files (check `find ... -type f | wc -l`); empty trees are stale accounts.
  - Folders observed: `INBOX`, `Sent` (`Éléments envoyés` for the French account), `Archive`, `Drafts`, `Trash`, `Junk`.
- **Archives** — `~/.mail/` (Evolution/Thunderbird-style maildir):
  - `Archives/cur/` — 88k+ historical messages (`.eml` files)
  - `Junk/cur/`, `Trash/cur/`, `Unsent Messages/`
- Live INBOX is small; most history is in `Archives`. Check both when searching.

## Reading messages

- Each message is a raw RFC-822 `.eml` file. Header block: `sed -n '1,/^$/p'`.
- Extract overview fields: `grep -E '^(Date|From|To|Cc|Subject):'`.
- Vietnamese subjects are often MIME base64 (`=?utf-8?B?...?=`); decode with `base64 -d`.
- Body may be HTML-only; strip tags if the user wants plain text.
- Newst-first listing by file mtime: `find <dir> -type f -printf '%T@ %p\n' | sort -rn`.

## Conventions

- Present inbox summaries as a table: date, from, subject.
- Decode encoded subjects before showing them; note spam-looking messages instead of quoting their content.
- Mail is read-only for the agent: never move, delete, or modify files under `~/.mail/` or the Evolution cache.
- When the user says "latest mail" without a folder, read the live INBOX first.
