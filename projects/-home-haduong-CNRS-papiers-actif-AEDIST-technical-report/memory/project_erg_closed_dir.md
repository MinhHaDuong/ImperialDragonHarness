---
name: erg auto-archives closed tickets to tickets/closed/
description: erg close triggers batch archival of all Closed:-header tickets to tickets/closed/; Blocked-by refs to archived tickets break validation
type: project
originSessionId: a8674d80-1e78-499e-aa96-f5a6a8574fb9
---
The v2 erg binary (`tickets/tools/go/erg`) auto-archives ALL tickets with `Closed:` headers to `tickets/closed/` when `erg close <id>` is run. This is a side effect of the close operation — it reorganizes the full tickets/ directory.

**Why:** Discovered 2026-05-05 during celebrate/end-session: running `erg close 0163` archived 126 closed tickets (0001–0161) to `tickets/closed/` as an untracked batch move. This required a manual commit.

**How to apply:**
- After `erg close`, expect `git status` to show many "D" deletions in `tickets/` and an untracked `tickets/closed/` directory. Stage with `git add -A tickets/` and commit.
- `tickets/closed/` is validated by the erg binary (not by `scripts/check_ticket_structure.py`).
- Cannot move tickets with `Blocked-by: NNNN` when NNNN is already in `tickets/closed/` — the erg validator rejects unknown ticket refs. Leave those tickets in `tickets/` or strip the Blocked-by line first.
- The erg binary also generates `.claude/CLAUDE.md` with ticket system docs — commit this file (it's not gitignored).
