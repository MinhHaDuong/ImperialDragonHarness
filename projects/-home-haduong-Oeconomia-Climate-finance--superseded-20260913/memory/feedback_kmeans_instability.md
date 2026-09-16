---
name: KMeans cluster instability
description: KMeans cluster IDs shuffle with small corpus changes — never use KMeans IDs as stable references
type: feedback
---

Removing 0.6% of works (159/26,426) reshuffled KMeans cluster assignments for thousands of works. SHORT_LABELS mapped to wrong panels, causing a factual error in the submitted manuscript caption.

**Why:** KMeans assigns IDs by proximity to random centroids. Small data changes shift centroids enough to swap cluster numbering. The clusters themselves may be thematically similar but their numeric IDs are arbitrary.

**How to apply:** Never hardcode cluster ID → theme mappings. Use frozen archive data for submitted figures. For future work, evaluate stable alternatives (HDBSCAN, Spectral, BERTopic — ticket #299). When using KMeans, always verify labels match TF-IDF terms before publication.
