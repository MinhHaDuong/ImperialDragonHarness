---
name: project-upstream-rebaseline-recipe-drift
description: "The --rebaseline recipe in bench/upstream_catchup.py still prescribes README-row updates for a standing report dissolved on 2026-09-04, and lists 28 tickets while calling them 29; baseline moved to zoteus v1.20.2 (c386e83) on 2026-09-17 in PR #604"
metadata: 
  node_type: memory
  type: project
  originSessionId: 35d0f237-bff6-455b-9ad4-b2d00efc2a58
  modified: 2026-09-17T09:01:02.637Z
---

On 2026-09-17 the reviewed upstream baseline moved from v1.16.0 (4467663) to
v1.20.2 (c386e83) in PR #604, no ticket. Verdict of the row re-read: no
delivered requirement verdict moved; index schema generation 2 unchanged.

**Recipe drift, left unfixed (below the severity floor):**
- `python3 bench/upstream_catchup.py --rebaseline` still tells the operator to
  update README standing rows, bars and tallies, and says `make check` fails
  until the page names the release. The README standing report was dissolved
  on 2026-09-04 (DECISIONS entry "the README stops tracking completed design
  work"); `make check` no longer gates on the version. The rows are still
  worth re-reading into `verification/UPSTREAM-<v>-REREAD.md`, which is what
  PR #604 did.
- The 2026-09-17 run listed 28 tickets under "tickets/" while prose said 29.
- Upstream's withdrawal of the zotero#6012 mean-vector citation (3a1e942) is
  partial: the same citation still stands on `packCode()`'s docstring in
  `sqlite-index.ts`. SPEC.md now says so.

**Why:** the next rebaseline will read the recipe as authoritative and go
looking for README rows that do not exist, or skip the re-read because the
gate it names no longer fires.

**How to apply:** at the next `TOUCHED` catch-up, treat the README lines of
the recipe as stale, do the REREAD file anyway, and fix the recipe text in
the same PR if the move is small enough to carry it. Smoke at the new SHA
needs `make upstream-checkout` first; the R23 restamp fails read-only under
the account posture (instrument fault, seen 2026-09-17) and R10-no-egress
shows the same 4 local-resolver connects as at 1.13.0, undiagnosed.

Related: [[project-zoteus-ladder-goal1-status]], [[feedback-refreshing-is-not-copying-forward]].
