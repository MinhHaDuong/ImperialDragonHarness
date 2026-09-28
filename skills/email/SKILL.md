---
name: email
description: "Read local mail (Evolution cache, ~/.mail archives) and send via msmtp CLI. Load when the user asks to read, search, summarize, reply-draft, or send their email/inbox, or mentions mail messages."
user-invocable: true
---

# Email — reading local mail from files

There is no mail connector. All mail lives on disk in maildir-style layouts and is read with `bash` + `read_file`.

## Accounts and mail flow

- **Professional**: minh.ha-duong@cnrs.fr — Evolution IMAP `imap.cnrs.fr:993` (login minh.ha-duong@ods.services); sends via `smtp.partage.renater.fr:587`. This is the French-UI account in the Evolution cache.
- **Personal**: minh.haduong@gmail.com — received by Gmail, which redirects everything to the ouvaton server (Received chain shows google → ouvaton.org, `Delivered-To: minh@haduong.com`).
- **Ouvaton mailbox**: minh@haduong.com — Evolution IMAP `imap.ouvaton.coop:993`; msmtp sends as this address via `smtp.ouvaton.coop:465`.
- Legacy accounts (ha-duong.minh@orange.fr, haduong@centre-cired.fr) exist in Evolution sources but are stale in the cache.
- **Flow**: mail is archived locally and deleted from the CNRS and ouvaton servers — the local archives are the primary history for those accounts. Google servers keep a copy of all personal mail.

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
- Newest-first listing by file mtime: `find <dir> -type f -printf '%T@ %p\n' | sort -rn`.

## Sending

CLI transport is `msmtp`, configured in `~/.msmtprc`:

- Default account `ouvaton`: `smtp.ouvaton.coop`, port 465 (implicit TLS), auth on, `from minh@haduong.com`.
- `~/.msmtprc` contains credentials: never read, display, or edit that file; msmtp reads it itself. Same for `~/.msmtp.log` — it records sends, check it for delivery errors.
- Send a drafted message (recipients taken from To/Cc/Bcc headers): `msmtp -t < draft.eml`
- Send body text to one address: `printf 'body' | msmtp dest@example.com`
- Sending is an external, hard-to-undo effect: always show the user the full draft (headers + body) and get explicit confirmation before running msmtp.
- Sent messages are stored server-side (IMAP Sent) and appear in the Evolution cache only after sync — do not expect them in local files immediately.

## Conventions

- Present inbox summaries as a table: date, from, subject.
- Decode encoded subjects before showing them; note spam-looking messages instead of quoting their content.
- Local mail stores are read-only for the agent: never move, delete, or modify files under `~/.mail/` or the Evolution cache. Sending goes through msmtp only, never by writing into mail stores.
- When the user says "latest mail" without a folder, read the live INBOX first.
