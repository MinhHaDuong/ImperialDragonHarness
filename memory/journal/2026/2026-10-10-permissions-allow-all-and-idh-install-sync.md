# Permissions: allow all Bash, and idh install carries them (2026-10-10)

PR #1344 (permissions rewrite plus the install sync) and PR #1345 (ticket 1081).

## Observed
- The author asked for a harness that works on every project, machine and runtime with no Claude auto-blockers in the way. `settings.shared.json` `permissions.allow` went from 36 per-tool entries to `Bash` plus the Gmail read tools, the two worktree tools, `Read(//mnt/snapshots/**)`, `WebSearch` and one own-domain `WebFetch`. The `deny` block and `Edit(~/.claude/settings.json)` are gone.
- A 17-rule `deny` block for destructive git was written first, then removed before merge. An Opus read-only audit of the uncommitted diff found it would block commands the harness runs itself: `git branch -D` in `/roar` step 10 (`skills/roar/SKILL.md:308,334`), `git push --force-with-lease` (`rules/git.md`, `skills/raid/SKILL.md:254`) matched by `push *--force*`, and the clean-tree `reset --hard` in `skills/merge/SKILL.md:60`. It also found `git -C <path> …` bypassed every deny pattern. The pattern semantics were taken from documentation, not tested on the live runtime.
- `register_settings()` (`adapters/lifecycle.py`) merged hooks, `statusLine` and `env`, and never `permissions`; `~/.claude/settings.json` is a regular file, not a link. The second commit of #1344 unions `allow`, `deny`, `ask`, `additionalDirectories` and sets `defaultMode` only when absent. Removals do not propagate. `idh check claude` printed `ok` before and does not report permission drift. Test: `test_install_adds_shared_permissions_and_keeps_operator_rules`; it was not run against the unmodified code.
- `~/.claude/settings.local.json` holds 76 Bash, 34 WebFetch and 22 Read allows and 4 directories; it was counted, not edited. Whether the user-level file is loaded was not established.
- `erg-pr-merge` refused #1344 until the body carried `**Ticket:** none`. Ticket 1081 asks for a measured audit of that requirement. Observed once; the rate is unmeasured.
- After #1345 was opened, `erg-pr-merge` exited with "CI has 10 check(s) still running". The agent then waited for the next user message; the user reported about one hour. `gh pr checks` showed all 10 passing, the slowest at 1m36s.
- `local-ci.sh` ran twice (about 70 s of tests each), once on a ticket-only change. The user asked why writing the 52-line ticket took over 13 minutes; per-step timings were not available.

## Disclosed gaps
- The live `~/.claude/settings.json` and `settings.local.json` on every machine are unchanged; they take the new allows after `idh install`.
- The pruning of `settings.local.json` was planned and not done.
- The Opus audit has no review-attribution record: the runtime exposed only the `opus` token, not a verbatim model id.
