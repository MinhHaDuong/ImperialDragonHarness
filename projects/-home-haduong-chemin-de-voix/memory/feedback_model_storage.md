---
name: model-storage-location
description: "Store ML model files in /data/models/, never in project directories"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a11b63b8-e69e-40d9-aaaa-44a002663528
---

Always store model files in `/data/models/`, never inside the project directory tree.

**Why:** Project dirs are for code and data artifacts; large model weights don't belong there. `/data/models/` is the designated location on PADME.

**How to apply:** When downloading or referencing models, use `/data/models/` as the base path. HF cache (`~/.cache/huggingface/hub/`) is acceptable for cached downloads. Don't create `models/` subdirs inside `~/chemin-de-voix/` or `~/data/projets/chemin-de-voix/`.
