---
name: menagerie-build-state-2026-09-06
description: "Where the Menagerie one-shot build and the 0029 program stood when the 2026-09-06 session paused under token pressure; merged PRs, running lane, next steps"
metadata: 
  node_type: memory
  type: project
  originSessionId: a690b729-abc6-4ef5-a712-f0be4683c51b
  modified: 2026-09-06T20:09:52.164Z
---

Session "Reimagining the Menagerie", 2026-09-06, paused by the author under terminal token pressure.

**Merged to main:** PR #363 (design record, panel, rulings, DECISIONS.md 2026-09-06), #380 (library census, ticket 0711 closed), #381 (0632 export fix and the first real export, defects recorded), #406 (Library-level bench, ticket 0719 closed). Main at 6c73caf or later.

**Running when paused:** the one-shot Menagerie build lead (team-lead, worktree `agent-a03a1d56b31066157`, branch `t0029-menagerie-build`), told to push everything, mark PRs draft, log its position on ticket 0029 and stop. It was mid-injection on padme with two sourcing executors killed earlier by a rate limit. Check origin for branch `t0029-menagerie-build` and any `t0029-*` sourcing branches before resuming; read ticket 0029's last log line for its position.

**Next steps, in order:** review the build's draft PRs; re-injection of the fixture with explicit charset and stock-limit reindex, then re-export (owed to 0632); question bank and v2 scorer with the any-of/all-of flag; the RIS package; the SPEC pass (§5.2.10, caps sentence, "~40 queries" deletion, thresholds recalibrated, R29 widened for Vietnamese queries, README page-240 promise). Open for the author: whether the local API's 404 on text/plain full text goes upstream; the embedder name behind the cross-lingual near-zero the bench found.

**How to apply:** start the next session by reading ticket 0029's log tail and DECISIONS.md's 2026-09-06 entries; do not relaunch the build from scratch, resume from the pushed branches.
