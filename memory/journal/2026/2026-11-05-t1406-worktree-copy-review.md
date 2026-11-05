# Ticket 1406 — worktree setup-copy review

PR #2216 changed the cleanup preflight to recognise setup copies and links to
the primary checkout. The first gaze review reproduced a data-loss case: the
apparent primary file could itself point to the only copy inside the worktree
being removed. Commit `69585ca492e8e7957ff3861d453fe1929ae6a835` rejected
counterparts resolving inside the candidate worktree and added tests for both a
direct link and a linked parent directory.

The second gaze confirmed the fix on both cases. Its integration fallback had
one intermittent forge-cache failure; the same test passed in isolation. The
gate then ran the integration fallback in a checkout with an independent Git
common directory: 1,556 passed and five skipped. The gate approved the closed
ticket head; PR #2216 merged on 2026-11-05.
