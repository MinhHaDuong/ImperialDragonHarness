# Guichet triage trial: blind replay rejects C1

Date: 2026-11-12 · host: padme · drafter anthropic/claude-opus-5-5 ·
follows `2026-11-12-guichet-design-red-team-to-c1.md`

## Context

C1 (intake over git, sandboxed read-only triager, verdict script) was the
recommendation of the guichet design note after PR #2476. Asked how C1
beat the status quo, the drafter proposed testing the triage step on real
cases before building; the author asked for more cases and a hand run.

## Events

- A sweep (Claude pinned `sonnet`, read-only) found 21 more cross-project
  reports to the harness, git-erg and padme, 27 with the six already in the
  note. Its outcome timings were partly wrong (G2's retarget: 26 minutes,
  not the sweep's 1h45, corrected by the judge and verified).
- Four triager agents (Claude pinned `opus`) replayed a draft triage brief
  blind: each saw the report as first filed and the receiver as a detached
  checkout at the filing commit's parent, outcome files withheld. Two
  triagers reported small blindness breaches (P3, K-P1). Several replay
  artifacts: K-P1 and P1 were filed together with or after their fix.
- A judge (Claude Fable) compared verdicts with real outcomes: 19 no
  change, 3 small or partial gains (G2, H3, K-H1), 3 harms (G3, H1:
  refusals on recorded text the owner then reversed; H7: a fold into
  another ticket), 2 unjudgeable. In K-H1, the case with the largest
  possible saving, the triager missed the local-API ruling present at the
  cutoff in `memory/topics/host-environment.md`.
- The author ruled to commit the trial and rewrite the recommendation as
  the status quo plus three additions; PR #2478 merged after four gaze
  rounds of wording corrections (overstated gains, cause of harms,
  superseded entries, median rather than every case).
- Tracker 1544 and children 1545–1547 filed by PR #2479; children carry
  `needs-human` while the note is provisional.

## Outcome

Recommendation on main: status quo plus an owner wake-up (`filed from`
log line listed by molt and dashboard), a premise check at pickup (ruling
conflicts go to the author as questions), and a return path for blocked
askers (`Blocked-by:` on the receiver's ticket, `deferred`, released by the
asker's molt). `rules/guards.md` unchanged. Trial evidence:
`design/research/2026-11-12-guichet-triage-trial.md`.
