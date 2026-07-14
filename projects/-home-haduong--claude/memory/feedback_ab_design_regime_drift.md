---
name: feedback_ab_design_regime_drift
description: "Live A/B designs in a fast-moving harness void silently — pin full launch-config manifests, compare live head-to-head arms, review the design before authorizing spend"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f10f81b4-1c42-4655-8d4f-bbb8ffedc93c
---

The trace-doctor phase-5 A/B (ticket 0245) was authored 2026-06-10 and
reached first authorized spend 2026-07-14 with five unfrozen variables:
effort level absent from the arm definitions (global `effortLevel: high`
applied silently; traces do not record effort), the gaze battery re-tiered
mid-study (0320), the "Opus mains" premise obsolete (beat defaulted to
Sonnet in April; Fable replaced Opus as the session default), the paired
per-ticket baseline unobservable inside shared raid sessions, and a stale
PR join cache. The author voided the design at the smoke replay and dropped
the arc.

**Why:** arms were defined by narrative ("a Sonnet main"), not by config; a
historical corpus is not a control arm when the regime turns over monthly;
and the two premise gates in the pipeline (ticket Action-1 "confirm or
revise with reasons", raid Imagine phase) rubber-stamped because
questioning the *what* was framed as drift (fixed by 0336/PR #597 —
premise objection is now a success outcome of Imagine).

**How to apply:** define an experimental arm as the full launch-config
manifest enumerated from the live surface (`claude --help` flags plus
settings keys: model, effort, permission mode, gaze tier, harness SHA);
freeze everything not under test and diff the arms — a forgotten variable
is then an unfrozen line, not a mid-study surprise. Compare live
head-to-head arms on identical inputs, never against a historical
baseline. Adversarially review the design document for unfrozen variables
BEFORE authorizing spend. Keep design-to-data latency inside one wave.
Related: [[feedback_pin_intervention_surface_to_measured_window]].
