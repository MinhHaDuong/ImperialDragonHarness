---
name: compute-before-figure
description: Run throwaway data computation before writing figure code — catches prose claim errors and design risks early
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 00c8918d-a72c-42bc-b74c-adebb21672fb
---

Run a short throwaway script against the raw data before writing any figure script. Catches:
- Prose claim errors (e.g., "2–7 months" was actually 0.9–4.8 months)
- Design risks (N=3 for some cells when ticket assumed N=5)
- Surprising findings that reshape the figure design

**Why:** Advisor called this out before 0246 figure work; the check took 15 lines of Python and caught a §3 factual error before it reached the PR.

**How to apply:** Whenever a new figure reads from a data file, write the computation inline first, check against existing prose claims, then write the script.
