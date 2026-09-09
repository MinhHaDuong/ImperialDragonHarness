---
name: the-briefing-is-a-claim
description: "A gate directive stated five facts about the batch it was gating; five were wrong or imprecise, each checkable in one command against the artifact (gate #5 adapter batch, 2026-09-03)"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-08T07:53:15.476Z
  originSessionId: a0465653-bed4-450c-a2b2-a9fe384d1532
---

# The briefing is a claim, not a fact

A directive that hands a gate its scope also hands it a summary of what it will
find. That summary was assembled by someone reading the same pull requests, and
it decays the same way any second-hand reading does. On the adapter batch of
2026-09-03, the gate's own directive told it to "trust the PR and tell me I was
wrong" — and then earned that instruction five times in one night.

| The brief said | The artifact said |
|---|---|
| the tip carries **one** further unreviewed commit | **two** (`5ee8722` + `80353d6`) |
| the port deviation "is disclosed in **all three** declarations" | only `zotero_core_6012.py` names it a *deviation*; the other two describe the write as harness setup and never cite the shipped default |
| the lane allocated **four** ports | **five** — `r10_host_baseline.py:208` adds `a.port + 10` for its control cell |
| **four** egress drivers now sit outside `bench/acceptance/` | **three** |
| 0496's report **§5** asserts a build "exists on no machine reachable from **any** lane" | §5 says "**this** lane", and is still true as written; the "any lane" overclaim is one file over, in the ticket's closing log entry |

The last is the instructive one, because acting on the brief would have produced
a *wrong correction to a correct sentence* while leaving the actually-false one
standing. Every entry above was one `grep`, one `git log`, or one `python3 -c`
away.

## The rule

Verify a directive's load-bearing claims the same way you verify a lane's. The
tell is a sentence that names a count, a location, or a scope word — *all
three*, *four ports*, *§5*, *any lane*, *one commit*. Those are the ones cheap
to check and expensive to inherit, because a gate that repeats them signs them.

State the correction in the merge comment, on the record where the next reader
is, not only in the report back to whoever briefed you. Two of the five above
were repeated by an independent reviewer as well, which is how a second-hand
number becomes a fact nobody measured.

## It applies to a reviewer's premise too, and there it is sharper

A reviewer is a briefer. On 2026-09-08 two adversarial seats reviewing sibling
patches contradicted each other on a checkable fact: whether any commit merged
upstream from this fork carries `Co-Authored-By` / `Claude-Session` trailers.
One said none does and called their presence a defect; the other measured and
found six of ours plus four of the maintainer's own. I had already relayed the
first as an instruction to strip them.

Two things make this worse than the count errors above. The instruction would
have **changed something that was already correct** — the conforming commit
would have become the odd one out. And a review's whole value is that it is
adversarial, which makes its assertions feel pre-verified when they are exactly
as second-hand as any brief.

`git log --all --grep='Claude-Session'` settled it in one command. What survived
the check was the *other half* of the same finding, and it was real: across 331
upstream commits not one is authored by a non-human identity, and the patch's
was. So the seat was half right, which is the normal case and the reason to
check rather than to pick a side.

**The rule:** before acting on a reviewer's factual premise, run the command
that would falsify it — most sharply when the premise asks you to change
something that currently works, and when two reviewers disagree. Neither seat's
word is evidence, in either direction.

## The corollary that settled a merge

The same discipline decides when a verdict still covers a branch. **A verdict
covers the head it was given at, plus any follow-up the reviewer itself named.**
On this batch that cut both ways within an hour:

- #238's approval was given at `1122c18`; the head was `80353d6` with two
  commits the reviewer never saw. **Fresh verdict obtained**, posted to the PR
  page and confirmed by grepping it.
- #240's approval was given at `6598ee6` and its text read "Take the three
  corrections in a follow-up commit on this branch if the gate is willing; none
  of them blocks the merge." The head moved to `69597ac` carrying exactly those
  three. **Merged on the standing verdict**, with the delta named in the merge
  comment.

The difference is not how large the delta is. It is whether the reviewer
authorized it in advance, in writing, on the page.
