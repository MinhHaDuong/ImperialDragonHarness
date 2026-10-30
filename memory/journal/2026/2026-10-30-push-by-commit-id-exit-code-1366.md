# A push by commit id needs no read-back (PR 2035, follow-up to 2033)

Context: PR 2033 fixed ticket 1366 by pushing the gate record by commit id
from a per-process ref, and added an `ls-remote` read-back after every push
with a one-second second look (about 90 lines, one forge round trip per
record). See 2026-10-30-gate-record-lost-shared-ref-rewind-1366.md.

Events:
- The author asked whether the fix was KISS; PR 2035 kept the commit-id push
  and dropped the read-back, the second look and their four tests. Gaze
  (redteam openai/gpt-6.1-sol) REVIEWED, verify-gate APPROVED round 1.
- The gate flagged that dropping the read-back departs from rules/git.md
  "Verify a forge mutation by reading it back". The author merged anyway and
  declined to narrow the rule: the distinction below is memory, not rule.

Facts:
- `git push <remote> <commit-id>:<ref>` moves the remote ref atomically or is
  refused (non-fast-forward included), so its exit code is the read-back.
- `git push <remote> <ref>:<ref>` can exit 0 having sent nothing when another
  process rewound the local ref first (ticket 1366); a push by name is the
  case the read-back rule still covers.
- Forge read lag with commit-id pushes yields refused pushes and a loud
  GateError after two attempts, not a silent loss. A rare true loss is caught
  by `main_sweep.py --after` and stays in the notes reflog for about 90 days.
