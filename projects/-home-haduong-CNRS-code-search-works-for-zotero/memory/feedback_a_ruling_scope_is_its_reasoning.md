---
name: a-ruling-scope-is-its-reasoning
description: "\"No precision knob upstream\" was contextual — precision cannot travel alone — not a blanket ban on knobs; re-read the ground before applying a ruling to a changed world"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6c21d767-95a0-4e11-8ec4-b9730449bfdb
  modified: 2026-09-03T11:41:14.821Z
---

The 2026-08-29 ruling reads "no per-axis embedder knobs upstream; the ask is a
registry." I carried it as a blanket ban and argued against shipping
`ZOTEUS_EMBEDDING_POOLING` on that authority. The author corrected me: he had
expected the knob.

**Why:** The ruling's ground was that *precision cannot travel alone* — a dtype
knob without pooling, templates and per-repo availability hands the user a
setting whose likeliest outcome is a wrong conclusion about a good model. By
2026-09-03 upstream had shipped `ZOTEUS_EMBEDDING_MODEL`, `_PREFIXES` and
`_DTYPE`, so the axis no longer travels alone. The reasoning had expired; the
slogan had not, and I applied the slogan.

**How to apply:** Before invoking a ruling against a proposal, re-read the
argument under it and ask whether the facts it rested on still hold. A ruling
made about a configuration of the world does not automatically govern a different
one. State the ground when citing it ("withdrawn because precision cannot travel
alone") rather than the conclusion alone — quoting the ground is what makes an
expired premise visible.

**The resolution, which is the reusable design move:** the maintainer's own
`ZOTEUS_EMBEDDING_PREFIXES` is an escape hatch on top of a layer that is right by
default (an inference from the model id). The pooling equivalent is an escape
hatch on top of a curated table — same architecture, different oracle, because
for pooling an inference is impossible (the ONNX mirrors publish no
`1_Pooling/config.json`). Copying the target's own two-part idiom beats both a
bare knob and a purist table. See [[registry-not-knobs]] for the original ruling
and [[a-question-is-not-a-directive]] for the sibling misread in the same session.
