---
name: project_axis_is_unimodal
description: "The efficiency–accountability axis score is unimodal; ΔBIC was measuring non-normality, not two communities"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82aac5fe-ddfd-4e93-afb5-d90fabf6f6cf
  modified: 2026-07-27T12:51:13.413Z
---

Measured 2026-07-27 (ticket 0330, PR #1146), the first time the Hartigan dip
test ever ran in this project — `diptest` had been undeclared, so the import
always failed silently.

On n=29,675 axis scores: dip p = 1.0000 overall, 0.9943 / 0.9942 / 1.0000 for
1990–2006 / 2007–2014 / 2015–2024. Dip statistic 0.00098, about six times
*below* the 1/√n null scale — not a low-power near-miss.

Why ΔBIC=1355 said otherwise: the axis score is skewed (0.59) and leptokurtic
(excess 1.11), and the two-component GMM that wins the BIC comparison has its
components 0.84σ apart, putting **one mode** in the fitted density. A
two-Gaussian mixture needs ~2σ separation to have two humps; the script never
checked. ΔBIC was detecting departure from normality.

Consequences for the writing:

- **Resolved 2026-07-27** (ticket 0345, PR #1151, merged). §5.3 was retitled
  "The efficiency--accountability axis" and now states a continuum; §5.4's
  "polarisation" clause says the axis and flags that PC2's own ΔBIC carries the
  same caveat. `bim_dip_p_*`, `bim_gmm_separation` and `bim_gmm_modes` are
  pipeline variables now, so the claim is vars-driven.
- Separation is below 2σ in **every** period (0.84 overall; 1.84 / 1.40 / 1.08
  by period) and the mode count is 1 in all four. Not a post-2015 artifact.
- Quarto does not expand `{{< meta >}}` inside `$...$`. The old
  `$\Delta BIC_{\text{emb}} = {{< meta ... >}}$` emitted a raw shortcode span
  and killed xelatex — the multilayer paper had not rendered for some time.
  Keep meta refs outside inline math.
- The **Œconomia manuscript is not exposed** — verified. It quotes no `bim_*`
  variable; its two-pole material is historical (`@tbl-poles`) and A.6
  validates the axis by *venue ecology*, not by a distributional claim. The
  "bimodal curve" at l. 86 is `@fig-breaks` (thematic renewal speed over time),
  a different object.
- The defensible claim is a **continuum along a real axis**, not two camps:
  the axis is externally valid (embedding/lexical agree at r=0.77, ends
  concentrate in different journal ecologies) but there is no gap in the middle.
- The per-period ΔBIC comparison is separately confounded with n: 19 vs 1118
  raw is 4.6×, not 59×, per observation.

Do not cite ΔBIC alone as evidence of bimodality anywhere in this project.
Related: [[feedback_verify_vars_file_provenance]], and ticket 0344 (Phase-2
tables stale against the corpus, found by the same byte-compare).
