---
name: feedback_skeptical_advisor_before_new_guard
description: "No new guard (test, check, validator view) is proposed or merged without a skeptical advisor challenging it first; the author asked for fixes, not guards"
metadata:
  node_type: memory
  type: feedback
  originSessionId: eae976b8-5082-4ce8-97e1-6c05a93a8951
  modified: 2026-09-29T16:15:27.980Z
---

Before proposing or merging a new guard, send it to a skeptical advisor: an agent on a model other than the coder's, briefed to argue against it and to test whether it fails on revert, pins typed constants or text patterns, or duplicates what a fix already removes. Only survivors reach the author, with the advisor's objection beside each. A build-time assertion counts as a guard, but it is admitted when it fails loud (ERROR on stderr, a count line) and never blocks (exit 0, the bad item omitted, nothing hidden in the served output).

**Why:** on 2026-09-29 (0870 integration review) the author asked for anomalies to be fixed and got detector designs and guard proposals instead ("I was not asking for more guards, I was asking for fixing the items. Rule: ask advisor before proposing new guards", then "a _skeptical_ advisor"). The advisor then deleted or rejected most candidates: a test that could not fail on revert (numba pre-warm, PR #1571), guards pinning typed counts 145 and 30 (register dispositions, PR #1574), a legacy-readers guard that misfired on a living file name (deleted in PR #1572 rather than grown). The author ruled the same day that build-time asserts are fine "provided they fail loud and do not block".

**How to apply:** in any brief to a team-lead, say "no new test guard; build-time asserts may fail loud but must not block"; when an agent adds one anyway, route it to the advisor before asking the author. When a guard misfires, offer deletion first. See [[feedback_guard_the_class_not_the_stale_value]], [[feedback_red_test_the_guard_you_wrote]], [[feedback_author_is_not_the_checker]].
