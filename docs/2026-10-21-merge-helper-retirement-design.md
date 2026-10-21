# Retiring `erg-pr-merge`: design note and edge cases

Status: **draft for author review**, nothing implemented. Written 2026-10-21 in an
Imagine session; no code or test was changed. Prices are estimates, not measurements.

## Why this note exists

`tests/test_erg_pr_merge.sh` is the slowest single item in `make check` (32 s under
4-worker load of a 353 s run; measured once, `pytest --durations`). The helper it
guards, `skills/merge/erg-pr-merge`, is 742 lines; its suite is 1,544. Dozens of
closed tickets (0138 … 1152) are fixes to it. Question asked: do we need the
helper to merge on GitHub at all?

## What the helper does today (read from the script, not run)

| Duty | Where |
|---|---|
| Parse close claims from the PR **body** (`**Ticket:**`, `Ticket-ref:`, `Ticket: NNNN`, `Ticket: none`, CommonMark fence tracking) | Step 1 |
| Cross-check claims against the branch tip (force-replaced branch, PR #522) | Step 1.5 |
| `erg close` + commit + push when the ticket is not yet closed on the branch | Step 2 |
| Auto-ready a draft PR; queue `gh pr merge --merge --auto`; fallback when auto-merge is refused (protection inspection, 18 test scenarios) | Step 3 |
| `--merge` always (merge commits), `--match-head-commit`, `--delete-branch` outside worktrees | Step 3 |
| Sync local main after the merge lands (`scripts/sync-local-main.sh`) | Step 4 |

Its only irreducible job is the **link between a PR and a ticket's closure**.
Everything else is `gh pr merge --auto --merge` plus forge behaviour.

## Decisions taken by the author (this session)

1. No forge-side CI check. 2. No agent hook. 3. No runbook teaching agents `gh`.
4. Put the claim check in the end-of-work checks (`make check`, `/verify-gate`),
   and verify at `/lair` time.

## Design

**The claim source moves from the PR body to the branch.** Today the body is a
grammar (fences, short forms, bold or bare) and most of the helper's tests pin that
grammar. Instead: a ticket branch `t{N}-…` *is* the claim that ticket N closes with
this work.

| Layer | When | Check | Cost |
|---|---|---|---|
| A. `make check` | before the PR | branch `t{N}-…` ⇒ `tickets/closed/N-*.erg` exists at head, unless the diff is tickets-only (see E1) | ~1 h, file reads only, ms |
| B. `/verify-gate` | on the PR | extend the existing dangling-claim rule: claimed ticket closed at head | ~1 h |
| C. `/lair` step 8 | end of day | `skills/roar/check-close-claims.sh` (exists, tested), plus a **branch join** (D1) | ~0.5 h |
| D. Retire | after one observed cycle | delete helper, 3 suites, `/merge` runbook; fix ~25 call sites; replace allow rule | ~3–4 h |

Closing moves from **merge time** to **authoring time**. This reverses a standing
memory note (`feedback_dont_pre_close_ticket_in_execution`: "leave the ticket open,
let erg-pr-merge close it"). The script already tolerates pre-closed tickets (its
Step 2 comment calls that "the normal case after close-before-gating", ticket
1153b), so the two practices coexist today; the note records the flip so the
memory is updated when D lands.

## Edge cases

### E. Ticket-only changes

| # | Case | What happens | Gap / decision |
|---|---|---|---|
| E1 | PR touches only `tickets/` (new tickets, annotations, e.g. `explore-velocity` filing four tickets) on a branch named `t{N}-…` | A would demand N closed, which is wrong for an annotation | **Decide**: exempt tickets-only diffs from A. Ticket 0159 already used `git diff -- . ':(exclude)tickets/'` as the test. Cost of the exemption: a ticket whose deliverable *is* a ticket change stays open, visible and reversible (the 1081 doctrine) |
| E2 | Branch closes *other* tickets (roar wrap-up, molt, tracker closure pass) | Branch is not `t{N}`; A no-ops; nothing verifies those closures | Out of scope; same as today |
| E3 | Direct push of erg-only branches (ticket 0159) | Gone: `rules/git.md` says no direct-push path | None, but 0159's premise is dead; note it when D lands |
| E4 | Parallel PRs touching the same `tickets/` files | Closing early widens the window for archive-move conflicts (`check-cross-pr-ticket-collision.sh`, memory `erg_close_bookkeeping_conflict`). Today the helper closes at merge, on the freshest base | **Real cost of the design.** Measure how often it bites before D; mitigation is rebase-then-close as the last commit |
| E5 | `.idh-checks.json` scoped gate | A must be in the always-run set, or a ticket-only PR skips it (fine by E1) | This repo has no `.idh-checks.json`; check other repos |

### H. Hotfixes

| # | Case | What happens | Gap / decision |
|---|---|---|---|
| H1 | Hotfix, no ticket, PR | Branch is not `t{N}`; A no-ops; merge needs no claim. Matches the 1081 decision (no line ⇒ closes nothing) | None. The severity floor (`workflow.md`) says a fix to a red `main` needs no ticket |
| H2 | Hotfix, **no PR** | `main` has no direct-push path; only the manuscript-prose exception commits to `main`. Every layer here keys on PRs, so it is invisible | Accept for prose repos; **decide** whether an admin-bypass merge is ever legitimate. The helper never allowed it either, I did not verify how it fails |
| H3 | Hotfix to an area of a ticket that is still open | Branch name decides; if named `t{N}` it must close N | Name the branch by what it is (`fix-…`), not by the neighbouring ticket |
| H4 | Hotfix while checks are red | Forge required checks block; helper's fallback would too | Out of scope |

### D. Dead angles (nothing sees them)

| # | Angle | Why nothing sees it | Mitigation |
|---|---|---|---|
| D1 | **PR with no body claim** | `check-close-claims.sh` joins *from claims*, so it cannot see it (ticket 1081 states this). Measured on 400 PRs, 24 days: close claim 196, `Ticket: none` 155, `Ticket-ref` 86, no ticket text 16 | Add a join from the other side: merged PRs whose head branch is `t{N}-…` and whose ticket N is still open on main |
| D2 | **Branch names are not a reliable claim** | Remote branches include `t-<slug>` (no number: `t-wake-clause-…`, `t-dedupe-checks-…`) beside `t{N}-…` (about 25 numbered, a small sample of live branches) | Either enforce `t{N}` on ticket work or keep the body-claim sweep alive alongside the branch join. **During transition there are two claim sources that must agree** |
| D3 | Multi-ticket PRs (raid waves) | Branch name carries one N | `workflow.md` says one ticket per PR unless they land together; A can check every ticket *touched* in the diff instead of the name |
| D4 | **Merge method** | Helper always passes `--merge`; a bare `gh pr merge --squash` loses the strategic merge commit and the roar attribution (memory `squash_merge_loses_roar_attribution`) | `/lair` sweep asserts merged PRs landed as two-parent merge commits (verification only, no forge setting) |
| D5 | **Local main sync** | Helper runs `sync-local-main.sh` when the merge lands; `rules/git.md` says "run … after `/merge`" | Move the duty to `/roar` or `/lair`; otherwise local main drifts |
| D6 | Merged outside any session (web UI, another machine) | A, B never ran | Only C sees it, and only within its window |
| D7 | Sweep cadence | `--days 7` window; if `/lair` is skipped for a week the leak ages out | Window longer than lair cadence, or record last-run |
| D8 | Branch force-replaced after A ran (PR #522) | The helper's tip cross-check disappears | C's branch join sees it afterwards |
| D9 | Two sessions on one ticket (`t{N}-{pid}`) | Both pre-close ⇒ duplicate archive moves ⇒ conflict on second merge | Same shape as today; first merge wins |
| D10 | Non-harness repos (cross-repo raid, `-C PATH`) | A lives in this repo's `make check`; the others have no such test | Ship A as a template, or accept sweep-only there. **Decide** |
| D11 | Wrong closure (exit criteria unmet) | Not helper's job; `/verify-gate` owns it | Pre-closing makes it visible earlier; unchanged otherwise |

## Not a concern (checked)

- I found no live hook that blocks a literal `gh pr merge` in a worktree
  (`block-pr-merge-in-worktree.sh` appears only in closed tickets), so removing the
  script does not newly trip a guard.

## Prices and risk (estimates)

- Total ~6–7 author-hours, ~$15–20 agent time; removes ~2,300 lines and ~32 s/CI run
  plus the helper's maintenance stream.
- Probability the folded check plus sweep catches the dropped-claim class: ~70%.
  The residual failure is an open ticket: visible, reversible.
- Largest unmeasured risk: E4 (conflict window). Second: D2 (naming).

## Open decisions for the author

1. E1: exempt tickets-only diffs from A?
2. H2: is any no-PR merge to `main` legitimate besides prose?
3. D2/D3: enforce `t{N}` naming and one-ticket-per-PR, or keep the body-claim sweep?
4. D10: ship the check to other repos, or accept sweep-only there?
5. D5: which skill takes over the post-merge local sync, `/roar` or `/lair`?
6. Keep `erg-pr-status` (one-shot status read) after D?
7. Order: A–C first, observe one cycle, then D. Agreed?

## Staging if approved

Tracker plus children A–D, D `Blocked-by` A–C, tracker closed after the integration
review (`/roar` step 8). Nothing is filed until the author says so.
