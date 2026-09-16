---
name: Teaching pipeline methodology lessons for data paper
description: Key findings from building the teaching scraper — worth documenting in data paper and code comments
type: project
---

Lessons from the 2026-03-22/23 teaching pipeline session, relevant for the data paper methodology section:

1. **Regex > LLM for DOI extraction**: gemma-2-27b-it only extracts 24% of DOIs visible in PDF text. A simple regex `10.\d{4,}/...` catches 100%. Hybrid approach (regex first, LLM for title-only refs) is essential.

2. **CrossRef > OpenAlex for title→DOI**: CrossRef found ~500 DOIs per 1500 lookups. OpenAlex fulltext search returns wrong matches for bibliographic queries — it searches title+abstract+fulltext, not title alone. Author appended to OpenAlex search query actively hurts results. Use CrossRef as primary, OpenAlex as fallback.

3. **Chunk size matters**: 8K char chunks work with gemma-2-27b-it, 20K causes 0 extractions from dense bibliographies. Model-dependent — needs calibration.

4. **LMS harvesting bias**: NYU Stern syllabus says "readings on Brightspace" — structurally unreachable. Business schools publish public syllabi, development/policy programs use institutional LMS. This biases the teaching canon toward finance/business perspectives.

5. **No text truncation needed**: The original TEXT_LIMIT was solving a non-problem — make_chunks() handles splitting. Truncation only loses data.

**How to apply:** Items 1, 2, and 4 belong in data-paper.qmd §2 methodology. Item 4 is already partially covered in §2.3 but should mention the LMS mechanism explicitly. Items 1-3 should be code comments in collect_syllabi.py.
