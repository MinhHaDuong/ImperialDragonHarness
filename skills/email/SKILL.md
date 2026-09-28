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
  - Several account trees exist; the `<account-hash>` is not stable across account reconfigurations. More than one tree can be active at a time (CNRS and ouvaton both are) — when searching live mail, iterate over ALL trees whose `folders/` contain files (`find ... -type f | wc -l` per tree), not just one.
  - Folders observed: `INBOX`, `Sent` (`Éléments envoyés` for the CNRS account), `Archive`, `Drafts`, `Trash`, `Junk`. Fresh, unprocessed mail lands in the sibling `new/` directory before Evolution moves it to `cur/` — check both.
- **Archives** — `~/.mail/` (Evolution/Thunderbird-style maildir):
  - `Archives/cur/` — 88k+ historical messages (`.eml` files)
  - `Junk/cur/`, `Trash/cur/`, `Unsent Messages/` — check Junk before declaring an expected message missing (spam filtering is imperfect).
- Live INBOX is small; most history is in `Archives`. Check both when searching.

## Reading messages

- Each message is a raw RFC-822 `.eml` file. Header block: `sed -n '1,/^$/p'`.
- Extract overview fields: `grep -E '^(Date|From|To|Cc|Subject):'`.
- Vietnamese subjects are often MIME base64 (`=?utf-8?B?...?=`); decode with `base64 -d`.
- Body may be HTML-only; strip tags if the user wants plain text.
- Newest-first listing by file mtime: `find <dir> -type f -printf '%T@ %p\n' | sort -rn`. Filenames are unreliable as dates (epoch-ms for some, IMAP UIDs for others) — for chronology, use the `Date` header, not the filename or mtime.

## Sending

CLI transport is `msmtp`, configured in `~/.msmtprc`:

- Only the personal identity is wired for CLI sending: default account `ouvaton`, `smtp.ouvaton.coop:465` (implicit TLS), auth on, `from minh@haduong.com`. There is no CNRS account in msmtp — never send professional mail (minh.ha-duong@cnrs.fr) via CLI; CNRS mail is sent from Evolution, whose SMTP is `smtp.partage.renater.fr:587`.
- `~/.msmtprc` contains credentials: never read, display, or edit that file; msmtp reads it itself. Same for `~/.msmtp.log` — it records sends, check it for delivery errors.
- Send a drafted message (recipients taken from To/Cc/Bcc headers): `msmtp -t < draft.eml`
- Send body text to one address: `printf 'body' | msmtp dest@example.com`
- Sending is an external, hard-to-undo effect: always show the user the full draft (headers + body) and get explicit confirmation before running msmtp.
- msmtp does NOT save a copy to the IMAP Sent folder — messages sent via CLI leave no trace server-side. To keep a copy, add `Bcc: minh@haduong.com` to the draft (the redirection then delivers it back to the ouvaton INBOX).
- The CLI path is plain-text single-part only: no attachments, no MIME alternatives. Do not improvise multipart construction; if the user asks for attachments, tell them to send from Evolution.

## Conventions

- Present inbox summaries as a table: date, from, subject.
- Decode encoded subjects before showing them; note spam-looking messages instead of quoting their content.
- Local mail stores are read-only for the agent: never move, delete, or modify files under `~/.mail/` or the Evolution cache. Sending goes through msmtp only, never by writing into mail stores.
- When the user says "latest mail" without a folder, read the live INBOX of every active account tree, not just one.
- The cache shows only what Evolution has already fetched; there is no way for the agent to trigger a sync. If Evolution has not run recently, say the local view may be stale instead of asserting a mailbox is empty.
- The Google copy of personal mail is NOT accessible from this machine. "Absent locally" is not "does not exist" for personal mail.
- Mail content is confidential: never pass it to external services (web search, third-party model APIs, paste sites) unless the user explicitly asks for that specific content to go there.
