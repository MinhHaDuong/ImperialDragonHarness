---
metadata:
  category: publication
name: conference-submission-prep
description: "Prepare a humanities and social sciences conference submission from its call for papers. Use once venue and message are set; not for those (/choose-venue, /message-framing)."
---

# Conference submission preparation

Editorial sparring, not content generation: the author owns the
contribution; this pass makes it fit what the call asks for and how it will
be read. It does not judge scientific merit.

**Upstream.** Venue chosen with `/choose-venue`; central message framed with
`/message-framing`. If either is missing, do it first: a call cannot be
answered by a submission that does not yet know its one claim.

The steps run sequentially: each consumes the previous one's output.

## 1. Read the call

- **Submission types** offered (paper, short paper, poster, panel, other),
  and which one the project's maturity supports. Recommend one.
- **Explicit requirements**: deadline with its timezone, length, file format,
  citation style, required sections, blind or open review.
- **Review criteria**, when stated. They are the scoring sheet for step 3.
- **Implicit expectations**: what this community counts as a contribution
  (archival finding, interpretation, method, synthesis). Read past programmes
  when the call is silent.

Say so when the fit is poor. A modest, well-positioned contribution beats an
overreaching one.

## 2. Write the abstract as a paper

**A poster abstract is a standalone short paper**, not a summary of the
poster: reviewers score it alone, often without ever seeing the poster. The
same holds for most conference abstracts. It covers, explicitly:

1. the question or problem, and why it matters to this audience;
2. the approach: sources, corpus, method;
3. the findings or the argument's result;
4. the significance: what changes in the field if it holds.

Self-contained, no tables or figures unless the call invites them, claims no
larger than the evidence, the contribution type named.

Length over budget: `/cut-prose`. Citations: only those that carry the
argument, in the venue's style; a new reference goes through
`/related-work-note`, then `runbooks/bib-merge.md`.

## 3. Review before sending

Run `/gaze` (prose panel) on the submission's merge request, or
`/manuscript-review` on its PDF, giving the reader the call's criteria from
step 1. When the author explicitly requests independent external readers,
use `/external-peer-review`, which runs the same protocol per routed reader
and preserves dissent. Resolve verified findings; report unresolved concerns
and the remaining author decisions with a recommendation.

## 4. Finish and record

- Blind review: in the source, self-citations in the third person,
  acknowledgments, identifying project names and identifying figure content
  (logos, maps, screenshots) removed; then `/pdf-finish`
  builds the anonymous variant and sweeps it, metadata included.
- Once sent: `/submission-event submitted`.
