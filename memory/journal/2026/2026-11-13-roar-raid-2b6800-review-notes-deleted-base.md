# Raid 2b6800: review of PR 2481 and ticket 1548, review notes bound to a deleted base ref

Date: 2026-11-13 · host: padme · drafter anthropic/claude-fable-5-2

## Context

The author asked a harness session to review PR 2481, a ticket filed from
climate-finance-het, then to fix the PR, merge it and raid the ticket. Ticket
1548: `review_notes.py` refused every answer and verdict once the base ref
named by a review's request was deleted, met while landing a stack of three
merge requests on a forge that deletes head branches on merge.

## Events

- Review of the filing. The refusal was reproduced in a throwaway repository
  with a bare remote: after a merge-commit landing of the base branch and a
  pruning fetch, `add answer`, `coverage`, `gate_state` and `record_verdict`
  all raised `cannot resolve origin/<base>`; the same answer write had
  succeeded before the deletion. The forge timeline of the three requests
  matched the ticket's account. Three statements of the ticket were not
  carried by the evidence: that a mere retarget refuses (it does not while the
  old ref resolves), which level of a stack escapes (the bottom one, not the
  top), and a merge-skill criterion that a no-op satisfied.
- PR 2481 was corrected on its branch (commit `60791078f`): those three
  points, a scope line and a criterion for a base landed by squash. It landed
  at bookkeeping tier; main's after-merge run passed on `b2f8b91c8`.
- Raid 2b6800, one ticket, one wave. The per-ticket reimagine and the separate
  plan seat were skipped; the Blind-Spot seat (Opus 5.5) ran and returned six
  findings, among them: the bookkeeping path fails silently on an unresolvable
  base (`merge-gate.py tier` exits 3, read as "not bookkeeping"); `gate` and
  `verdict` took no base, so the squash case could not be told apart on the
  gate path; nothing retains the recorded `base` commit, while `merge_base`
  survives with the kept head; the verdict write and the admission read
  different entries. All six went into the executor's brief.
- The executor (coder profile, Opus 5.5) opened PR 2483. Its full `make check`,
  run with `TMPDIR` inside its worktree, stopped writing at about 99% after
  80 s; one xdist worker kept spinning and the others sat idle. The stall
  breaker fired at 30 minutes; the raid resumed the executor with the
  observation. The executor reported
  `tests/test_review_trajectory.py::test_unreadable_repo_is_not_checked`
  passing in 0 s with the default `TMPDIR` and timing out at 90 s with the
  worktree one, on its branch and on main `b2f8b91c8` alike.
- Gaze round 1 on `585e0c3e8` (Opus, Sonnet, and an OpenAI gpt-6.1-sol
  red-team seat through Codex) answered FINDINGS: the round-2 re-gate after a
  REROLL admitted a squash-landed base. Reproduced, fixed in `d09224854` with
  a test that failed before the fix. Round 2 answered REVIEWED at `d09224854`.
  One red-team finding was downgraded by gaze to a consider (a branch reset
  to its pre-rebase history after a REROLL on a squash-landed stack); the raid
  kept the downgrade.
- The raid closed the ticket on the branch (`99a5e1380`). Verify-gate, run as
  a gate seat (Opus 5.5), ruled APPROVED in round 1 with a positive control:
  against main's `review_notes.py`, 8 of the 9 new gate tests failed.
- PR 2483 landed at `99a5e1380` (main `beff74b37`); the after-merge run passed
  on that tip.

## Outcome

- Handling chosen by the executor: the review is checked against the
  request's current forge base. `gate`, `verdict` and `coverage` take
  `--base-ref`, which verify-gate passes; an answer recorded under another
  base admits a head only when its range is unchanged against the new base;
  without the option, an unresolvable base refuses before any work and names
  the option; gaze setup writes a new request on the same head when the
  request's base is not the current one or no longer resolves.
- Timings: gate round 1, 3 min 56 s from launch to result (the seat reported
  2 min 20 s); merge, 39 s. From the executor's launch to its REVIEWED answer,
  about 50 minutes, 20 of them in the hung test run. Gaze was not timed by the
  raid.
- Attribution backfill for the defect fix: appended 0, no-match 0,
  unresolved 344 (no reviewed-revision evidence was supplied).

## Left as found

- `forge.py list --state open|merged` in no-forge mode still raises on a
  review whose latest request names a deleted base (read, not run). A gaze
  relaunch repairs it by writing a request on the new base; a gate-only path
  does not. The ticket's scope did not include the listing.
- `skills/raid/SKILL.md` and `skills/hunt/SKILL.md` show `coverage` and `gate`
  without `--base-ref`; the default works until a base is deleted, then the
  refusal names the option.
- A base branch deleted and re-created under the same name at another commit
  is trusted by name, as before this change.
- Hunt § Worktree advises `TMPDIR="$W/.tmp"` per command; the hang above
  occurs under that setting.
