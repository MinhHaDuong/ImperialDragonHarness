# Purge automatic harness refresh

The author chose a one-shot purge rather than filing ticket 1552 from PR #2499:
“Cleanup, purge drop the idea of auto-harness refresh.”

On doudou, claude-refresh.timer was enabled and claude-refresh.service failed
with its working directory pointing at the missing ~/.idh. This session disabled
the timer, cleared its failed state, deleted both user unit files, and reloaded
systemd. Direct read-back reported both units LoadState=not-found and inactive,
with no enablement link or failed claude-refresh unit remaining. Padme had
neither unit. A search of the current installer found no claude-refresh reference.
No replacement timer or installer migration was added.

PR #2499 was closed without merging. PR #2500 removed the obsolete daily-pull
timer comment from scripts/check-primary-checkout.sh. Non-comment bytes matched
the base exactly; bash syntax passed, the script-only gaze plan passed, nine
touched tests passed, and the before-merge checks passed on padme.

The conversation initially inspected historical PR #1552 instead of the ticket
proposed in PR #2499. The author corrected the target. An unrelated bounded wake
probe had already been armed; its message later reached this conversation.

Writer identity: this session’s runtime turn_context reports model gpt-6.1-sol
and effort medium. The gaze used a script check, without a model reviewer seat.

Attribution capture reported “not derivable: reviewers” for this script-only
plan and produced no attribution file. The writer identity was saved on review
notes; no model reviewer identity is claimed.
