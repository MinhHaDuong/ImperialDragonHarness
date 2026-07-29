---
name: feedback_check_open_prs_for_ticket
description: "Before starting a ticket, scan open PRs for that ticket ID — origin/main currency does not reveal a sibling session already working it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0f40bf6-0077-4e13-a087-1fb24d90b8fb
  modified: 2026-07-28T08:10:47.164Z
---

`git fetch` + `git log HEAD..origin/main` only shows work that has **landed**.
It cannot show a parallel session that started the same ticket ten minutes ago
and has not merged. On 2026-07-27 two sessions independently implemented ticket
0359 and opened PRs #1196 and #1198 **62 seconds apart** — both adding a
reachability guard over `deliverables/_shared/`, both splitting
`CORPUS_REPORT_FIGS` out of `DATAPAPER_FIGS`, both editing `paths.mk`. Neither
saw the other until one of them ran `gh pr list` for an unrelated reason.

Second occurrence 2026-07-28: PRs #1245 and #1250 both fixed ticket 0375, 6
minutes apart — and the pre-work scan does not cover it, because the sibling's
PR appeared *after* mine was open. In a multi-ticket wave, re-run the scan at
each ticket boundary, not once at session start; the author's "check what
other sessions are doing before choosing work" is this rule. Resolution
followed [[feedback_diff_fully_before_deleting_a_fork]]: full diff of both,
the later PR was a strict superset (extra TOTAL/`****` fix, stricter CSV pin,
emitter byte-compare), so the earlier one closed with a comment naming the
test-name collision the merge would otherwise hit.

Third occurrence, same day, and it extends the class beyond tickets: PRs #1242
and #1248 both restored the `return found` that a Copilot autofix deleted from
`products_named_in`, 14 minutes apart. Neither was claiming a ticket — both were
repairing *main being red*, which no ticket ID identifies, so every ID-keyed
probe above is blind to it. The scan that would have caught it keys on the
**file**: `gh pr view <n> --json files` over the open list, matching the path you
are about to touch. And the miss happened at the *merge*, not at dispatch — #1242
appeared four minutes after the fixing subagent was launched, so only a re-scan
before merging could see it. **A subagent will not run that scan for you**; it
sees its own worktree and the task text, not the forge. The dispatcher owns the
pre-merge check.

Fourth variant, and it needs no sibling session at all: **two gates on one PR,
both mine**. On 2026-07-28 I launched `/gaze 1244` as a background fork, read the
review panel's comment when it posted, acted on its minors, and merged — while
the fork was still in its verify phase. It finished afterwards, found the branch
dead, and reported a "concurrent session" that was in fact me. No harm (the
verdict was APPROVED either way, and the panel's best catch was applied), but a
gate whose verdict lands after the merge is not a gate. **If you delegate the
gate, wait for the verdict, not for the intermediate artifact you can act on.**

**Why:** the session-start sync rule guards against duplicating *merged* work.
Under parallel autonomous sessions the more likely collision is duplicating
*in-flight* work, and the two need different probes. The repo had 15 open PRs
that afternoon; the odds of two picking the same ripe ticket are not small.

**How to apply:** at ticket start, before writing any code, run both probes —

```bash
git fetch origin && git log --oneline HEAD..origin/main   # landed work
gh pr list --state open --json number,headRefName,title \
  --jq '.[] | select(.headRefName + .title | test("0?359"))'   # in-flight work
```

If a sibling PR exists: do not race it. Comment on it, and either take a
different ticket or agree a split. If the collision is only found late (as here),
do not merge either PR — post a comparison on both, state what each covers that
the other does not, and let the author pick. Merging the first-created one
silently discards the other session's work.

## The same probe, at allocation time

The identical scan answers a second question: **is the ID I am about to
allocate already claimed?** Here the two sessions are working *different*
tickets and merely collide on the number. The 0339/0340/0341 raid hit this
three times in one afternoon (0349, 0367→0370, 0376→0378); two were caught only
at the merge gate, because a sibling PR claimed the ID *after* this session
allocated it. This repo has no cross-PR collision CI, so nothing catches it for
you.

**A high-water mark is not the answer.** At the 2026-07-27 wrap-up the working
assumption was "IDs through 0378 are taken". `origin/main` actually carried
through 0382, and open PRs added 0379 and 0380. Allocating 0379 on that
assumption would have been the fourth collision. Enumerate the union, never a
remembered maximum:

```bash
git fetch origin
git ls-tree -r --name-only origin/main -- tickets/     # landed IDs
for p in $(gh pr list --state open --json number --jq '.[].number'); do
    gh pr diff "$p" --name-only | grep '^tickets/'      # in-flight IDs
done
```

Do **not** take `max(union) + 1` — that was this file's advice and it is wrong.
The next-free seat is the most contended number in the repo: every parallel
session computes the same value and races for it, so allocating there is exactly
as collision-prone as the allocation you are repairing. On 2026-07-27 one filing
collided three times chasing it (0384 → 0385 → 0386), leaving `origin/main` red
on a duplicate ID twice; it settled first try at 0400, twelve clear. Pick a
number well above the high-water mark — IDs are free and a gap costs nothing.
`erg new` scans only the local checkout, so treat its allocation as a proposal
this scan confirms, then move it clear of the frontier.

`erg check` scans `tickets/closed/` too, so **archiving one half of a duplicate
does not clear it** — only a renumber does. Verified 2026-07-28 by replaying an
archive against `origin/main`'s tree while the duplicate persisted.

**Who moves, on a collision.** Seniority says the later allocator ought to
renumber, but the session holding the merge gate is the one that *can* renumber
correctly — it has both tickets in view and can fix cross-references before
landing. The sibling session may never re-check. So the merge-gate holder
renumbers itself, regardless of who allocated first, and does not wait for the
sibling to notice. Re-run the scan at the merge gate too, not only at
allocation.

Related: [[feedback_scope_discipline]], [[feedback_ticket_pr_fast_path]],
[[feedback_no_ci_local_merge_gate]].
