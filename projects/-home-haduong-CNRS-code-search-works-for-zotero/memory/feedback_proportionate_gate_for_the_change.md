---
name: feedback-proportionate-gate-for-the-change
description: "Match the gate to the diff — a full make check on a prose or ticket edit wastes the author's clock."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f7d7cc4a-5b20-40a1-9710-3d81ce55aa58
  modified: 2026-09-14T10:44:47.474Z
---

The author, twice on 2026-09-14: *"Proportionality. Edited release notes, what is
to gate?"* and *"We cannot work if you stop 15mn every other prompt."*

**Why:** `make check` in this repo is ~90 s of 1,400 tests plus 84 mutants plus
the JS suites. On a prose or ticket-only diff none of it can be affected, and the
cost lands on the author's wall clock in an interactive session. Running it
reflexively is not rigour, it is not thinking about what changed.

**How to apply:**

| diff touches | gate |
|---|---|
| `RELEASE-NOTES.md` and other prose | `pytest tests/test_sdt_sitter.py -k disclosed` + `bench/check_figures.py` — under a second |
| `tickets/**` only | `tickets/erg check tickets/` + `bench/check_ticket_logs.py` |
| `plugins/sdt-sitter/**` payload | full `make check` — version gate and mutants are live |
| anything, before a merge | full `make check`, once |

The merge gate still earns the full run. The iteration loop does not.

Same session, same complaint: he had just cut RELEASE-NOTES.md from 680 lines to
50 and I inserted an 11-line bullet into it — *"WTF did you add textwalls?"*
Match the register of the document you are editing, and when a defect is found in
shipping prose the answer is usually one line plus a ticket, not a paragraph.
See [[feedback-decision-briefs]].
