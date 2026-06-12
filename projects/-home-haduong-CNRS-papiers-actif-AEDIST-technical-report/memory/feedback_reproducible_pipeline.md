---
name: Reproducible research pipeline
description: User wants clearly defined, reproducible test harness — not ad hoc scripts
type: feedback
---

Build a reproducible research pipeline. The test harness must be defined and implemented clearly — not a collection of ad hoc scripts but a proper experimental framework.

**Why:** This is a research project aiming at quasi-scientific experimental design. Results must be reproducible (median of 3 runs, controlled variables, recorded cost/latency).

**How to apply:** When writing experiment scripts, design them as a unified harness with clear CLI interface, consistent output format, and documented methodology. Every experiment should be re-runnable with a single make target.
