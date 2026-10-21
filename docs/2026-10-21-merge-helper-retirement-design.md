# Retiring `erg-pr-merge`: design note and edge cases

Status: **draft v2 for author review**, nothing implemented. Written 2026-10-21 in an
Imagine session; v2 folds in an Opus review (facts corrected, a governing constraint
added). No code or test was changed. Estimates are judgment calls unless marked
measured; files were read, not run.

## Why this note exists

`tests/test_erg_pr_merge.sh` is the slowest item in a local `make check` (32 s, one
`pytest --durations` run under 4-worker load; a single local measurement). The helper,
`skills/merge/erg-pr-merge`, is 842 lines. Its three suites total 2,744 lines
(`test_erg_pr_merge.sh` 1,544, `_gate.py` 282, `_preflight_settles.sh` 76), plus
`test_close_claim_grammar.sh`, which runs the helper as a fixture. Dozens of closed
tickets (0138 to 1152) are fixes to it. Question asked: do we need the helper to
merge on GitHub?

## The governing constraint: the helper is the merge gate (tracker 1045)

The author disabled the forge ruleset `main-required-checks` on 2026-10-21, and CI has
no `pull_request` trigger (ticket 1174). Ticket 1045's log says the gate record of
child 1156 is now **the only merge check**, and the helper is where it is enforced:
when the base carries `.merge-gate.json` with gate=on, Step 3 reads the latest
`refs/notes/gate` record on the candidate merge commit (`scripts/merge-gate.py`),
refuses on fail, and requires tip equality (`erg-pr-merge:31-37`, 148-162). Children
1157, 1158 and 1171 are still open.

So "delete the helper, merge with bare `gh pr merge --auto`" would merge with **no
check at all**. Retirement is blocked on 1045, or on moving the gate enforcement
somewhere else. With forge CI and agent hooks ruled out, the enforcement point must
remain a local command that agents call to merge.

## What the helper does today

