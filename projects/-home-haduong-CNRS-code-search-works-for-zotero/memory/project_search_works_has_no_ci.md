---
name: project-search-works-has-no-ci
description: "search-works-for-zotero runs NO CI — there is no .github/ in the tree, so the validate-tickets and cross-pr-ticket-collision jobs the harness AGENTS.md describes never fire here; a hand-run make check is the only gate"
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-10T10:36:00.692Z
  originSessionId: eded38a7-e9ed-4e8d-a223-47b5877c1920
---

This repository has **no continuous integration at all**. Verified 2026-09-10:
no `.github/` anywhere in the tree, no `scripts/`, and `statusCheckRollup` is
empty on every PR. Independently confirmed the same day by a Sonnet reviewer.

The harness's global `tickets/AGENTS.md` describes two jobs as running "on every
push and PR" — `validate-tickets` (`erg check tickets/`) and
`cross-pr-ticket-collision` (`scripts/check-cross-pr-ticket-collision.sh`).
**Neither exists here.** That text describes a convention, not this repo. Same
situation as climate-finance-het, which declined CI by ruling (its ticket 0321).

**Why it matters:** `make check`, run by hand, is the entire gate. Nothing
re-runs it after a push, nothing blocks a merge on it, and `gh pr merge` /
`erg-pr-merge` will land a red branch without complaint. So:

- Run `make check` on **every** branch before pushing, including branches that
  only touch `tickets/` — `erg check` alone does not read log stamps, and that
  gap put an invented stamp on an open PR (see
  [[feedback-erg-log-stamp-must-match-wall-clock]]).
- The cross-PR ticket-ID collision trap has **no** automated guard. Enumerate
  open PRs and `gh pr view N --json files` per PR before allocating, and run
  `erg check` against `origin/main` **after** a merge — that post-merge run is
  the only check that can see a duplicate that already landed.
- Ticket 0763 (filed 2026-09-10) is the instance of this class inside the tree:
  two mutation probes that call themselves gates in their own docstrings, which
  `make check` never invokes. Their anchors rotted unnoticed for that reason.

Repo settings read the same day: merge commits allowed, squash allowed,
`deleteBranchOnMerge: true`.

Related: [[feedback-a-gate-without-the-button]], [[feedback-green-prs-red-union]].
