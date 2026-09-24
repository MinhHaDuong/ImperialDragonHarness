---
name: clean-room-before-live-install
description: Every sitter build gets the acceptance smoke tests on the Multilingual Menagerie in a clean environment first; the author installs on his live Zotero only after I confirm a pass
metadata:
  node_type: memory
  type: feedback
  originSessionId: b87a9f19-6e44-43d9-a91e-3488202c9aa2
  modified: 2026-09-23T08:16:44.296Z
---

Before any sitter build goes near the author's live Zotero, run the acceptance
smoke tests on the Multilingual Menagerie in a clean environment (throwaway
profile and data directory: `bench/sitter_smoke_test.py` / `make sitter-smoke`,
and `bench/sitter_acceptance.py`), and report the verdict. He installs on his
live Zotero only after I confirm the pass. Never propose "run it in your live
Zotero" as the first test.

**Why:** stated by the author 2026-09-23, after I suggested he run the 0.4.31
acceptance script in his live Zotero. His live library is the instrument he
works in; an untested payload must not be its first test.

Ratified the same day as a ladder (DECISIONS.md 2026-09-23,
`plugins/sdt-sitter/TESTING.md`): unit → smoke → Menagerie → clone (reflink
copy of his library) → dogfood, and no release before he has used it himself.
The clone rung is required before EVERY live install, release or not. Never
call the Menagerie rung "acceptance": acceptance is his own use.

**How to apply:** for every candidate release or "is it ready?" question, run
the clean-room pair yourself first, quote the result, and only then hand over
the live install. Related: [[project_live_smoke_recipe]],
[[project_sitter_install_paths_on_doudou]].
