---
name: deploy-root-content-retirement
description: How to decide keep-vs-retire for served-but-unreferenced deploy-root content on the homepage.
metadata: 
  node_type: memory
  type: project
  originSessionId: 0cda7768-577a-43b3-8a82-679d31d99a91
---

The homepage deploy root (`~/CNRS/html`, mirrored to `/httpdocs/` by `make
sync`) accumulates legacy dirs that are served live but referenced by nothing the
generator emits. Before retiring any such dir, run two checks — "0 in-tree
references" is NOT sufficient grounds to delete:

1. **External-citation check.** Is the URL cited outside the tree? `Lacq_CCS_Pilot/`
   is KEPT because the published 2013 report cites its URLs, despite 0 in-tree refs.
2. **Source-backup check.** Is the content a derivative whose source is filed
   elsewhere? `page/recap_2020/` was retired (commit 5e960fc) because it was a 2020
   "Voeux" greeting whose source lives in `~/Media/Pictures/2020/` — personal
   content that belonged in `Media/`, not under CNRS, and deliberately not in Google.

Retirement procedure (both sides): delete server-side over FTP
(`lftp -e 'rm -r /httpdocs/<dir>; ...'`), confirm the URL 404s and the homepage
still 200s, remove the local copy, drop the dir's line from `.gitignore` (these
dirs are gitignored, so only that line is a tracked change), commit, push padme.

Open candidate: `CleanED-blog-archive/` (ticket 0025) — same shape, not yet
assessed. The recurring drift is tracked by [[homepage-backup-push]] sessions; a
standing drift-detector test is ticket 0026.
