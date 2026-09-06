---
name: feedback-a-gate-without-the-button
description: "A merge gate that does not hold the merge action is advisory only; three of five PRs merged from other lanes, twice mid-review, and its findings then landed on main unfixable"
metadata:
  type: feedback
---

A review gate is a **gate** only where the merge action is serialized behind its
verdict. Where every lane can merge, the same work is an **opinion in a race**,
and the difference is not rhetorical: it changes what the gate produces and what
its findings can still do.

**What happened, 2026-09-02 overnight.** One session was appointed merge gate for
five PRs. It merged none of them. Three merged anyway, from other lanes: #216 at
19:58Z before the gate ruled, #217 at 20:02Z **while the gate agent was mid-review**,
#220 likewise. The two the gate did rule on (#211, #212) it bounced REROLL, plus
#218 — so every verdict the gate actually issued was a bounce, and every merge that
happened was somebody else's. `origin/main` moved 35bce51 → ceadf71 under it.

**The cost is mechanical, not hurt feelings.** A gate that arrives after the merge
is a *post-merge audit*, a different product. A finding against an open diff is
a bounce: the author fixes it before it exists on main. The same finding against
merged main is a ticket, or nothing. Tonight it was nothing, three times —
a hardcoded provenance flag under 33 quoted figures, an unsourced divisor in
`SPEC.md` §5.2.8 contradicting §5.2.9 two paragraphs later, and a ratchet
(`MINIMUM_PAIRS` 462 against an actual 496) with 34 pairs of silent slack. All
three were found *because* the gate kept reading after the merge; none could be
bounced, and the session was under an explicit no-file constraint. That is the
tax: an advisory gate converts blockable defects into backlog.

**Diagnose it by the clock, not by the outcome.** The tell is a merge timestamp
earlier than the verdict timestamp — check it, because a lane that merges a PR
you were reviewing has no reason to know you were. Two of tonight's three were
invisible until the gate re-read `origin/main`.

**How to run it.**
- Before accepting a gate mandate, establish whether the button is exclusive. If
  it is not, say so in the first report: "advisory review, N lanes can merge".
  A mandate that cannot be enforced is a mandate to be renamed, not to be tried
  harder.
- When a PR merges mid-review, **do not discard the review** — retarget it at
  merged main and label the output an audit. It is the only thing left that can
  find the defect.
- Findings against merged main need an owner at the moment they are found. Under
  a no-file constraint, that owner is the report; name the file, the line, and
  the contradicting number, because nobody will re-derive it.

Sibling to [[feedback_merge_authority_needs_attached_verdict]]: there, a lead
merged on verdicts that did not exist. Here the verdicts existed and the merges
did not wait for them. Both are the same missing property — the merge action and
the verdict were not bound to each other.
See also [[feedback_one_gate_per_pr_at_a_time]] and
[[feedback_green_prs_red_union]].
