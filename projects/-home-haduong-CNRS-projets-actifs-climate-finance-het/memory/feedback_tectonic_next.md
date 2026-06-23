---
name: Use Tectonic instead of Quarto for next paper
description: User frustrated with Quarto full-rerender behavior; wants Tectonic (incremental LaTeX) for next project
type: feedback
originSessionId: be8aa033-fcba-4d45-933d-2863514380e8
---
Quarto rerenders everything when any dependency changes. For a project with many analysis scripts feeding into multiple documents, this means long build times on every change.

**Why:** The make → quarto render pipeline has no incremental rendering. Changing one include triggers a full PDF rebuild of every document that uses it.

**How to apply:** For the next paper/project, use Tectonic (Rust-based incremental LaTeX engine) with plain .tex files instead of Quarto .qmd. Keep the Makefile-driven pipeline for analysis, but output LaTeX directly instead of going through Quarto's rendering layer.
