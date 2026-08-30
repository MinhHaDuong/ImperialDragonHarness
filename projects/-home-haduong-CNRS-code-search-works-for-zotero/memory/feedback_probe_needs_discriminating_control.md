---
name: feedback-probe-needs-discriminating-control
description: A positive control must discriminate the hypothesis under test, not merely show the instrument produces output
metadata:
  type: feedback
---

A positive control proves the probe can detect **the specific thing being
tested**. A control showing only that the instrument returns numbers is not
one, and it passes just as happily when the experiment is vacuous.

**Why:** on 2026-08-29, testing whether an embedder silently truncates at 512
tokens, the first probe embedded one word repeated 900 times and compared the
vector to its 512-token prefix. Cosine 1,000000 — "truncation confirmed". It
proved nothing: mean-pooling over a homogeneous text gives the same vector at
any length, so the result was identical whether or not truncation occurred.
The control that ran alongside it (two unrelated short texts scoring 0,10)
showed the metric discriminates *texts*, which was never in doubt. The second
attempt used a head of 482 tokens — under the limit — so the two inputs never
shared a full-length prefix, and its 0,994 was consistent with both hypotheses.
Only the third construction, head over the limit with a semantically different
tail, discriminated.

The same failure appeared twice more that day in a different costume: a
paragraph-size measurement whose splitting method reported a median of 3 words,
because a third of the corpus was HTML snapshots extracted one word per line —
the instrument was measuring layout, not paragraphs.

**How to apply:** before trusting a probe, state what result the *opposite*
hypothesis would produce, and confirm the probe would show it. If both
hypotheses predict the same output, the experiment is not yet an experiment.
Then check the instrument against the data's real shape — sample one raw input
and look at it — because a method that suits the data you imagined can silently
mismeasure the data you have.

**A third costume, the null case, same day.** Sweeping for prose that quotes
this repo's measurements, a grep matched figures shaped `0,884` / `1 773,0` —
decimal comma required. It returned nothing for `CONSTRAINTS.md`, and the
nothing was written into ticket 0160 as a finding: *"checked and quotes none —
correctly absent"*. The file carries `584 of 8 037` and `410 versus 0..25 036`,
all four in `bench/results/0012-fulltext-sequence/`. Integers with space
thousands and no decimal comma: the pattern could not match them, so its silence
meant *this regex is blind here*, not *this file is clean*. `/gaze` caught it —
a false negative control published inside a ticket about false negatives.

The mechanism generalises past greps: **a search pattern encodes an assumption
about the shape of what it seeks, and where the assumption fails the miss is
indistinguishable from an absence.** Redone properly — deriving the patterns
from the artifacts themselves rather than assuming a format — the same sweep
found 29 files, not 2.

**How to apply to a null:** derive the probe's patterns from the data you are
searching *for*, never from how you expect it to be written. Then run it once
against a case known to be positive, and only then believe a zero.

The harness rule "a null result is not a finding until a positive control has
fired" covers the null case. This is its twin: **a positive result is not a
finding until the control could have come out the other way.**

**Enforce the control; do not merely record it (2026-08-29, ticket 0421).** A
pooling probe was written specifically to keep four states apart — `read`,
`ambiguous`, `confirmed_absent`, `could_not_look`. Its own negative control failed
on the first run and caught the probe collapsing two of them: a repository that
does not exist and a repository publishing no pooling config both answer 404, and
separating them needs a second call to the metadata endpoint. A probe written to
detect collapsed states had committed the collapsed-state error.

It surfaced only because the control was enforced rather than reported. The script
refuses to write its artifact when a control comes back wrong, so the run stopped.
Had the control merely been *recorded in the output* — the shape that feels
thorough — the artifact would have been written, every value in it would have
looked fine, and the wrong classification would have been read months later as a
measurement.

So: a control that is written into the artifact is documentation. A control that
aborts the run is a check. Prefer a positive control whose expected value is
attested somewhere independent of the probe (here, a pooling mode recorded in
Zotero core's own registry), because a control the probe itself defines can only
confirm the probe is self-consistent.

Related: [[feedback-adopted-constants-carry-mechanisms]].
