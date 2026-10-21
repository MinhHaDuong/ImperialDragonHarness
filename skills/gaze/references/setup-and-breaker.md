# Gaze — phase 1 collection, breaker and waiver

Loaded from `skills/gaze/SKILL.md` § 1. Setup, after the isolation script has run.

- Abort if not mergeable or if there are open merge conflicts.
- Collect:
  - The ticket file(s) referenced by PR-body close claims (`tickets/*.erg`);
    include any title/body reference when no close claim exists. No close
    claim and no title/body reference → proceed with `ticket: none`; the gate
    reviews against the PR body (`/verify-gate` § Circuit breakers).
  - PR body, full diff, all existing review comments, all inline comments, all commit
    messages on the branch.
- Check CI status for the merge request if the forge exposes it. If the forge CLI or API is unavailable, skip gracefully — CI status is informational only. If checks are configured and any are failing, note this in the setup summary; do not block on it (reviewer decides).
- First run `python3 "$IDH_ROOT/scripts/review-pr-anchor.py" <pr-number> --worktree "$primary_root/.claude/worktrees/review-<pr-number>"`. A nonzero `REVIEW-ANCHOR:` result stops the battery: do not review an empty or wrong-tree diff. Carry its HEAD and changed-file roster into every review prompt.
- Compute PR size rename-aware: `pr_lines` = total insertions + deletions from `git diff origin/main...HEAD --stat`; `pr_files` = the CONTENT-BEARING entry count from `git diff --name-status -M origin/main...HEAD` — added, modified, and deleted each count 1; cross-reference rename entries with `git diff --numstat -M origin/main...HEAD`: a rename counts 1 iff its additions + deletions > 0, otherwise 0 (a genuinely content-free pure rename has zero line change in rename-aware numstat; R100 alone is insufficient because the similarity index ignores line order) — pure renames add no review load, and counting them via `--no-renames` inflates consolidation diffs past the breaker on arithmetic (ticket 1026, observed on PRs #1178/#1179).

  Size has one use: the un-reviewable breaker below. It selects no battery
  tier; every PR gets adherence, the review panel and simplify.

- **Preflight before spawning phases 2–5.** Count distinct ticket close-claims
  from the PR **body**, using the same line grammar as `erg-pr-merge`: bold or
  bare `Ticket: tickets/NNNN...` lines count; the title, `Ticket-ref:` lines,
  `Ticket: none`, and repeated claims for one ID do not. For example, extract
  IDs with `grep -oiP '^\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+' | sort -u`.
  If the count is two or more, record `multi_ticket: <IDs>` as a **non-blocking**
  finding for `/verify-gate` to disposition. Below the size breaker, continue the normal review;
  genuinely bundled tickets are permitted by `rules/git.md` § Merging.
- If `pr_files >= 15` and no waiver is recorded (see **Waiver** below), the PR exceeds the **15+ content-bearing files** monster threshold
  borrowed from `rules/workflow.md` § Ticket discipline for multi-PR work. Return ESCALATE
  immediately, before spawning any phase 2–5 reviewer,
  with `circuit_breaker: un-reviewable` and reason
  `un-reviewable: <pr_files> content-bearing files / <pr_lines> lines — split before review`.
  When `multi_ticket` is present, add that the combined tickets are a
  decomposition signal. Post the result comment with the
  breaker and `battery: skipped (un-reviewable)` visible; the caller's
  `/verify-gate` re-counts the files itself and ESCALATEs the same way.
  Cleanup and containment
  still run. An explicit `--force-approve <reason>` overrides this breaker
  loudly under the existing override contract; record the waived breaker and
  size in its PR comment. `--force-approve` runs no review at all (§ `--force-approve`);
  a waiver below is the way to keep review on an oversized PR.
- A recorded waiver (`--waive-breaker` or the PR-body `Review-scope: indivisible` line) lifts only this stop; its rules are in § Waiver below.

- ESCALATE with a clear message, and do not proceed, only if a close claim names a nonexistent ticket file or the PR body, diff or comments cannot be located. A missing ticket with no claim and no reference is not an escalation.

#### Waiver

The 15-file count is a decomposition signal, not a hard wall. A waiver lifts
only the file-count stop. It never lifts the review, simplify or any other
breaker, and gaze never approves a waived PR: the caller passes the waiver
record to `/verify-gate`, which rules NEEDS-AUTHOR on a passing waived PR, and
only the author decides to merge it.

**Declaring.** `--waive-breaker <reason>` on the `/gaze` invocation, or a
PR-body line `Review-scope: indivisible — <reason>`. The author writes either.
Gaze does not check who wrote it; the gate judges the diff (`verify-gate`
§ Indivisibility). The change must be indivisible: a pure rename or rewire with
no independent change that could land alone.

**Recording.** Read in phase 1, before any reviewer spawns. Record the waiver
with `pr_files`, `pr_lines`, the reason and its source (flag or body line) in the
PR comment, and set the header to
`circuit_breaker: waived (<pr_files> content-bearing files / <pr_lines> lines — <reason>)`.
The round-1 header is the baseline for growth.

**Scope.** Growth is measured against the earliest posted waived header, not the
phase-1 recount of a later round, because a recount absorbs the very growth it
should catch. Growth past that baseline makes the PR un-reviewable:
`circuit_breaker: un-reviewable`, ESCALATE. A waiver beside two or more close
claims is flagged as `multi_ticket`, as in the preflight above. Every later
comment of a waived PR repeats the header
`circuit_breaker: waived (<pr_files> content-bearing files / <pr_lines> lines — <reason>)`
so the gate reads one format.
