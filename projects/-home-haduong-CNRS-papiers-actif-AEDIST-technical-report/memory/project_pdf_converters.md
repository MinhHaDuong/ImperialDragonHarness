---
name: PDF converter architecture
description: Five PDF-to-MD backends planned — 3 shipped (grobid/ollama/openrouter), 2 ticketed (marker/mineru). All containerized except ollama.
type: project
---

PDF converter system has uniform interface: all export `pdf_to_markdown()`, use shared `metadata_comment` from `pdf2md_utils.py`.

Three backends shipped (PRs #80, #86):
- `pdf2md_grobid.py` — GROBID container, academic papers
- `pdf2md_ollama.py` — Ollama local vision, scanned docs
- `pdf2md_openrouter.py` — OpenRouter cloud vision, fallback

Two backends ticketed (#81-#85):
- `pdf2md_marker.py` — Marker container (#83), GPL-3.0
- `pdf2md_mineru.py` — MinerU 3.x container (#84), AGPL-3.0

**Why:** GROBID fails on 16/18 Vietnamese government PDFs (scanned images). Vision-LLM path works but weak on complex tables. Layout-aware tools (Marker, MinerU) detect table geometry structurally.

**How to apply:** Next session starts with #82 (Protocol + registry dispatch), then #83-#84 (containerized backends), then #85 (table benchmark).
