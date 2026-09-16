---
name: GROBID on padme
description: GROBID runs locally via podman on padme for bibliography parsing — 200 citations/sec, port 8070
type: reference
---

GROBID 0.8.1 runs on padme via podman (rootless container):

```bash
podman run -d --name grobid -p 8070:8070 docker.io/lfoppiano/grobid:0.8.1
```

- API: `POST http://localhost:8070/api/processCitation` with `citations=<text>&consolidateCitations=0`
- Returns TEI XML with structured bibliographic fields
- Throughput: ~200 citations/sec (7ms each on padme hardware)
- Used by: `scripts/parse_citations_grobid.py` (#538)
- Cache: `enrich_cache/grobid_parsed.jsonl` (keyed by text hash, survives re-runs)

**How to apply:** When parsing unstructured citation strings, use GROBID — two orders of magnitude faster than LLM (5ms vs 300ms-2000ms), gold-standard quality, no API cost.
