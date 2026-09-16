---
name: feedback_sweep_beats_guard_for_prose
description: "A prose defect class is closed by a repo-wide sweep, not a standing guard — the guard is one spelling behind and costs lines forever; author rejected 115 test lines for two phrases"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 64492b53-3182-47c5-af4a-905183c6c5ef
  modified: 2026-07-28T13:00:58.448Z
---

Ticket 0338/0590 (2026-07-28): the data paper asserted that multilingual
embeddings "place all works in a shared semantic space regardless of
language" — a property of the model's *training objective*, stated in the
indicative as a measured outcome nobody had measured. Calibrated to "is
trained to place".

The class had **three** live instances across two deliverables. Review found
one. A drafted guard found the second. The `/roar` sweep found the third —
which the guard would have missed, because the guard matched `semantic space`
and that sentence said `same space`.

The guard was written (115 lines: pattern, whole-document test, two red-tests)
and reverted at the author's direction: *"115 lines guarding two phrases.
Enough said."*

**Why:** a prose claim has no data signature, so the only available instrument
is a source-text pattern match — and that is always one spelling behind. Each
new synonym needs a new pattern, so the guard accretes lines forever while
still missing the next instance. The sweep costs nothing, runs at wrap-up when
the class is freshly in mind, and reads every file at once. See
[[feedback_static_guard_cannot_replace_an_invariant]]: where a defect *has* a
data signature, assert the property in the code path; where it has none, do
not substitute a weaker static check and call the class closed.

**How to apply:** on a prose defect, fix every instance and sweep the whole
tree for the class at `/roar` step 3 — that sweep is the deliverable, not a
guard. Reach for a standing prose guard only when the class has recurred
*after* a sweep already cleared it. Two shaping notes if it ever is written:
key it on the **distinguishing feature** (here, presence of an attribution
verb) rather than on topic vocabulary, or it fires on a methods paper whose
subject *is* that topic and gets deleted within a week; and check the span
bounds — a 60-character window between verb and phrase caught one instance and
silently skipped its sibling, where a language list sat in between.

The project's polarity rule (`.claude/rules/writing.md`) permits negative
prose guards. Permitted is not proportionate. Related: the severity floor in
`.claude/rules/workflow.md` — machinery that watches for a class is the thing
not to proliferate. Commits `5816bd0b` (add) / `662ee83f` (revert) keep the
guard recoverable.
