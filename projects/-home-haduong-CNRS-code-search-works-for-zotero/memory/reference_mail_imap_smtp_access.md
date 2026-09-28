---
name: mail-imap-smtp-access
description: Mail is reachable from the shell via curl --netrc (all four IMAP/SMTP endpoints verified 2026-09-15); hosts, logins, and credential locations are tier-2 data in the private overlay.
metadata:
  type: reference
---

The author's mailboxes are reachable from the shell via `curl --netrc`,
credentials mirrored from Evolution's keyring into `~/.config/keys/netrc`
(mode 600) on 2026-09-15. Four machine entries cover the personal and the
professional account, for both IMAP (read) and SMTP (send).

Hosts, ports, login aliases, and the keyring-extraction procedure are tier-2
personal data and live in the private mail skill,
`~/.config/harness/private/skills/email/SKILL.md` — not in this public repo.
Read that file for the exact endpoints and command lines
(`curl -s --netrc --url imaps://<host>/ -X 'STATUS INBOX ...'` for status,
`imaps://<host>/INBOX;UID=N` for a message, `--mail-from/--mail-rcpt/-T` for
sending). Verified 2026-09-15: IMAP STATUS and SMTP `235 Authentication
successful` on all four.

Evolution's own local cache (headers in a sqlite `folders.db`, bodies as
maildir) sits under `~/.cache/evolution/mail/<account-hash>/` and is readable
without the network. A third, legacy IMAP account exists in Evolution but was
not mirrored. Never print the netrc or the secret-tool output.
