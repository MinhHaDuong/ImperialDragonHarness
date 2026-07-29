---
name: Companion paper method design
description: Lean 6-method panel for multilayer-detection.qmd (epic 0026), QSS target
type: project
originSessionId: 6028d794-8c6f-418a-85d8-eedb55e43fed
modified: 2026-07-29T07:06:12.779Z
---
`content/multilayer-detection.qmd` (renamed from companion-paper.qmd in #737).
Reimagined 2026-04-15 as methods+application paper for QSS.
Lean design: 6 methods across 3 layers, not the 16-method zoo.

| Layer | Lead | Robustness |
|-------|------|------------|
| Embedding | Energy distance | C2ST on PCA-32 |
| Lexical | JS divergence | C2ST on TF-IDF |
| Graph | Community div (Louvain+JS) | Spectral gap |

Key design decisions:
- Permutation null CI ribbons (B=500); raw statistic values plotted (ticket 0113 drops Z-score rescaling)
- Null ribbon = null_mean ± 1.96*null_std in native units; no cross-year standardisation in zoo figures
- Significance: year outside ribbon = p < 0.05 (two-sided)
- Transition zones (year ranges), not point breaks — social change is fuzzy
- Two-pass censored-gap confirmation: detect zones, censor, retest
- C2ST gives interpretation for free (discriminative terms + documents)
- companion-paper.qmd stays standalone (NOT merged into tech report)

**Why:** User pushed back on statistics-paper framing and method zoo. The paper
is a companion to the Oeconomia intellectual history, not a benchmark.

**How to apply:** Methods must serve the narrative, not the other way around. Supplementary material holds the other 12 zoo methods. §5 prose (§5.1–5.4) not yet written — known RED tests in test_multilayer_detection_prose.py and test_multilayer_detection_pca.py.

**UPDATE 2026-07-23 (author, RDJ revision session):** "Y a pas de companion
paper" — the author does not want to multiply papers. The only two outlets are
the RDJ data paper and the Œconomia article (which the data paper cites as
[Ha-Duong, under review]). Do not route findings to a separate
methods/structuration paper; interesting results go into the data paper
(minimal, statistic-backed items) or the Œconomia article at its next
revision round. The multilayer-detection.qmd plan above is dormant until the
author says otherwise.

**UPDATE 2026-07-29 (author):** Zoo and multilayer reports are *potential
future articles* — not active submissions, not mere internal references.
Priority stays with the RDJ-26561 resubmission (due ~2026-10-20). Author's
summer vacation starts 2026-07-30; expect a low-activity window.
