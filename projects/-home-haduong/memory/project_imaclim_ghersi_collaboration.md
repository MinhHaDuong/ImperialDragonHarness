---
name: project-imaclim-ghersi-collaboration
description: "Minh's informal collaboration with Frédéric Ghersi (CIRED) on IMACLIM-R France bugs"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0fd81a80-6f76-4edb-96dd-d65b58ebdeb6
  modified: 2026-09-22T14:19:47.331Z
---

Minh proposed helping fix bugs on an IMACLIM country model (Scilab), motivated
purely by mutual aid and contributing to the collective effort — not a code
review to publish or an audit. Preferred pace: close one bug a day, not a
rewrite. Meeting with Frédéric Ghersi planned Thursday 2026-09-24 afternoon.

Context: the CIRED GitHub org (`github.com/CIRED`) hosts three public IMACLIM
Scilab repos (`IMACLIM-R_France`, `IMACLIM-R_World`, `IMACLIM-Country`) under
open licenses (GPL-3.0 / AGPL-3.0 / CeCILL v2.1), but with near-zero PR
activity (2/0/0 respectively despite 11 contributors on `IMACLIM-Country`) —
they function as a diffusion channel, not a collaborative dev workflow, and
appear to be frozen snapshots (`IMACLIM-R_France` last commit 2025-12-15,
`World` 2026-02-06). Frédéric says the *current* working code is now
proprietary (work of Laurent Faucheux) and underlies paid country-model
contracts (IMACLIM UE with SMASH, IMACLIM Turquie with Natixis; in progress:
Sénégal, Nigéria, Tunisie; possible Vietnam revival). No open GitHub issues
track known bugs on `IMACLIM-R_France` — bug knowledge is informal/tribal so
far.

Frédéric's counter-proposal was to hand Minh a full formal spec (equations +
variable/parameter list) and have AI reimplement in Python before doing the
"review" — rejected in this session's technical discussion as riskier than a
line-by-line bug-compatible port, since the `.tex` docs are ~11 months stale
relative to the code (last touched 2024-10-30 vs. code 2025-12-15) and a
clean-room-from-equations reimplementation loses the diff-based validation
seam against the existing Scilab reference.

**Why:** sets expectations for any future session picking this back up — the
open-question for Thursday's meeting is just repo access + review circuit for
Minh's contributions (which repo, propriety code or the public snapshot,
who merges), not a publication or IP negotiation.

**How to apply:** if Minh reports back after the Thursday meeting, treat that
as the authoritative update to this entry — don't re-derive from the emails.
