---
name: no-ruff-ping-pong
description: "Author directive — no edit/formatter ping-pong; a PostToolUse ruff hook reformats after EVERY Edit, so multi-step edits race it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6e423984-6613-4698-bb69-cfb19dcf5c54
---

Author said "NO PING PONG WITH ruff" (2026-06-10) after an edit cycle broke a file.

**Why:** A PostToolUse hook runs ruff (with unused-import removal) after every single Edit/Write. Splitting one logical change across two Edit calls means the hook sees the intermediate state — e.g. step 1 adds `import re`, step 2 uses it: the hook strips the "unused" import between them, producing a NameError and a fix-up round-trip the author has to watch.

**How to apply:** Write new files complete and lint-clean in ONE Write call. For changes to existing files, batch all related edits so no intermediate state has unused imports/variables. After the hook fires, trust it — don't re-lint reflexively; run tests once at the end of the batch.
