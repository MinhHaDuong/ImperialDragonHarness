---
name: feedback_pagination_widow_verification
description: "Fix manuscript widows/pagination by shaving signposts first and verifying by rendering the specific page to PNG and Reading it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a0bed5cd-c7ef-4c4b-bb4c-87b251470dcd
---

**When the author reports a widow / "N lines too long" on a specific page**, the
reliable loop is:

1. **Shave the lowest-value lines first**: section roadmaps, recap lead-ins,
   forward-reference closers, signpost sentences, and descriptors already in a
   figure caption. These carry no argument and ~2 lines of them clear most
   widows. Prefer compressing a standalone paragraph into a `see Figure~\ref{…}`
   pointer over deleting substance.
2. **Verify by rendering the exact page**, never by guessing: `tectonic -r 2`,
   then `pdftoppm -f N -l N -r 120 -png main.pdf out` and **Read the PNG**.
   Confirm the orphan line is gone and the target (e.g. §heading, conclusion
   end) lands on the intended page. `pdftotext | grep` is unreliable for this —
   line-wrapping hides the phrase.
3. **Cross-PR pagination interacts**: a widow on page K often depends on an
   earlier shave (e.g. the abstract shave pulls everything up). Render with ALL
   the relevant PRs merged before the final verdict; a build off a branch that
   lacks the prior shave shows a stale layout.

**Why:** the 2026-06-15 widow pass (abstract, intro, §7, §9/§10) cleared every
widow this way; each fix was a 2-3 line shave of signpost prose, verified by
reading the rendered page. Guards held (em-dash cap, §fusion primacy markers,
0588 fig:cost-quality anchor) — see [[feedback_no_caveats_in_captions]] and the
CI-polarity rule.
