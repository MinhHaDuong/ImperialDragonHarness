# Design history moved from docs/ to conception/ (PR #1744)

Date: 2026-10-27. Project: .agents (harness). Merge: af05be6d.

Context: an external paper staged for Zotero (King & Worthington 2026,
"Peerless") sat untracked in docs/ among 282 tracked design files, because
.gitignore re-included docs/** while rules/zotero.md declares docs/ git-ignored
staging. The author ruled: docs/ stays staging, design history moves to
conception/, as in climate-finance-het, JETP-observer and
search-works-for-zotero.

Events:
- References were rewritten by exact top-level name of the moved files
  (214 replacements, 111 files), leaving generic docs/ mentions alone.
- Five hash-pinned records refused rewriting: the dream-ledger journal entry
  (test_dream_v8), the memory hoards (relocation ledger in
  test_memory_v8_pilot), the PR 1211 capture draft (test_attribution_record)
  and the harness-doctor control fixture (sha256 pin). They were restored
  byte-identical; the two link checkers now map docs/X to conception/X when
  the relocated file exists.
- test_memory_v8_pilot clones committed HEAD, so it failed until the move was
  committed.
- A rebase carried the rewrite into ticket 1250 after main archived it; an
  amend restoring it was denied by the auto-mode classifier ("Git
  Destructive"); a separate commit restored the closed ticket's wording.
- Gate: make check on the merged tip, 2430 passed, 4 skipped. Merged without
  /gaze at the author's instruction ("no ceremony").

Open: the author is weighing a global rename of conception/ to design/
(notes/ also floated); not decided.
