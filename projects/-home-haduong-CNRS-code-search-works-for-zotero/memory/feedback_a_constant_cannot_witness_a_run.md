---
name: feedback-a-constant-cannot-witness-a-run
description: "A hardcoded warm: true satisfies a guard specified to read the code path that ran; all six bench drivers write the literal, two with no derived witness at all"
metadata:
  type: feedback
---

When a guard's contract says a field is **set from the code path that ran**, a
literal in the emitter satisfies the guard and defeats it in the same line. The
guard goes green forever, which is worse than red: a provenance field that cannot
vary carries no provenance, and everything downstream is quoted as if it did.

**The instance, 2026-09-02.** `bench/check_figures.py` documents `warm` at its
definition: *"``True`` — the driver did a warm pass, and set this from the code
path that ran."* `bench/extract_chunk_throughput.mjs:563` writes `warm: true` as
a literal, with `warm_basis` a static string beside it. The driver's warm-up is
in fact **conditional** (`warmKeys.length ? await serialPass(warmKeys) : null`),
so the flag is true whether or not the pass happened. Thirty-three quoted figures
rest on that artifact.

**The independent proof the artifact is not that driver's output.** The committed
driver emits a `warm_up` object (line 596) recording the discarded slice.
`bench/results/0500-extract-chunk/extract-chunk-throughput.json` does not have
that key. A field the emitter always writes, absent from the artifact, is
mechanical evidence of a version skew no `warm: true` could ever reveal. **Look
for the key that must be present, not the value that must be right** — the
literal cannot be wrong, so it cannot be a test; the missing key can only come
from a different run.

**The class, swept 2026-09-02.** Six drivers write the literal:
`embed_feasibility.mjs:123`, `extract_chunk_throughput.mjs:563`,
`quant_fidelity.mjs:154`, `query_embed_cost.mjs:147`, `recall_embed.mjs:145`,
`service_ceiling_rss.mjs:401`. **Zero** derive it. The split that matters is the
witness beside it, not the literal:
- Four (`embed_feasibility`, `quant_fidelity`, `query_embed_cost`,
  `recall_embed`) run an unconditional warm pass and emit `warm_ms` **measured
  from that pass**. The flag is redundant; the witness is real. Acceptable.
- Two have no witness. `extract_chunk_throughput` gates its warm-up on a
  condition; `service_ceiling_rss` declares `warm: true` while its warming is a
  **separate optional invocation** (`--warm`, `default: false`) that the emitting
  run cannot observe at all. These are the two to fix.

**How to fix the shape, not the instance.** Set the flag from the variable the
warm path assigns (`warm: warmed !== null`), or drop the flag and let the guard
read the witness key. And when specifying a provenance field, write the contract
so a constant *fails* it: require the derived quantity (`warm_ms`, `warm_up`),
not the boolean, since only the derived quantity can be absent.

**A guard already exists; do not propose a second one.** `tests/test_warm_before_timing.py`
(ticket 0260) enforces this class already — but by **source inspection**, because the
drivers need corpora absent from the repo. It asserts a driver warms *before its timing
window*, reading the code. `check_figures.warm_verdict` reads the *artifact*. Neither
crosses the gap between them, and that gap is the whole defect: nothing checks that the
artifact on disk was produced by the driver in the tree. A source-inspection guard is
structurally unable to see a version skew, so the fix is not a third guard but a witness
key in the artifact that the existing artifact-side check can require.

One level down from [[feedback_verify_the_load_bearing_claim]]: not a claim
nobody executed, but a claim a machine re-checks on every run and can never
falsify. See also [[feedback_guard_the_silent_failure_first]] and
[[feedback_warm_runs_and_single_point_fits]].
