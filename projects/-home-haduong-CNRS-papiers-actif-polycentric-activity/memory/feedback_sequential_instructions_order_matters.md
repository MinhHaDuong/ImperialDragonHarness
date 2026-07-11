---
name: feedback-sequential-instructions-order-matters
description: Apply multi-part instructions in the given order — a later part (e.g. a tool switch) can redefine the design space of an earlier part.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 00f42d32-9617-4639-b3b5-e14ec6e85a97
---

2026-07-08: User asked (1) teach clean/cleaner recipes to sub-Makefiles, then (2) switch builds to tectonic. I designed clean/cleaner against pdflatex leftovers, then bolted tectonic on — leaving a `clean` that swept aux files tectonic never writes while the PDF (the build's only product) survived. User: "Tu as inversé l'ordre de mes consignes du coup c'est pas clean."

**Why:** Instruction order carries design intent. A later instruction that changes the toolchain/environment invalidates assumptions baked into the earlier one; designing them out of order produces recipes that reference a world that no longer exists.

**How to apply:** When a request has sequenced parts, execute in the stated order, and after any part that changes the environment (build tool, framework, data source), re-derive the earlier parts' design from the new world before committing. Check each recipe/config against what the *current* toolchain actually produces.
