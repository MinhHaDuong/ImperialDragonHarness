---
name: Multi-space comparison over multi-method
description: When clustering finds no structure, test multiple representation spaces (semantic, lexical, citation) — more informative than comparing methods within one space
type: feedback
---

When clustering methods show no structure (flat silhouette, high noise), the productive question is "does structure exist in a DIFFERENT representation?" not "which clustering method works better?"

**Why:** User suggested testing lexical and citation spaces after semantic clustering showed no structure. This transformed the analysis from "KMeans is unstable" into "climate finance is a continuum — traditions are citation communities, not conceptual clusters." Much stronger finding.

**How to apply:** Before running multiple clustering methods on one representation, check silhouette scores first. If they're near zero, the problem isn't the method — it's the representation. Test alternative spaces (TF-IDF, citation coupling, bibliographic coupling). L2-normalize citation vectors to avoid hub artifacts.
