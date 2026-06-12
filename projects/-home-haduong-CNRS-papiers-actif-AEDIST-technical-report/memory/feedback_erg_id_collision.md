---
name: erg-id-collision-across-branches
description: "erg new IDs allocated on a branch can be re-allocated by parallel sessions on main — land ticket files fast, re-run erg check after every rebase"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9f2627e7-d2c9-4b17-8993-714c70f8b232
---

`tickets/erg new` allocates IDs atomically only within one checkout. Two parallel
sessions (branch + main) both got **0421** on 2026-06-04: mine (skill update-publist,
on the t412 branch) and a nightbeat session's (render-rules, landed on main via PR #713).
No corpus breakage only because mine had already been moved to IDH and deleted
before merge.

**Why:** ID allocation is per-checkout; the corpus-level duplicate guard (`erg check`
in CI) only fires when both files reach the same tree.

**How to apply:** Land new ticket files on main quickly (quickpr) instead of letting
them ride a long-lived feature branch; after every rebase onto origin/main, re-run
`tickets/erg check tickets/` before pushing; when a ticket moves to another repo,
delete the local file in the same session. [[econom-ia-2026-presentation]]

**2026-06-12 recurrence:** bit again (0566) when the orchestrator hand-wrote ticket
files with IDs read off origin/main while a raid executor's branch held an
unmerged `erg new` allocation of the same ID. Worse: `erg check && quickpr` did
not stop the push (PATH-erg version skew exited 0 on the violation). Always
allocate via `tickets/erg new` (the repo-committed binary, never hand-pick IDs
even for orchestrator-authored tickets), and validate with `./tickets/erg check`,
not the PATH `erg`.
