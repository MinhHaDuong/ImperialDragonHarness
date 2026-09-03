---
name: feedback-verify-the-load-bearing-claim
description: The one sentence an outside reader checks first is the one nobody verified — run the code behind a rhetorical centerpiece before it ships
metadata: 
  node_type: memory
  metadata_type: feedback
  type: feedback
  originSessionId: 7a9efc3f-7c9c-49b1-b574-07d7404e6a7a
  modified: 2026-09-03T05:43:49.354Z
---

A drafted upstream PR opened its case with "`to be or not to be` tokenizes to
nothing at all, on both backends". It does not. `not` was never among the 29
stoplist words, so the query survived as `not` alone and the search returned
twenty confidently ranked, entirely unrelated passages. Checking it took one
command — importing `tokenize()` from each built tree and printing its output
(2026-08-29, ticket 0014).

The claim had been repeated across three artifacts — a source doc comment, a
test comment, and the PR body — carried forward from an earlier session and
verified by nobody. It was also the PR's opening argument, aimed at a
maintainer whose trust is this project's scarcest asset, and falsifiable by him
in under a minute.

**Why:** a rhetorical centerpiece attracts exactly the scrutiny its author did
not apply. The sentence chosen to be memorable is the sentence a skeptical
reader tests, so the load-bearing claim in outbound text carries more risk per
word than anything else in it — and inherited prose is where the risk hides,
because it reads as already-settled.

Worth noting what the verification bought beyond the correction: the real
defect was *worse* than the claimed one. A query returning nothing tells the
user something went wrong; one returning confident noise does not. Checking a
claim you expect to confirm is not wasted when it comes back stronger.

**How to apply:** before anything leaves for an external reader — an upstream
PR or issue, a submission, a report — list the claims a skeptic would test
first, and execute each one. Prefer running the code over reading it: grepping
the wrong file returns zero just as convincingly as a true negative (the same
session nearly concluded a bundle carried no stoplist by grepping the entry
point instead of the tokenizer). Treat inherited sentences as unverified
regardless of how many artifacts already repeat them; repetition is not
evidence.
A second instance, and the sharpest form of it: a premise entering an
**append-only** document. The 0140 chunk-budget recommendation rested on "every
candidate embedder declares a window at or above 512", flagged as unverified
when the ballot went to the author. He ratified. Measuring it before writing the
ledger entry took one script — 9 of 9 candidates resolved, tightest window 512 —
and it came back stronger again: the census found that "the model's limit" is
not one number (one candidate declares four position-limit fields spanning a
factor of four), which became a second, independent argument for the low
ceiling. A ratified entry is never edited, so an unverified premise written
there is permanent. Measure before ratifying, not after.

A third instance, and the cheapest to prevent: the claim was about **my own
edit**, not about the world. A script inserted a children table into ticket 0240
with `str.replace` against an anchor carrying a blank line the file does not
have. Python's `replace` matches nothing and returns the string unchanged — no
exception — and the script printed "ok" afterwards regardless. A second replace
in the same script did match, so the commit looked half-right. I then asserted
the section existed in the commit message and the PR body. Two of three review
agents caught it independently; nothing else would have (2026-08-29, raid 240).

The general shape: `str.replace`, `sed s///`, and `re.sub` all no-op silently on
a missed anchor, and the *edit* is the load-bearing claim in the commit that
follows. So an in-place edit script asserts its anchor appears exactly once
BEFORE substituting, and asserts the result is present AFTER writing. Two lines,
and they convert a silent wrong commit into a loud failure. Never let a script's
own "ok" stand as evidence that an edit landed — grep the file.

A fourth instance, at ticket scale: raid 220 (2026-08-29). Ticket 0220 was
written entirely from reading `onnx.js` and even said so — "every GPU claim in
this ticket is read, not observed". Executed, FOUR load-bearing claims failed:
`device: 'auto'` hard-fails on CPU-only Linux instead of falling back; `q7` is
silently coerced, not rejected; the fall-back-to-default-precision remedy would
have mislabelled the index (the identity is stamped before the first embed);
and "the model is already configurable", the ticket's whole motivation, was
false — the local path hardcodes it. The honest self-flag was the tell nobody
acted on. When a ticket marks its own claims unexecuted, executing them is
step one of the hunt, cheapest first — the CPU-only half of the device claim
needed no GPU and voided the ruling in one probe. Corollary learned the same
day: before recommending any filing, one search for the existing issue —
transformers.js#1642 had reported the device bug four months earlier
(one `gh search issues` command, run only after the author pushed back).

A fifth instance, the cheapest of all and mine: **`command -v X` answers "is X
on `PATH`", never "is X available".** At the 2026-09-03 dawn close I ran it for
`erg-pr-merge`, got nothing, and wrote *"not available in this environment"*
into a merge comment as the justification for closing a ticket by hand. It ships
at `~/.claude/skills/merge/erg-pr-merge`; one `find` would have said so. The
outcome was unharmed — the manual close was verified end to end — but the
*reason* on the record was false, which is the part an outside reader checks.

The shape generalises past this command: a probe that answers a narrower
question than the sentence you write from it. `command -v` scopes to `PATH`,
`grep` scopes to the files you named, `git log` scopes to the range you gave.
Each returns a truthful narrow answer and a plausible wrong wide one, and the
widening happens in prose where nothing checks it. When a negative probe is
about to become a justification, run the second command that widens the scope —
and if you have already published the wide claim, **post the correction rather
than editing it away**.

Related: [[feedback-benchmark-harness-traps]],
[[feedback-execute-authorized-outward-actions]],
[[feedback-probe-needs-discriminating-control]],
[[feedback_a_denial_that_matches_a_rule]].
