---
name: rename-sweep-test-files
description: Script renames must include test files; grep the test/ directory for every literal string being renamed
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 60765da7-1ecb-410a-9fa2-44e30fdc3bc9
---

When renaming directory names or constants across scripts, always include test files in the sweep. In PR 87 (chunks→extracted, clean→cleaned), the rename agent updated 7 scripts but missed test_clean_corpus.py, and the /verify simplify step had to fix it in round 2.

**Why:** Test files use the same literal strings as scripts. A mechanical rename that only touches scripts/ leaves tests broken.

**How to apply:** Before committing a rename, run:
`grep -rn '"old_name"' scripts/ tests/`
Both directories must be clean before the commit is ready.
