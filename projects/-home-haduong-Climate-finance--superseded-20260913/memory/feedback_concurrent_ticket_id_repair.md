---
name: feedback_concurrent_ticket_id_repair
description: Two sessions repairing the same duplicate ticket ID concurrently create a new duplicate; the cross-PR gate is blind to it by construction
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 59128797-3c56-459e-9142-57f27d820f13
  modified: 2026-07-28T09:15:40.628Z
---

`tickets/AGENTS.md` documents concurrent *allocation* (two sessions call
`erg new`, get the same id). The failure that actually bit on 2026-07-27 was
concurrent **repair**, which the note does not cover and the gate cannot see.

Sequence: a duplicate 0385 sat merged on main. Two sessions found it
independently and both renumbered — one to 0386 (PR #1215), one to 0388
(PR #1216), minutes apart. Result: the same ticket alive at two ids, and a
brand-new ticket colliding with the first renumber. Two correct repairs
composed into a fresh instance of the defect they were repairing.

**Why:** the `cross-pr-ticket-collision` gate compares *open PRs*. Both repairs
targeted something already merged, where that gate is blind by construction —
the same blind spot that let the original duplicate land. Renumbering is an
unsynchronised mutation of shared state, and the standing rule ("seat taken,
move to the next one") says nothing about who moves when both sessions decide
to move.

**How to apply:** before renumbering a duplicate that is *already on main*,
re-fetch and check whether another branch has just repaired it —
`git log --oneline -8 origin/main -- tickets/` shows a repair commit, and
`gh pr list --state open --json files` shows one in flight. If a repair already
landed, adopt its id assignment rather than issuing a second one; the earlier
merge keeps its seat. Then check the whole 4-digit neighbourhood again, not
just your own id — a repair moves *someone else's* ticket onto a seat you may
have taken. Verify with `erg check` against the merged main, not only your
branch: a branch-local check passes while main is broken.

**The pre-check is necessary but not sufficient — the race window is your whole
branch, not just its first commit.** On 2026-07-28 the same defect recurred
despite this note: a duplicate 0371 sat on main, the pre-repair scan came back
clean, and the sibling's renumber to 0470 landed *two commits later*, while the
repair branch was open. The tell is a **rename/rename conflict** on
`git merge origin/main`:

```
CONFLIT (renommage/renommage) : tickets/0371-x.erg renommé en
  tickets/0450-x.erg dans HEAD et en tickets/0470-x.erg dans origin/main
```

Read that as "main already fixed this", not as a conflict to resolve. When the
PR *is* the repair: `git merge --abort`, verify main is clean (`erg check` + a
`uniq -d` over the 4-digit prefixes), then **close your PR as superseded and
delete the branch**. Resolving the conflict is the trap: picking your side
reverts main's repair, picking both mints a third seat for one ticket. When the
PR carries other work (the 0450/0470 case, resolved 2026-07-28): resolve every
hunk **wholly to main's number** — never a third id — and rewrite your own log
line to record the race and the deferral. The earlier merge keeps its seat —
including when "earlier" means it landed after you branched.

Related: [[feedback_regenerate_dont_merge_generated]] — same shape, two agents
independently producing a shared artifact without coordinating on the result.
