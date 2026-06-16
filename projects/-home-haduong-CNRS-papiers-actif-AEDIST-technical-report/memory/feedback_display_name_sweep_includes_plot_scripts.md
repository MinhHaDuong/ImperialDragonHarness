---
name: feedback_display_name_sweep_includes_plot_scripts
description: "Stale model/display-name fixes in prose must sweep figure-generating label maps too, and disambiguate vs genuinely-different registry entries"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e6272c1e-8db3-4722-a5d7-ca195f81cf04
---

When fixing a stale model display name in manuscript/report prose (e.g.
`Qwen3-Max` → `Qwen3.7 Max`, tickets 0584/0594), the defect class extends
beyond `.tex`/`.md` to **figure-generating scripts** — `src/aedist/plot_*.py`
carry label dicts like `{"qwen": "Qwen3-Max"}` that render the stale name into
a manuscript figure via `\includegraphics`. The 0594 `/roar` sweep caught one
(`plot_exp2_coverage_certainty.py:55`) live in a `main.tex` figure → ticket 0596.

**Why:** prose-only sweeps miss the rendered-figure surface; a label map is just
as much a display-name source as a sentence, and figures are first-class artifacts.

**How to apply:**
- Sweep target for any display-name rename: `*.tex *.md *.yaml *.toml` AND
  `src/aedist/plot_*.py` label/legend maps.
- Disambiguate before fixing: the same token may legitimately name a *different*
  registry entry. `Qwen3-Max-Thinking` (`qwen3-max-thinking`) and OpenRouter
  `qwen3-max` are genuinely different `models.yaml` entries — leave them. Confirm
  the arm's slug from a run-record, never assume (see [[feedback_no_invented_names]]).
- Never edit archived run-records (`experiments/archive/outputs/`) or protocol
  specs (`experiments/sota/`) — immutable experimental record.
