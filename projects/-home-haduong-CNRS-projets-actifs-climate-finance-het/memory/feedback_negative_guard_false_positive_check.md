---
name: feedback-negative-guard-false-positive-check
description: "before shipping a new forbidden-phrase prose guard, grep the live document for the exact phrase — generic candidates collide with legitimate structural prose"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4416da70-2381-4a58-904a-29125c1a1dde
---

When adding a new negative-guard phrase to a prose ratchet (ai-tells.yml
`blacklisted_phrases`, or a manuscript-scoped pattern list), run the test
suite against the live document *before* considering the guard done — a
generically-plausible "AI tell" phrase can collide with normal academic
writing already in the text.

**Why:** ticket 0243 (voice-alignment mechanization, PR #1016) added "this
section demonstrates" / "this section shows" as candidate generation-
scaffolding tells (Fable-suggested). `manuscript.qmd` line 94 legitimately
opens a section with "This section shows why...", a standard academic
signpost sentence, not bot commentary — the test suite caught it
immediately (`test_no_blacklisted_phrases` failed) before the guard was
committed. Dropped those two phrases rather than trying to special-case
them; kept the unambiguous ones ("as requested", "note for the reviewer").

**How to apply:** run the relevant prose test suite right after adding a
guard phrase, not just at the end of a batch. A red result at that point is
cheap information (which phrase, which line) — a red result discovered later
in a pile of other changes is not. When a phrase is genuinely ambiguous
(collides with normal usage), prefer under-mechanizing (drop it, note the
near-miss) over trying to write an exception carve-out — see
[[feedback_aitells_scope_manuscript_vs_crossdoc]] for the sibling lesson on
where these guards should live.
