---
name: feedback-refreshing-is-not-copying-forward
description: "Every line you carry into a refreshed status file is a claim you are re-asserting today — check each against the source of truth, and answer a status question by running the gate, not by reading the file you just wrote"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3cdf4883-8bf7-4ffa-8060-2e328114969d
  modified: 2026-09-16T11:46:11.549Z
---

Refreshing a status file is not editing the changed parts and preserving the
rest. Each line you carry forward you are **re-asserting today**, under today's
date, with your name on it. Check every one against its source of truth — not
just the ones you came to change.

**Why:** on 2026-09-16 a `/lair` STATE refresh carried `Critical path: 0796 →
0795 → 0797` forward untouched. Two of those three were **closed**, one of them
by a PR merged the previous night. One command against `tickets/closed/` would
have said so. The stale line landed on `main`, made the project look further
from release than it was, and hid the one thing actually blocking it. In the
same file I also left "0727 and 0787 are upstream matters, neither ours to fix"
after the author had ruled that morning that both become our pull requests.

The compounding half: when the author then asked "have we advanced or retreated
on the release?", the honest answer needed the acceptance suite **run**, not the
recorded verdict read. Running it took twelve minutes and found a release
blocker — the pause checkbox reporting "Indexing is off" while the sitter
completed all four fixture documents. Answering from the status file would have
reported a release blocked only by paperwork, confidently and wrongly, using a
file I had written myself an hour earlier.

**How to apply:** before a status refresh, resolve every ticket ID in the file
against the tree (`git ls-tree origin/main -- tickets/` shows `closed/`
directly), and re-read any line asserting who owns what against the day's
rulings. When someone asks where a project stands, run the gate that decides it;
a status file is a cache, and the one you wrote yourself is the most persuasive
stale cache there is. Same discipline for generated stamps: rewriting a file
with `Write` destroys what a tool generated into it — `erg new`'s log stamp was
replaced with a hand-typed one four minutes in the future, caught only by
`make ticket-logs`.

Related: [[feedback_a_stale_artifact_reads_as_live]] and
[[feedback_matching_a_stale_number_is_not_confirmation]]; this one is about the
stale artifact you authored, which no freshness check flags.
