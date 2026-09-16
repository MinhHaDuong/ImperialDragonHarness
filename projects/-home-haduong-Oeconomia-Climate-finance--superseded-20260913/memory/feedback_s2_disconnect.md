---
name: S2 keyword search is wrong tool
description: Semantic Scholar should be used via citation graph, not keyword search — disconnected from pipeline
type: feedback
---

S2's /paper/search endpoint treats multi-word queries as OR (not phrase match). "adaptation fund" returns 2.1M results. The 1000-result cap means we get a random sample of noise. The bulk search endpoint supports quotes but we weren't using it.

**Why:** S2 is a semantic engine, not a keyword database. Its value is the citation graph, paper recommendations, and SPECTER embeddings — not keyword matching.

**How to apply:** Don't re-enable S2 keyword harvest. Pool data preserved in data/pool/semanticscholar/. Future S2 integration should use seed-based citation graph expansion or /recommendations endpoint. OpenAlex already indexes RePEc, so economics working papers are covered.
