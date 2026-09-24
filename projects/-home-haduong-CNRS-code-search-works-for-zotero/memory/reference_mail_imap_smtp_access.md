---
name: mail-imap-smtp-access
description: The author's mailboxes (Ouvaton minh@haduong.com, CNRS minh.ha-duong@cnrs.fr) are reachable from the shell via curl --netrc; credentials mirrored from Evolution's keyring into ~/.config/keys/netrc on 2026-09-15.
metadata:
  type: reference
---

Four `machine` entries in `~/.config/keys/netrc` (symlinked from `~/.netrc`, mode 600), copied from the GNOME keyring where Evolution stores them (`secret-tool lookup e-source-uid <uid>`; uids in `~/.config/evolution/sources/*.source`):

- imap.ouvaton.coop and smtp.ouvaton.coop (port 465, implicit TLS) for minh@haduong.com
- imap.cnrs.fr and smtp.partage.renater.fr (port 587, STARTTLS) for minh.ha-duong@cnrs.fr, IMAP/SMTP login is the ods.services alias

Read: `curl -s --netrc --url imaps://imap.ouvaton.coop/ -X 'STATUS INBOX (MESSAGES UNSEEN)'`, or `imaps://host/INBOX;UID=N` for a message. Send: `curl --netrc --ssl-reqd --url smtp://smtp.partage.renater.fr:587/ --mail-from ... --mail-rcpt ... -T msg.eml`. Verified 2026-09-15: IMAP STATUS and SMTP `235 Authentication successful` on all four.

Evolution's own local cache (headers in a sqlite `folders.db`, bodies as maildir) sits under `~/.cache/evolution/mail/<account-uid>/` and is readable without the network. A third IMAP account, haduong@centre-cired.fr (imap.centre-cired.fr), exists in Evolution but was not mirrored. Never print the netrc or the secret-tool output.