| Duty | Where |
|---|---|
| Parse close claims from the PR **body** (`**Ticket:**`, `Ticket-ref:`, `Ticket: NNNN`, `Ticket: none`, CommonMark fence tracking) | Step 1 |
| Cross-check claims against the branch tip (force-replaced branch, PR #522) | Step 1.5 |
| `erg close` + commit + push when not already closed on the branch; strip `Blocked-by:` on dependents | Step 2 |
| **Enforce the gate record** (`.merge-gate.json`, ticket 1156) | Step 3 |
| Auto-ready a draft PR; queue `gh pr merge --merge --auto`; fallback when auto-merge is refused (protection inspection, 18 test scenarios) | Step 3 |
| `--merge` always, `--match-head-commit`, `--delete-branch` outside worktrees | Step 3 |
| Sync local main after the merge lands | Step 4 |

Callers rely on more than the merge: raid Phase 7 uses `-C PATH`, three-way tip
equality (`HEAD == origin/<branch> == ruled_tip_sha`), `erg-pr-status` exit codes 0 to 3
and the merge-permission-denial section (`raid/SKILL.md:423-441`).
`scripts/enumerate-merges.py` recovers each merge's ticket from the helper's exact
close-commit text, `ticket(N): close and archive — PR #N`, and refuses branch names
because they "carry misleading digits" (`enumerate-merges.py:12-15, 38-47`); that feeds
`attribution_query.py`. About 27 live files reference the helper.

## Two ways forward

**D-delete**: remove the helper, its suites and the `/merge` runbook. Only possible
after 1045 lands a gate enforcement that does not live in the helper. The other costs
below apply in full.

**D-slim (recommended)**: keep a thin `erg-pr-merge` of roughly 100 lines whose duties
are the gate record check, `gh pr merge --merge --auto` and the local sync. Drop the
body-claim grammar parsing at merge time, the protection-inspection fallback (18
scenarios) and the cosmetic-failure/race handling. The suites shrink to a handful of
cases. This keeps one enforcement point and keeps `-C`, tip equality and
`erg-pr-status` for raid, and removes most of the 2,744 lines. It does not need the
claim source to move. Estimated cost 4 to 6 author-hours; the savings are a
judgment (about two thirds of the lines and the slow suite), not a measurement.

The rest of this note covers the claim check, which both options need.

## Claim check design (layers A to C)

| Layer | When | Check | Open point |
|---|---|---|---|
| A. gate-time check | when `/verify-gate` or raid runs, **not** every `make check` | the ticket the PR claims is in `tickets/closed/` **with a `Closed:` header** at the ruled tip | Running it in every `make check` turns red during ordinary work on a `t{N}` branch until N is closed, which pushes toward the partial-work autoclose `lair/SKILL.md:55` warns about. The merge gate also builds a detached candidate commit (`merge-gate.py:4-10`), where a branch-name check cannot see the branch |
| B. `/verify-gate` | on the PR | extend its existing dangling-claim rule (`verify-gate/SKILL.md:404-408`) to "closed at tip" | Cheapest home for A |
| C. `/lair` step 8 | end of day | run `check-close-claims.sh` | Not wired today. Default `--limit 30` covers about 1.8 days at about 16.7 PRs/day (derived: 400 PRs/24 days), not the 7-day window. It does not audit short `Ticket: NNNN` claims (`merge/SKILL.md:290-291`) |

**Claim source.** The earlier draft moved the claim from the PR body to the branch name
and called it a simplification. It is not: gaze (`setup-and-breaker.md:20-21`),
verify-gate (`:403`) and `check-close-claims.sh` all parse the body "with the same
grammar as erg-pr-merge", so the grammar and its tests survive the helper. And
`enumerate-merges.py` already rejects branch-derived tickets. Recommendation: **keep
the body claim as the source**, and treat a branch-name join (D1 below) only as a
supplementary sweep signal, labeled approximate.

**Timing.** Closing happens before gating, not at merge. That is already the practice:
raid (`:425-428`) and verify-gate (`:404-407`) close before gating, and the script
treats it as "the normal case" (`:23-24`, ticket 1161). The memory note
`feedback_dont_pre_close_ticket_in_execution` is stale, not reversed; update it
when this lands.

## Edge cases

### E. Ticket-only changes

| # | Case | What happens | Gap / decision |
|---|---|---|---|
| E1 | PR touches only `tickets/` (filing, annotation) on a `t{N}` branch | A would demand N closed, wrongly | **Decide**: exempt tickets-only diffs (ticket 0159 used `':(exclude)tickets/'`). Cost: a ticket whose deliverable is a ticket change stays open, visible and reversible (the 1081 doctrine) |
| E2 | Branch closes other tickets (roar wrap-up, molt, tracker closure) | Branch is not `t{N}`; nothing verifies those closures | Not probed; assumed out of scope |
| E3 | Direct push of erg-only branches (0159) | Gone per `rules/git.md:7` | None |
| E4 | Parallel PRs touching the same `tickets/` files | Closing early widens the archive-move conflict window (`check-cross-pr-ticket-collision.sh`). A rebase onto a main that already holds the same move gives an add/add conflict on `tickets/closed/N-*`, and `hooks/pre-commit:16-22` skips validation during a rebase, so a bad resolution (file in both directories, duplicate header) commits unchecked | **Real cost.** The memory note `erg_close_bookkeeping_conflict` is named in `memory/.provenance.json` but I found no file, so the frequency is unmeasured. Measure before any cutover |
| E5 | `erg close` side effects | It strips `Blocked-by: N` and logs on dependents (`erg-pr-merge:490-494`). Closing at authoring time misses a dependent filed on main after the fork: it stays blocked by a closed ticket | Closing last, after rebase, narrows this. Decide who repairs |
| E6 | `.idh-checks.json` scoped gate | A must be in the always-run set | This repo has none; check other repos |

### H. Hotfixes

| # | Case | What happens | Gap / decision |
|---|---|---|---|
| H1 | Hotfix, no ticket, PR | Branch is not `t{N}`; no claim needed (the 1081 decision) | `workflow.md` files a ticket when a defect "blocks a merge", and says only to delay filing until your fix is pushed (the "red gate on main" paragraph). So a hotfix to a red `main` may owe a ticket; it is not exempt. **Decide** |
| H2 | Hotfix, **no PR** | `main` has no direct-push path except manuscript prose | **Decide** whether an admin-bypass merge is ever legitimate. How the helper behaves under bypass was not verified |
| H3 | Hotfix to an area of a still-open ticket | Branch name decides | Name it by what it is (`fix-…`) |
| H4 | Hotfix while checks are red | **Corrected**: no forge required checks block it now (ruleset disabled, 1045). The gate record is the only block | Same as the governing constraint |

### D. Dead angles

| # | Angle | Why nothing sees it | Mitigation |
|---|---|---|---|
| D1 | PR with no body claim | `check-close-claims.sh` joins from claims (1081). Counts from ticket 1081, 400 PRs, 2026-09-16..10-10, labeled derived there and **not re-measured**: close claim 196, `Ticket: none` 155, `Ticket-ref` 86, no ticket text 16 | Supplementary join: merged PRs whose head branch is `t{N}-…` with N still open. Approximate: `t-<slug>` branches exist without a number; "about 25 numbered" is a small, unverified sample |
| D2 | Two claim sources during transition | Body grammar and any branch join must agree | Keep the body as the source (above) |
| D3 | Multi-ticket PRs (raid waves) | One branch name, several tickets | Check every ticket the diff touches |
| D4 | Merge method | Helper always passes `--merge`; a bare `--squash` loses the merge commit and roar attribution (that memory note exists only in the search-works project, not here) | Under D-slim the thin helper still passes `--merge`. Under D-delete, a sweep asserts two-parent merge commits |
| D5 | Local main sync | Helper runs `sync-local-main.sh` after the merge | Keep it in the thin helper, or give it to `/roar` |
| D6 | Merged outside any session | A, B never ran | Only C sees it, within its window |
| D7 | Sweep cadence | Window and limit (see C) | Raise `--limit`, set the window above lair cadence, or record last run |
| D8 | Branch force-replaced after A | The tip cross-check goes | C sees it afterwards |
| D9 | Two sessions on one ticket (`t{N}-{pid}`) | Both pre-close, conflict on the second merge | Today the close happens at merge time on the branch tip, a narrower window, so this is **wider** than today |
| D10 | Non-harness repos (cross-repo raid) | Layers A and B live in this repo | Template or accept sweep-only |
| D11 | Wrong closure | `/verify-gate` owns it | Unchanged |
| D12 | **PRs already open at cutover** | Authors who followed the stale memory note have the ticket open plus a body claim; a bare merge drops the close, and C may not see it | Cutover must drain or close open PRs first; D-slim avoids this because the claim path is unchanged |
| D13 | **Attribution pipeline** | `enumerate-merges.py` keys on the helper's close-commit text; closing before a PR number exists changes or removes it | Check `attribution_query.py:234` before any change to Step 2 |
| D14 | Reused `t{N}` for follow-up on a long-closed ticket | A passes vacuously | Check the `Closed:` header date against the branch base |
| D15 | Rule text | `rules/git.md:23` ("Merge through `/merge`") and `rules/workflow.md:131` point to the runbook | Add to D's edit list |

## Prices and risk (estimates, no measurement behind them)

- A to C: about 2.5 author-hours (1 + 1 + 0.5). D-slim: 4 to 6. D-delete: 3 to 4 plus
  the blocked dependency. Total for A to C plus D-slim: about 6.5 to 8.5 hours. The
  earlier "6 to 7 h / $15 to 20 / 70%" had no basis and is withdrawn; treat the
  catch probability as unknown until C is wired and run once.
- No CI-time saving is claimed: CI no longer runs on PRs. The 32 s is local `make check`.
- Largest risks: the gate duty (above), E4 conflicts, D12 cutover, D13 attribution.

## Open decisions for the author

1. D-slim or D-delete? (Recommended: D-slim; D-delete waits on 1045.)
2. Keep the body claim as the source? (Recommended: yes.)
3. Run layer A at gate time only, or in `make check` with an in-progress exemption?
4. E1: exempt tickets-only diffs?
5. H1/H2: does a hotfix to a red `main` owe a ticket, and is any no-PR merge legitimate?
6. D10: ship layers A and B to other repos, or accept sweep-only there?
7. D5: keep the sync in the thin helper or move it to `/roar`?

## Staging if approved

Tracker plus children. Order: C first (smallest, already tested), then A/B, then D-slim,
`Blocked-by` 1157, 1158 and 1171 only where D-slim touches Step 3. The tracker closes after
the integration review (`/roar` step 8). Nothing is filed until the author says so.
