---
name: feedback_check_the_detector_first
description: "When a QA check flags prose you wrote carefully, verify what it actually measures before editing the text"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5dc4f34f-6be9-445c-ad64-4385a54f11f8
  modified: 2026-07-27T19:39:48.095Z
---

A quality check that fires on careful prose is a hypothesis, not a verdict.
Read its implementation before touching the text.

**Why:** on 2026-07-27 the data paper's render reported two AI tells and both
were detector defects. `landscape` came from a cited report title's URL slug
in the bibliography — a reference list holds other people's words, which no
edit can fix, and the existing `Global Landscape` carve-out could not match
the lowercase hyphenated slug. The em-dash check claimed "3+ per paragraph"
but built paragraphs by splitting pdfplumber output on a blank line, which
that PDF almost never contains: one "paragraph" spanned six pages, so the
check had been measuring nothing since it was written. Editing the prose to
satisfy either would have made the paper worse.

This applies to instruments I write myself, not just ones I inherit. On the
same day, a reachability sweep I wrote reported 13 orphaned includes that were
perfectly reachable: Quarto resolves `{{< include >}}` against the *top
rendering doc*, not the including file — a rule `architecture.md` already
states — and my resolver joined each path against its own directory. Both
failures produced confident, plausible, wrong output. A sweep's first result
is a hypothesis; check it against one case you already know the answer to
before reporting the count.

**The silent-pass counterpart: read a guard's stated exemptions too.** A check
that fires wrongly is noisy and gets investigated. A check that *declines* to
fire, for a documented reason, is invisible — and the reason can be false. The
0251 wrong-namespace guard exempted bare attribute assignment and named the
exempt case in its docstring: "a test patching utils' own namespace before
calling a function that lives in utils itself (test_robustness_observability.py
save_run_report tests)". `save_run_report` lives in `pipeline_io`, not `utils`.
The claim was wrong when written, nobody re-read it, and those tests wrote into
the DVC-tracked corpus for four and a half months while reporting green
(ticket 0346). An exemption is a factual claim about the code, with the same
shelf life as any other — verify it against source before trusting it, and when
inheriting a guard, read what it excuses as carefully as what it catches.

**A check that cannot fail is the sharpest form of this.** Twice on 2026-07-27
I shipped an instrument that reported success without measuring anything. A
ticket-ID collision scan used `gh pr list --json files`, which never populates
`files`, so it returned empty for every query — its "no collision" and its "I
never looked" were byte-identical, and a duplicate ID merged. Hours later, a
guard meant to reject nested DVC outputs passed on a tree DVC itself rejects: a
`.dvc` entry lists its hash fields before `path`, so `next(iter(entry))` read
the md5 as a path, every output became a 32-char hex string, and nothing could
ever nest.

Both were green, confident, and blind. The defence is cheap and mechanical:
after writing a discovery-driven check, assert the *discovered values*, not
just that discovery ran — that the paths look like paths, that the count is
plausible — and run the check once against a case known to be positive. A
non-vacuity pin belongs beside every guard whose assertion is `assert not
<collection>`; without it, the guard's silence is unreadable.

**How to apply:** two structural fixes generalise. Any check over a *rendered*
document must exclude the reference list before scanning — per-citation
carve-outs never scale. And a check must measure what its message claims: if
the input cannot support per-paragraph granularity, measure density over the
body and rename the finding accordingly. Both are cheaper than a growing
exception list. Once the noise stopped, one *genuine* over-use surfaced that
had been hidden by the false positives. Related: [[feedback_terse_reports]].
