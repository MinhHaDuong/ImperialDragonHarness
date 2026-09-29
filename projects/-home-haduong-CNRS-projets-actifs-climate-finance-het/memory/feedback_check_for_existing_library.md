---
name: feedback_check_for_existing_library
description: "Periodically ask whether a home-made component is already done better by an existing library or tool; the author's research is not infrastructure"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2d60f2a1-01f1-453b-a627-5228aea3a0c3
  modified: 2026-09-29T08:27:50.410Z
---

From time to time, audit home-made machinery by asking: is this already done
better in a library or an established tool? The author (2026-09-29): "Reinventing
EDM is not my research goal." The first application of this check moved the
JETP document store to a Zotero group library (tickets 1510, 1511), because
Zotero offers a stable data model and plugins, and the author cites the
documents from Zotero anyway.

**Why:** home-made infrastructure (document management, caches, fetchers)
costs upkeep that does not advance the history-of-economics research. A
library brings a maintained data model and an ecosystem.

**How to apply:** when the author asks "is there a library for X", treat it
as due diligence, not a proposal. Name the candidates, compare them against
what already exists (including tools the author already uses, e.g. Zotero),
and give a recommendation with odds. Keep in the repo only what is research
data (provenance, observations), not the management layer. Check the claims
against the repo before filing: the per-country PDF parsers looked like
reinvention, but they are layout-specific research code (ticket 1512,
deferred). Related: [[feedback_no_heavy_deps]], [[feedback_purpose_built_over_llm]].
