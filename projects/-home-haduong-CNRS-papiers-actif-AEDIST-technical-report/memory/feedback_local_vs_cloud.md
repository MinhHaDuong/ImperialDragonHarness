---
name: Local vs cloud as research question
description: Always pair one local model with one frontier cloud model through all sweeps
type: feedback
---

Keep one local model alongside one online frontier model through ALL experiment sweeps (not just census). "Can local do it?" is a key research question.

**Why:** The report is about feasibility for countries with limited resources. If a local model on modest hardware (A4000 + 128GB RAM) can match or approach cloud frontier quality, that's a major finding. The cost comparison (free vs $15/Mtok) is central to the assessment.

**How to apply:** When selecting top-5 models for Sweep 2+, always include the best-performing Padme local model alongside cloud frontier. Carry this pair through multiturn, RAG, web, and verification sweeps.
