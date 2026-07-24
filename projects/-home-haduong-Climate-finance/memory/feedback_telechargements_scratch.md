---
name: telechargements-scratch
description: ~/Téléchargements is scratch only — move downloaded files to durable storage immediately
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 352d5761-eab8-421e-8926-7931ba20d97f
  modified: 2026-07-24T09:14:35.856Z
---

The downloads directory ([[padme-downloads-dir]]) is NOT safe storage — treat
it as scratch.

**Why:** author directive 2026-07-24; downloads accumulate, get cleaned, and
carry meaningless browser filenames.

**How to apply:** as soon as a downloaded file is identified, copy it to its
durable home (pool dir, project data dir, Zotero staging), verify by checksum,
then delete the Téléchargements copy. Never reference a Téléchargements path
from any config or ticket.
