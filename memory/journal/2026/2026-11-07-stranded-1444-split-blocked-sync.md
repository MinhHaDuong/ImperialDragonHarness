# Stranded 1444 split blocked the local-main sync — 2026-11-07

Context: on padme, `sync-local-main.sh` refused to fast-forward the primary
checkout because of a tracked edit to ticket 1444, plus untracked tickets
1445, 1446 and 1447. Their file times (2026-11-02 16:33–16:47 +0100) and
`Author: reviewer` show a split of 1444 into three children, drafted by a
session and never committed.

Observed: main was 75 commits ahead. Over those five days, IDs 1445 and 1446
had gone to unrelated tickets (git notes, test targets). 1444 had moved on
too: log lines and a README / authoring-guide change (310223ae, b5c1383a)
that already covered each child's guidance criterion.

Actions: backed up the draft to the session scratchpad, restored 1444 from
HEAD, then synced (5971d810 -> 7680ddb0). At the author's request, re-filed
the children as 1453, 1454 and 1455 and kept 1444's upstream log lines. Each
child's guidance criterion is ticked against the landed text, and 1453's
import-probe exception is aligned with it. PR #2228 merged as ae8ed51b, a
bookkeeping-tier change with no review. The old untracked drafts were
deleted from the primary checkout.

Coordination: a doudou `.agents` session holds PR #2229 (tickets 1377 and
1440–1442), so there is no ID overlap. It was not reachable by cross-session
messaging, so a note went on PR #2229 instead. Untracked ticket 1452 on
padme belongs to the live smelt-run session and was left untouched.
