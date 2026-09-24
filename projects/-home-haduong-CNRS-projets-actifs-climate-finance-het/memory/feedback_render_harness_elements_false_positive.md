---
name: feedback_render_harness_elements_false_positive
description: "The observatory render harness logs getElementById lookups under \"elements\"; grep only \"main\" when probing for injected markup"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 36288e08-760c-498d-809d-4ea0d872d521
  modified: 2026-09-23T18:58:18.727Z
---

`node tests/_jetp_observatory_render.js <site> '<route>'` returns JSON with `main` (rendered HTML) and `elements` (a record of every `getElementById` lookup, keyed by the id string requested). An XSS probe that greps the whole output for `<img` fires on `elements` whenever the router looks up an id built from the address (e.g. `#glossary?term=…` scrolling to `term-<param>`) — harmless, since a lookup renders nothing.

**Why:** on 2026-09-23 the #1462 gate showed img=1 for two payloads; only `main` matters, and it was clean.

**How to apply:** probe `json.load(...)['main']`, and keep a positive control (a known-unescaped variant) to prove the probe can fire.
