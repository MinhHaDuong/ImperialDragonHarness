# Retiring `erg-pr-merge`: design note and edge cases

Status: **draft v3 for author review**, nothing implemented. Written 2026-10-21 in an
Imagine session. v2 folded in an Opus review; v3 folds in Codex and Fable reviews
(see "Review trail"). No code or test was changed. Files were read, not run;
estimates are judgment calls unless marked measured.

**Superseded in part by ticket 1178** (the author's decision, 2026-10-21, to remove
the helper). Read the "blocked on 1045" premise and the D-delete/D-slim choice as
history. What stays useful is the edge-case tables, the fact checks and the review
trail; the findings that bear on 1178 are logged on the ticket.

## Why this note exists

`tests/test_erg_pr_merge.sh` is the slowest item in a local `make check` (32 s; one
`pytest --durations` run under 4-worker load, a single local measurement). The helper,
`skills/merge/erg-pr-merge`, is 842 lines. Its three suites total 1,902 lines
(`test_erg_pr_merge.sh` 1,544, `_gate.py` 282, `_preflight_settles.sh` 76); helper plus
suites is 2,744. `test_close_claim_grammar.sh` also runs the helper as a fixture. Dozens
of closed tickets (0138 to 1152) are fixes to it. Question asked: do we need the helper
to merge on GitHub?

## The governing constraint: the helper is the planned merge gate (tracker 1045)

