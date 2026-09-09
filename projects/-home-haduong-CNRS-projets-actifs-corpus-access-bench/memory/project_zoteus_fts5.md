---
name: project-zoteus-fts5
description: Chantier replacing zoteus's resident JS search index with SQLite/FTS5 — repo, upstream state, and the measurements that motivate it
metadata:
  type: project
---

`~/CNRS/projets/actifs/zoteus-fts5` (public: MinhHaDuong/zoteus-fts5). Tickets,
benchmarks, and a `fork/` checkout of MinhHaDuong/zoteus (upstream
oscardvs/zoteus). Started 2026-08-21 from the question "can an LLM reach the
knowledge in a living directory".

**Why.** zoteus keeps its whole search index resident in JS objects and
snapshots it with one `JSON.stringify`. On a 7 540-item library: 5 370 MB
resident, a write that fails past V8's 512 MiB string limit, and an index a
stock Node cannot reload (OOM at the ~4 GB default heap, around 260 k
passages). No setting both writes and reads the library back. FTS5 over the
same corpus: 162 MB resident, 47 s to build, 762 MB on disk.

**Upstream, all open and unreviewed as of 2026-08-21**: issue #10 (persistence
ceiling, with SQLite proposed as direction (d) in a comment), PR #11
(configurable item cap + truncation notice), PR #12 (group libraries served
locally on Zotero 10). Posture agreed with the author: **prototype in the fork,
no merge request for the storage rewrite** until the maintainer arbitrates.

**Why the machinery differs from a normal project.** `/raid`'s merge step does
not apply — the merge decision belongs to a third party. `/gaze` and
`/verify-adherence` check against Python and prose rules that do not apply to a
TypeScript repo; the gate is upstream's own `vitest`/`tsc`/`eslint` **plus**
same-corpus-in/same-results-out against the current index, which is the check a
green suite cannot give. And no `tickets/` directory may ever appear in the
fork, or it rides along in a diff sent upstream.

Related: [[reference-zotero-fulltext-cache]], [[feedback-silent-ceiling-class]]
