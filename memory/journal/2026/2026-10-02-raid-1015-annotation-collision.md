# Raid 1015: cross-session annotation collision on the shared checkout (PR #1138)

A `/raid 1015` (the hermeticity guard's UNTERMINATED check, filed the same
morning from the 0875 sweep) ran the full eight-phase loop on 2026-10-02
while a second raid session worked its own 4-ticket wave on the same machine
and the same main checkout.

The raid's Phase 2-4 annotations were committed to local main (repo rule:
pushes to main are declined, so they sat unpushed). The parallel session's
wrap PR (#1139, "raid wave wrap — scorecards (0207) and 1015 annotations")
then landed its own copies of those annotations on origin/main, re-attributed
("reviewer", its own timestamps), taken from the shared working tree. When
PR #1138's auto-merge was queued, main had moved and the PR went
CONFLICTING: origin/main held the parallel copies at the open ticket path
while the branch held the original-attribution version plus the close/archive
rename. The rebase resolved it without manual conflict: git skipped the
annotation commits as cherry-picks already on main, and the archived ticket
carries the union — the parallel session's landed log lines plus the close
header.

No content was lost: the two versions carried the same annotation text, so
the collision cost one rebase and a force-with-lease, not a merge failure.
The class, though, is structural: two raid sessions committing ticket
annotations to the same unpushable local main will race, and the second
session to land wins the attribution. The cheaper discipline for future
parallel waves: commit phase annotations on a short-lived branch or land them
with the wave's own wrap PR, rather than parking them on main where another
session's wrap will sweep them up under its own authorship.

The 1015 delivery itself: controls 0q/0r pin the verdict priority (an exempt
suite with an unterminated heredoc answers UNTERMINATED, demonstrated red
live with "expected 'UNTERMINATED', got 'EXEMPT'" before the break removal),
the sentinel is consumed in the verdict read loop, and the cross-tool
byte-contract class opened by the 0875 runner incident is now closed on the
whole ref — no verdict-deciding path anywhere re-parses an awk-built stream
with grep, and no other such contract exists in scripts/ or tests/.
