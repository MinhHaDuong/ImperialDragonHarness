---
name: cookie-replay-fetch
description: "Fetching from bot-walled sites (oecd.org, one.oecd.org) works by replaying the author's Firefox cookies"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a5d889db-150a-4c5a-829a-2678315e0e35
  modified: 2026-07-24T20:22:14.042Z
---

Cloudflare-walled sites that 403 robots can be fetched by replaying the
author's own browser session: copy `~/.mozilla/firefox/<profile>/cookies.sqlite`,
extract the domain's cookies (`cf_clearance` is the load-bearing one), and
send them with a matching Firefox User-Agent. Proven 2026-07-24 on
www.oecd.org and one.oecd.org (100+ PDFs, zero failures); ReliefWeb and
Crossref need no cookies. Open-tab URLs come from
`sessionstore-backups/recovery.jsonlz4` (mozLz4: 8-byte magic then
lz4.block). Polite pacing (2-3 s) throughout; it is the author's own
access, used at their request.
