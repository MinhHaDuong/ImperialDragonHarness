---
name: reference-nextcloud-tasks
description: "How to work with the author's Nextcloud tasks and contacts over CalDAV/CardDAV — behavior and pitfalls; access details are private (tier-2)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4f38ce30-21e6-43a5-9b5b-36131219140c
  modified: 2026-08-10T18:53:40.649Z
---

The author's task list and address books live on a personal Nextcloud instance,
reachable over CalDAV/CardDAV from doudou. Server URL, account, credential
location, and endpoints are tier-2 personal data — they are deliberately NOT
recorded here.

Behavioral knowledge that does not depend on the specifics:

- The tasks instance accepts VTODO on one calendar only; the other calendar
  (birthdays) accepts only VEVENT. Create a task with a PUT of a VTODO on
  `.../<list>/<uuid>.ics` (expect HTTP 201). Verified 2026-08-10.
- Nextcloud does not reliably notify on VTODO VALARMs; for a real reminder,
  double the task with an email or a cron.
- CardDAV: search via REPORT `addressbook-query` with `prop-filter name="FN"`;
  create/merge via PUT/DELETE of individual `.vcf`. Before any mass mutation,
  take a full backup first (a dedup pass ran 2026-08-10).
- Two keyring items may match the credential's lookup prefix while only the
  first is valid (the second gives 401) — iterate and stop at the first that
  authenticates, with a `raw.decode()` fallback if the stored value does not
  decode as expected. Never display the credential.
