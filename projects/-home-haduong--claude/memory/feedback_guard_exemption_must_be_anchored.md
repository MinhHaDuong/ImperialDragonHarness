---
name: feedback-guard-exemption-must-be-anchored
description: "An unanchored exemption clause in a text guard waives every other check in the same input — worse than shipping no exemption at all"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c506a505-1611-409e-9bc5-e01468245a63
  modified: 2026-09-10T09:30:00.000Z
---

A text-matching guard grows an exemption the first time it misfires. Write the
exemption unanchored — "if this token appears anywhere in the input, allow" —
and it does not narrow the guard, it **holes** it: one incidental match anywhere
waives every other check for that whole input.

Measured 2026-09-10, on `guard-pgrep-waiter.sh`. The guard denies a shell loop
polling a process. It misfired on a heredoc *documenting* the banned shape — the
repo's own memory note quotes it verbatim — so heredocs were exempted with
`<<-?\s*['"]?\w`, matched anywhere. Three genuine waiters then sailed through by
sharing a compound command with something irrelevant:

- `x=$((1<<3)); until … pgrep … sleep …` — a bitshift
- `echo "legacy uses <<END markers"; until …` — decorative text
- `cat <<< "hi"; until …` — a herestring, which is not even a heredoc

None needed a heredoc to be present. The fix was to require the introducer at
end of line (grep is line-oriented, so `$` does the work) and to refuse the
exemption when the same line invokes an interpreter, since `bash <<EOF … EOF`
executes what it carries rather than documenting it.

**Two rules, and the second is the one that was skipped.**

1. An exemption is a *predicate on the whole input*, so scope it as tightly as
   the deny it overrides. Anchor it — line start, line end, command position —
   and state which construct it recognises, not which characters.
2. **Every exemption needs a deny case on its dangerous side.** The conceded
   risk (`bash <<EOF`) was written into three places in prose and pinned by no
   test, which is how the boundary an exemption claims to draw drifts unnoticed.
   A test on the safe side alone proves the exemption fires, never that it stops.

**The larger shape, over three review rounds.** Fixing a false positive opened a
false negative, and fixing that one re-opened a false positive elsewhere. That
is the natural failure mode of a *textual* guard against a defect defined by
*execution semantics*: the vocabulary of running a thing and of describing it is
the same vocabulary. Expect such a guard to need another patch after the one you
are writing, budget for it, and do not read a quiet week as convergence.

Related: [[feedback_measure_whether_a_guard_ever_fired]],
[[feedback_a_test_green_for_an_accidental_reason]],
[[feedback_pgrep_waiter_matches_itself]].
