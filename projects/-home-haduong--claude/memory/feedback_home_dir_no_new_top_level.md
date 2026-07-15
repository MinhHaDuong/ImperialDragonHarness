---
name: feedback-home-dir-no-new-top-level
description: Never propose a new top-level directory directly under ~ (home) — reuse an existing one
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 94584887-94e8-41ab-8572-2166f828f51e
---

Never propose creating a new top-level directory directly under `~` (the
user's home directory), even for a legitimate vendor-independence reason
(e.g. keeping personal data out of `~/.claude`). Reuse an existing top-level
directory instead — e.g. `~/data/` already holds project corpora
(`~/data/projets/chemin-de-voix/corpus`) and is the right home for other
personal, tool-independent data too.

**Why:** the user stated this as a hard rule ("~ is a sacred place, don't
even think about proposing a new top dir ever") after a voice-alignment
design discussion suggested `~/voice-corpus/` for a personal writing corpus.
Home directory layout is the user's own to curate, not a place for tooling
to grow into.

**How to apply:** when a design needs a location outside a specific
project/tool namespace, check for an existing top-level directory that
already serves that role (`~/data`, `~/CNRS`, `~/.claude`) before suggesting
anything new. If none fits, ask rather than propose a new one.
