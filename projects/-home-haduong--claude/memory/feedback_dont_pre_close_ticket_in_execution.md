---
name: feedback_dont_pre_close_ticket_in_execution
description: Don't erg-close+archive a ticket in the execution commit; leave it for erg-pr-merge to close at merge, else its close step no-ops with "no ticket found"
metadata:
  type: feedback
---

Leave the ticket OPEN in the execution commit — let `erg-pr-merge` close and
archive it at merge time (driven by the `**Ticket:**` close-claim line in the PR
body). If you run `erg close` + `erg archive` yourself during execution, the
merge script's close step no-ops with `close: no ticket found for ID NNNN`
(the ticket is already in `closed/`). Harmless but reads as a failure and forces
the manual `gh pr merge <N> --merge` recovery path.

**Why:** the erg pre-commit hook nudges you toward closing early — it rejects a
commit that adds a `Closed:` header while the file still sits in `tickets/`
(must run `erg archive` first). That nudge makes pre-closing feel required. It
isn't: the close claim in the PR body is the mechanism, and `erg-pr-merge` owns
the close+archive+push at merge.

**How to apply:** author the PR body with `**Ticket:** tickets/NNNN-...`, commit
the *work* only, leave the ticket file untouched in `tickets/`. Let the merge do
the close. This is the preventive form of the git.md merge-bounce recovery note
("close: no ticket found on a retry" → finish with `gh pr merge --merge`) — same
resolution, but don't create the condition in the first place. (Bit on IDH 0269,
2026-07-10.) See [[feedback_erg_pr_merge_needs_close_claim]].
