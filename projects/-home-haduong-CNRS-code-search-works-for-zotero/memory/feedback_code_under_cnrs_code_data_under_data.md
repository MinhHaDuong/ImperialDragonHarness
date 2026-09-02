---
name: code-under-cnrs-code-data-under-data
description: "Filesystem layout on the author's machines — git checkouts under ~/CNRS/code/, measurement data under ~/data/projets/; a fork clone is code"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 10ff81b6-272d-48c9-ad4c-0fbd7153aec2
  modified: 2026-09-01T09:21:50.160Z
---

Setting up padme (2026-09-01), the fork clone was placed beside the measurement
substrates at `~/data/projets/zoteus-bench/fork-0091`, mirroring where it happened to
sit on doudou. The author corrected: "Code does not live under ~/data/ my friend." The
clone moved to `~/CNRS/code/zoteus`.

**Why:** `~/CNRS/code/` is the home of every git checkout; `~/data/projets/` holds the
big regenerable or measured artifacts (indexes, vectors, corpora). A fork is code, even
when it exists only to serve a bench campaign. Doudou's own `fork-0091` under
zoteus-bench is a tolerated wart, not a precedent.

**How to apply:** when provisioning any of the author's machines, clone repositories
under `~/CNRS/code/<name>` and point drivers at data under `~/data/projets/<name>`;
keep data paths identical across machines so recorded artifact paths stay valid.
