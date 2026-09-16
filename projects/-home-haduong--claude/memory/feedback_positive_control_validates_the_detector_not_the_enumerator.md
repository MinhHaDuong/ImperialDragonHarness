---
name: feedback_positive_control_validates_the_detector_not_the_enumerator
description: "A positive control proves you can recognize the thing when you see it; it says nothing about whether you looked at the whole population, so cross-check the denominator against an independent count"
metadata:
  type: feedback
---

Measuring `/gaze` runs across repos on 2026-09-10, a probe was validated against
four PRs known to carry telemetry footers. It fired, so the probe was trusted —
and it was wrong by a factor of two. It enumerated `pullRequests(last:100)` while
`search-works-for-zotero` had **510** PRs updated in the window: the sample
covered four days out of thirty, and the conclusion drawn from it ("gaze is
essentially a single-repo tool") inverted once repaginated. Actual: 32 of the
runs were in that repo against 20 in the harness.

The same session repeated the shape twice more. A grep for callers of
`trace_ab_harvest.py` omitted `--include="*.yml"` and returned only docs and
tests, nearly justifying the deletion of 716 lines that
`skills/reviewers/benchmark-board.yml` actively calls. And a "scripts referenced
only by docs" detector returned zero — correctly, as it turned out, but only
after being run against a case known to be positive, which is what exposed the
`.yml` omission.

A fourth instance, 2026-09-16, moves the failure one step closer in: the
enumerator can be a *filter inside your own pipeline*. Measuring which
credentials `bash -x` leaks, the probe piped the trace through
`awk 'length(val) >= 16'` to skip noise. It reported five exposed variables. The
real count was six — `HAL_PASSWORD`'s value was shorter than the threshold. The
positive control had fired, the grep was sound, and the number was still wrong,
because the threshold was silently part of the population definition. The
undercount was announced to the author before a second pass caught it, and it
was load-bearing: it scoped a credential rotation.

**Why:** the positive control answers "can I recognize a hit?" and is silent on
"did I look at every candidate?". Those are different failures with the same
symptom — a plausible, complete-looking result. The enumerator fails quietly
because a truncated page and a full one are indistinguishable in the output;
nothing says "there were 410 more".

**How to apply:** validate the detector AND the denominator, separately. Count
the population by an independent path — `gh pr list --search` versus a GraphQL
walk, `wc -l` versus the tool's own total — and reconcile the two numbers before
believing any rate. Paginate by cursor until the window is exhausted rather than
taking `first/last:N`, and print the span the sample actually covered (min..max
timestamp), which is what made the four-days-of-thirty truncation visible at a
glance. For a grep-based inventory, list the file types you excluded and ask
whether the thing you are looking for could live in one. Where the probe
carries a threshold, a length cut or a `head`/`tail` of its own, name it as part
of the population definition and run the measurement once without it: a
convenience filter added to reduce noise is an enumerator nobody reviews. Related:
[[feedback_enumerate_untracked_with_status_uall]] (a probe returning *everything*
hides a broken parse the same way), [[feedback_measure_whether_a_guard_ever_fired]].
