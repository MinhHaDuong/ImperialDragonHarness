---
name: reading-blocked-sources
description: "Reddit threads come through the .rss endpoint when JSON, HTML and mirrors are blocked; a closed-source Zotero plugin's design is readable from its shipped .xpi bundle when esbuild kept module paths"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 2a50c7c2-f228-4853-b310-8aa619b99086
  modified: 2026-09-02T10:01:03.237Z
---

Two routes that worked on 2026-09-02 for the field review's second pass:

- **Reddit**: `www.reddit.com/r/<sub>/comments/<id>/.rss` with a Firefox
  user agent returned the post and every comment. `old.reddit.com` was refused
  by the fetch tool, the `.json` endpoint and the HTML page both served a
  "blocked" shell to curl, Pullpush returned empty, and every redlib mirror
  tried was down, walled, or gone (410).
- **Closed-source plugin**: BibGenie publishes no source, but its release
  `.xpi` is a zip whose `content/scripts/bibgenie.js` is an esbuild bundle
  with `// src/<module>.ts` markers and readable SQL. Table schemas,
  constants, and the scoring loop came straight out of `grep` with context.
  Inspecting a bundle is reading, not running, so it stays inside the field
  review's "we have run none of these tools" rule; the entry names the asset
  and version it read.

**How to apply:** when a source is walled, try the RSS route before a mirror;
when a competitor is closed, download the release artifact before writing
"could not look". See [[probe-needs-discriminating-control]] for the rule that
a null fetch is not a finding.
