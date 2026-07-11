---
name: user-single-bib-database-preference
description: "Author wants one shared refs.bib per project — no per-manuscript bib files, no filecontents-embedded bibliographies."
metadata: 
  node_type: memory
  type: user
  originSessionId: 00f42d32-9617-4639-b3b5-e14ec6e85a97
---

2026-07-08: offered the choice, the author rejected the split het-refs.bib design outright ("Splitter la base de données du projet et intégrer un fichier dans un fichier ne m'enchantent pas du tout"). Unified into refs.bib (PR #9).

**Why:** one database is easier to maintain and audit; a filecontents* block hides entries inside a .tex file where bib tooling cannot see them.

**How to apply:** new manuscripts cite `../refs.bib` directly. Manuscript-specific entries go in a banner-marked section of refs.bib. When the same work needs two bibliographic identities (original vs reprint, working paper vs journal), keep two distinct keys side by side with cross-referencing notes and a warning not to cite both in one manuscript — see the "HET companion" banner in refs.bib. Related: [[feedback-sequential-instructions-order-matters]].
