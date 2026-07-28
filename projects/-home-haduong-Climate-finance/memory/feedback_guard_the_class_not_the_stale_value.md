---
name: feedback_guard_the_class_not_the_stale_value
description: A guard that forbids the specific stale value blesses the next wrong one; forbid the shape that goes stale
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e1a2a449-f55d-4143-847e-e015213fee2a
  modified: 2026-07-27T18:41:27.505Z
---

When a value goes stale and you add a test so it cannot come back, forbid the
**class of value**, not the instance you just removed. A guard listing the old
string passes happily on the next wrong string.

Concrete case (ticket 0327, 2026-07-27): the deposit title said "Six Sources"
while the corpus had eight. The repair wrote "Eight Sources" and added
`TestSourceCardinality` with `STALE = ("six sources", "Six Sources", …)`. That
guard would have blessed "Eight Sources" forever — and "eight" is stale at the
next harvest, exactly as "six" was. The author's fix removed the count from the
title entirely; the guard now rejects *any* spelled-out source count in the
paper and the archive README, and the number lives in prose as
`{{< meta corpus_sources >}}`.

**Why:** the defect is not "the number is six", it is "a number is pinned in a
place that does not regenerate". Guarding the instance encodes the symptom and
resets the clock; guarding the shape ends the class.

**How to apply:** after writing a stale-value guard, ask "what value would make
this test pass but still be wrong in a year?" If such a value exists, widen the
guard to the shape, or remove the pinned value from the artifact and derive it.
The tell is a `STALE = (...)` tuple of literals where a pattern belongs.
Counter-example of a correct one: `test_script_hygiene.py`'s `FORBIDDEN` holds
regexes for the anti-pattern shape (`setattr(utils,`), not for one offender.

Related: [[feedback_union_only_defects]], [[project_datapaper_release_actions]],
[[feedback_check_the_detector_first]].
