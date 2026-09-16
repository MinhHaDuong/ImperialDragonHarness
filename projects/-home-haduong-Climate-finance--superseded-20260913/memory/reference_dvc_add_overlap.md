---
name: reference_dvc_add_overlap
description: A DVC output nested inside another makes dvc repro/dag abort at graph construction while every per-target command still reports healthy
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5389b1f5-6e6b-4500-b022-37ae6d8e29fd
  modified: 2026-07-27T19:39:32.721Z
---

DVC forbids one output nesting inside another, and enforces it when it *builds
the graph* — so the pipeline is not degraded, it is refused:

    ERROR: The output paths:
    'data/catalogs/run_reports'('data/catalogs/run_reports.dvc')
    'data/catalogs/run_reports/catalog_merge.json'('catalog_merge')
    overlap and are thus in the same tracked directory.

Fixed on 2026-07-27 (ticket 0430, PR #1228): the stable run report moved to
`CATALOGS_DIR/<script>_report.json`, outside the DVC-tracked `run_reports/`.
`dvc repro`, `dvc dag` and `dvc add` all work again.
`tests/test_dvc_output_overlap.py` now fails on any nested output, reading
`dvc.yaml` plus every `.dvc` file rather than invoking DVC.

**What made this expensive: the workaround worked.** Hitting the error through
`dvc add`, I switched to `dvc commit -f <path>.dvc`, which succeeded, and
recorded it as "the ticket's recipe went stale." It had not: `dvc repro` had
been dead for weeks and the corpus was unbuildable. A workaround that succeeds
removes the pressure to ask *why* the first command failed. When a documented
command suddenly refuses, establish the blast radius before routing around it —
here, one `dvc dag` would have shown the graph itself was broken.

**Why no check caught it.** The failure is in the *declaration*, not the data,
and only graph-building commands see it. `dvc status <path>.dvc`, `dvc commit`,
`dvc push`, and even a bare `dvc status` all succeed and print healthy output.
`dvc.lock` was equally reassuring — the stage had not run since the bad
declaration landed, so the lock never referenced it. To check DVC health, run
`dvc dag` or `dvc repro --dry`; nothing cheaper exercises the graph.

Related: [[feedback_check_the_detector_first]] [[feedback_corpus_rerun_byte_compare]]
