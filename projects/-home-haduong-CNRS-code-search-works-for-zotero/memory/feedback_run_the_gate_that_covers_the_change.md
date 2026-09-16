---
name: run-the-gate-that-covers-the-change
description: "Merged a red gate because I ran the gates I knew rather than the ones covering the diff I had written — .mjs suites and the version gate, never pytest"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f7d7cc4a-5b20-40a1-9710-3d81ce55aa58
  modified: 2026-09-15T05:12:28.624Z
---

PR #566 (ticket 0791, 2026-09-14) landed on `main` red. Before merging I ran
the four `.mjs` sitter suites and `bench/check_sitter_version.py`, all green,
and did not run `pytest tests/test_sdt_sitter.py`. That suite holds
`test_no_ui_site_keeps_a_sentence_of_its_own`, and my change had put the text
of a UI message into a code comment — one home per string, which is exactly
what that test guards. `main` stayed red for about two hours.

The gates I ran were the ones I had been running all day. The gate that covered
what I had actually changed — prose inside `bootstrap.js` near the message
table — was the one I skipped.

**Why:** proportionality is about matching the gate to the diff, and it cuts
both ways. Skipping `make check` on a prose-only ticket edit is right; skipping
the suite that reads the file you just edited is not proportionality, it is
habit wearing its clothes. "I ran gates" is not the same claim as "I ran the
gates that could have caught this", and only the second one licenses a merge.

**How to apply:** before merging, ask which test file *reads the file I
changed*, and run that one — `grep -rl <changed-file> tests/` answers it in a
second. On this repo a change anywhere in `plugins/sdt-sitter/` means
`tests/test_sdt_sitter.py` as well as the `.mjs` suites; the Python suite is
the one that reads the source as text and enforces the string-and-comment
invariants the `.mjs` suites cannot see.

Related: [[rerun-gate-after-own-fix]] is the adjacent failure — re-running a
gate *on its own fix*. This one is choosing the wrong gate in the first place.