**State today (verified):** the gate is off. `.merge-gate.json` is absent at
`origin/main` (267e1fc4); the activation commit 5586ee12 exists only on
`origin/t1156-activation`; ticket 1156 splits the machinery (#1564) from the activation
(#1569). The author disabled the forge ruleset `main-required-checks` on 2026-10-21,
and `CI.yml` has no `pull_request` trigger (ticket 1174; `ticket-collision.yml` does
have one, for the collision check only). So at this revision the helper's ungated route
arms `gh pr merge --auto` (`erg-pr-merge:776`), which with no required checks merges at
once: **no merge check runs today.**

**State intended:** ticket 1045's log says the gate record of child 1156 becomes the
only merge check, enforced in Step 3 of the helper: with gate=on, it requires the
latest `refs/notes/gate` record on the candidate (base tip plus head,
`scripts/merge-gate.py`), refuses on fail, and requires tip equality. Children 1157,
1158 and 1171 are open (1157's receive-side `hooks/reference-transaction` is partly
built, PR #1566; the author ruled out new hooks for this note, so it is context only).

So "delete the helper, merge with bare `gh pr merge --auto`" would drop the planned
check, and today it would drop nothing because nothing is enforced. Retirement is
blocked on the helper being the planned enforcement point, with forge CI and agent
hooks ruled out.

## What the helper does today

| Duty | Where |
|---|---|
| Parse close claims from the PR **body** (`**Ticket:**`, `Ticket-ref:`, `Ticket: NNNN`, `Ticket: none`, CommonMark fence tracking) | Step 1 |
| Cross-check claims against the branch tip (force-replaced branch, PR #522) | Step 1.5 |
| `erg close` + commit + push when not already closed on the branch; strip `Blocked-by:` on dependents | Step 2 |
| **Gated path** (gate=on): tip equality, `merge-gate.py check`, **disarm any armed auto-merge**, pinned `gh pr merge --merge --match-head-commit`, require the PR to read MERGED at the gated head | Step 3, `:723-767` |
| Ungated path: auto-ready a draft PR, queue `--merge --auto`, fallback when auto-merge is refused (protection inspection, 18 test scenarios) | Step 3 |
| Sync local main after the merge lands | Step 4 |

Callers rely on more than the merge: raid Phase 7 uses `-C PATH`, three-way tip equality
(`HEAD == origin/<branch> == ruled_tip_sha`), `erg-pr-status` exit codes 0 to 3 and the
merge-permission-denial section (`raid/SKILL.md:423-441`).
`scripts/enumerate-merges.py` recovers each merge's ticket from Step 2's exact
close-commit text, `ticket(N): close and archive — PR #N`, and refuses branch names
because they "carry misleading digits" (`:12-15, 38-47`); that feeds
`attribution_query.py`. About 27 live files reference the helper.

## Two ways forward

**D-delete**: remove the helper, suites and `/merge` runbook. Only possible once an
enforcement point other than the helper exists. Blocked by 1045.

**D-slim (recommended, to be respecified in ticket form)**: reduce the helper to the
**gated path** only. Required semantics, from `:723-767` and not negotiable:
fetch; three-way tip equality; `merge-gate.py check`; disarm any armed auto-merge;
pinned `--merge --match-head-commit`; confirm MERGED at the gated head; local sync.
It must **not** use `--auto`: an armed auto-merge could land a later head the record
does not cover (the helper's own comment, `:725-732`). The strongest counter-argument,
which does not win, is that the slow and large part (the 18 fallback scenarios, race
handling) is the *ungated* path, dead code once a base is gated; so the honest saving
is "delete the ungated path", not "a new 100-line helper". Order matters: the ungated
path is the live one until 1156 activates, so slimming comes **after** activation.

**Step 2 is a separate decision the draft hid.** Slimming away body parsing removes
`erg close` and the close commit. Either keep Step 2 in the thin helper, or accept that
D12 (PRs open at cutover) and D13 (attribution) become D-slim costs. Recommendation:
keep Step 2 until A to C have run for a cycle.

Estimated cost 4 to 6 author-hours; "about 100 lines" and "two thirds of the lines" are
guesses with no decomposition behind them.

## Claim check design (layers A to C)

| Layer | When | Check | Open point |
|---|---|---|---|
| A. gate-time check | when `/verify-gate` or raid runs, **not** every `make check` | the ticket the PR claims is in `tickets/closed/` **with a `Closed:` header** at the ruled tip | In every `make check` it turns red during ordinary work on a `t{N}` branch, pushing toward the partial-work autoclose `lair/SKILL.md:55` warns about. The gate builds a detached candidate commit (`merge-gate.py:4-10`), where a branch-name check cannot see the branch |
| B. `/verify-gate` | on the PR | extend its dangling-claim rule (`verify-gate/SKILL.md:404-408`) to "closed at tip" | Cheapest home for A |
| C. `/lair` step 8 | end of day | run `check-close-claims.sh` | Not wired today. Default `--limit 30` covers about 1.8 days at about 16.7 PRs/day (derived: 400 PRs / 24 days), not the 7-day window. Short `Ticket: NNNN` claims are unaudited (`merge/SKILL.md:290-292`) |

**Claim source: keep the body.** gaze (`setup-and-breaker.md:20-21`), verify-gate
(`:403`) and `check-close-claims.sh` parse the body "with the same grammar as
erg-pr-merge", so the grammar and its tests outlive the helper, and `enumerate-merges.py`
rejects branch-derived tickets. A branch-name join (D1) is a supplementary sweep signal
only.

**Timing.** Raid (`:425-428`) and verify-gate (`:404-407`) already close before gating,
and the script calls it "the normal case" (`:23-24`, ticket 1161). The memory note
`feedback_dont_pre_close_ticket_in_execution` and `lair/SKILL.md:55` describe the
older merge-time closing; update both when this lands.

## Edge cases

### E. Ticket-only changes

| # | Case | What happens | Gap / decision |
|---|---|---|---|
| E1 | PR touches only `tickets/` on a `t{N}` branch | A would demand N closed, wrongly | **Decide**: exempt tickets-only diffs (ticket 0159 used `':(exclude)tickets/'`). Cost: a ticket whose deliverable is a ticket change stays open, visible and reversible (1081 doctrine) |
| E2 | Branch closes other tickets (roar wrap-up, molt) | Not `t{N}`; nothing verifies those closures | Not probed |
| E3 | Direct push of erg-only branches (0159) | Gone per `rules/git.md:9` | None |
| E4 | Parallel PRs touching the same `tickets/` files | A rebase onto a main that already holds the same move gives an add/add conflict on `tickets/closed/N-*`; `hooks/pre-commit:16-22` skips validation during a rebase, so a bad resolution commits unchecked | **Real cost**; frequency unmeasured |
| E5 | `erg close` fan-out | It strips `Blocked-by: N` and logs on dependents (`erg-pr-merge:490-494`). Observed (aedist memory `feedback_erg_close_bookkeeping_conflict`, raid 419-420, 2026-06-04): two parallel closes of sibling blockers conflict in a **third** ticket's file, not in either closed ticket. A dependent filed on main after the fork stays blocked by a closed ticket | Close last, after rebase; decide who repairs |
| E6 | `.idh-checks.json` scoped gate | A must be in the always-run set | This repo has none; check other repos |
| E7 | Tracker-close PRs (`/roar` closes trackers only after integration review, `roar/SKILL.md:144`) | A ticket-only tracker close can merge with no evidence the review ran | Define that path explicitly; do not let E1's exemption cover it |

### H. Hotfixes

| # | Case | What happens | Gap / decision |
|---|---|---|---|
| H1 | Hotfix, no ticket, PR | Not `t{N}`; no claim needed (1081 decision) | `workflow.md` files a ticket when a defect "blocks a merge" and only says to delay filing until your fix is pushed; a hotfix to a red `main` may owe one. **Decide** |
| H2 | Hotfix, **no PR** | `main` has no direct-push path except manuscript prose | **Decide** whether an admin-bypass merge is legitimate. Helper behaviour under bypass not verified |
| H3 | Hotfix in the area of a still-open ticket | Branch name decides | Name it by what it is (`fix-…`) |
| H4 | Hotfix while checks are red | No forge check blocks it now (ruleset disabled). Once the gate is on, the gate record is the only block | See governing constraint |

### D. Dead angles

| # | Angle | Why nothing sees it | Mitigation |
|---|---|---|---|
| D1 | PR with no body claim | `check-close-claims.sh` joins from claims (1081). Counts are from ticket 1081 (400 PRs, 2026-09-16..10-10, derived there, **not re-measured**): close claim 196, `Ticket: none` 155, `Ticket-ref` 86, no text 16 | Supplementary join on `t{N}-…` branches; approximate, since `t-<slug>` branches exist without a number |
| D2 | Two claim sources | Body grammar vs any branch join | Body stays the source |
| D3 | Multi-ticket PRs (raid waves) | One branch name, several tickets | Check every ticket named in a **close claim**; annotations and dependency edits are not claims |
| D4 | Merge method | A bare `--squash` loses the merge commit and roar attribution (that memory note lives in the search-works project, not here) | The thin helper still passes `--merge`; under D-delete, a sweep asserts two-parent merge commits |
| D5 | Local main sync | Helper runs `sync-local-main.sh` | Keep in the thin helper or move to `/roar` |
| D6 | Merged outside any session | A, B never ran | Only C sees it |
| D7 | Sweep cadence | Window and limit (see C) | Raise `--limit`; window above lair cadence; record last run |
| D8 | Branch force-replaced after A | Tip cross-check goes | C sees it afterwards |
| D9 | Two sessions on one ticket (`t{N}-{pid}`) | Both close early, conflict on the second merge | Sessions that today leave closing to the merge are narrower; sessions that already close before gating are unchanged. Wider only for the former |
| D10 | Non-harness repos | A and B live here | Template or accept sweep-only |
| D11 | Wrong closure | `/verify-gate` owns it | Unchanged |
| D12 | PRs already open at cutover | Authors who followed the stale memory note have the ticket open plus a body claim; a merge that no longer runs Step 2 drops the close | Drain or close open PRs first, or keep Step 2. **Revalidate every open PR including already-APPROVED ones**: today Step 2 closes and exits 2 when the head changes (`:454, :517-519`) |
| D13 | Attribution pipeline | `enumerate-merges.py` keys on Step 2's commit text | Keep Step 2's text, or check `attribution_query.py:234` first |
| D14 | Reused `t{N}` for follow-up on a long-closed ticket | A passes vacuously | Compare the `Closed:` date with the branch base |
| D15 | Rule text | `rules/git.md:23` ("Merge through `/merge`") and `rules/workflow.md:131` point to the runbook | Add to the edit list |
| D16 | **Serial merges under the gate** | The record is built on base tip plus head. After PR 1 of a raid wave merges, PR 2's check exits 2 ("a moved main needs a new record", `:745`), while verify-gate allows two rounds only (`SKILL.md:57-59`) and raid allows one re-gate (`raid:336/350`). Each later PR stalls or spends its re-gate on base movement, not on a fix | A pre-existing cost of the 1045 design that D-slim keeps. **Decide** whether a mechanical re-record on a moved base should consume a review round |
| D17 | **Two gates, one contract** | A passing mechanical record does not mean APPROVED review: `decide()` checks record completeness, scope and result (`merge-gate.py:129`); the review contract separately needs APPROVED on the exact remote head (`merge/SKILL.md:194`). Closed ticket + passing record + REROLL verdict could merge through a thin command | Say which caller enforces each prerequisite; keep exit 2 as "re-run the mechanical gate", distinct from `erg-pr-status` exit 2, "pending" |
| D18 | **PR body edited after approval** | Head and candidate unchanged, so the record still passes; the body now claims another open ticket, and C may miss a short ID | Bind the reviewed claim set to the approval, or recheck body claims immediately before merging |

## Prices and risk

- A to C: about 2.5 author-hours (1 + 1 + 0.5), a judgment. D-slim: 4 to 6, a judgment.
  Total about 6.5 to 8.5 hours. No catch probability is claimed; it is unknown until C
  is wired and run over a few cycles, and even then one cycle cannot establish a rate.
- No CI-time saving is claimed: CI no longer runs on PRs. The 32 s is local `make check`.
- Largest risks: the gate is not yet active (ordering), D16, D12/D13 if Step 2 goes,
  and E4/E5 conflicts.

## Open decisions for the author

1. D-slim (respecified as the gated path only), or D-delete after 1045? Recommended: D-slim, after 1156 activates.
2. Keep Step 2 (close commit) in the thin helper? Recommended: yes, for one cycle.
3. Keep the body claim as the source? Recommended: yes.
4. Layer A at gate time only, or in `make check` with an in-progress exemption?
5. E1/E7: exempt tickets-only diffs, and how to treat tracker closes?
6. H1/H2: does a hotfix to a red `main` owe a ticket; is any no-PR merge legitimate?
7. D16: should a mechanical re-record on a moved base consume a review round?
8. D17/D18: who enforces claim set, approval and record together?
9. D10: ship A and B to other repos, or accept sweep-only?
10. D5: keep the sync in the thin helper, or move it to `/roar`?

## Staging if approved

Tracker plus children. Order: C first (smallest, already tested); A and B; then D-slim
**after** 1156 activation, touching Step 3 only. The tracker closes after the
integration review (`/roar` step 8). Nothing is filed until the author says so.

## Review trail

- Opus (code-reviewer seat): FIXABLE. Found the gate constraint, the `enumerate-merges`
  rejection of branch names, layer A timing, the cutover and rebase scenarios.
- Codex (`codex exec`, read-only): FIXABLE. Found `--auto` in D-slim, gate-off state,
  the suites total, the two-gate contract and the post-approval body edit.
- Fable (code-reviewer seat): FIXABLE. Confirmed gate-off and `--auto`, found the
  serial-wave scenario, the hidden Step 2 decision and the D9 contradiction.
- Astra: no routing entry exists in this repo and the `Agent` tool takes no `astra`
  token; Codex stood in as the other-family seat. Not an Astra review.
- Opus and Fable are the same vendor family as the author of this note (Claude); only
  Codex is decorrelated. All three reached FIXABLE independently and the main defects
  were found by at least two of them.
