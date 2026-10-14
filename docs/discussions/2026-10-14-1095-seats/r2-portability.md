**Option 1 — approve as observability, not lifecycle management.**

Round-1 objections answered: the scan now includes configured temporary storage, caches and registered worktrees; acknowledges unreadable entries; reports both filesystems; and avoids hook, session-ID and age-based deletion dependencies. Project-test leaks are explicitly distinguished from harness cleanup.

Remaining by runtime:

- **Claude Code:** “runtime temp root” needs an explicit discovery/configuration contract. A familiar `claude-<uid>` pattern cannot establish ownership or completeness.
- **Codex:** read-only seats can inspect accessible roots, but sandbox restrictions may prevent a complete census. Report inaccessible roots separately from an empty result. No managed-scratchpad equivalent is required.
- **Pi:** reporting `pi-bash-*` answers visibility, not their lifecycle. The scan must locate the parent process’s actual temporary root; a command’s `TMPDIR` can differ.

New defects: “owner ticket N, repo unknown” overstates what the filename proves; use “ticket-like name N; ownership unverified.” Overlapping roots need deduplication. The mode-000 control is not reliable under privileged execution; test permission failures deterministically or under an unprivileged identity.

**Verdict:** portable and useful with those clarifications. It neither prevents exhaustion nor closes temporary-storage lifecycles, as the revision now acknowledges.

**Option 2 — stronger than round 1, but still conditional.**

Round-1 objections answered: removing the proposed purge eliminates the new pre-WIP deletion defect. Plain Git replaces runtime-owned worktree APIs as the basis. Read-only seats are exempt, disk-transfer risk is acknowledged, and Option 1 accompanies the change. The supplied Git 2.43.0 probe establishes that ordinary removal deletes an ignored `.tmp/`; that point is now demonstrated.

Remaining by runtime:

- **Claude Code:** plain-Git creation still does not retarget the session’s tool root. Shared scratch and detached consumers remain outside reliable ownership detection. Native scratchpad use outside worktrees remains a separate lifecycle.
- **Codex:** writable `.tmp/` does not imply permission to update common Git metadata or remove sibling worktrees. Launch into the selected tree with permitted roots. A rule placed only in `rules/workflow.md` also needs an explicit loading path: repository observations show Codex does not automatically ingest `rules/`.
- **Pi:** explicit cwd selection remains necessary. Per-command `TMPDIR` still misses parent-generated bash logs and extension temporaries. It also does not eliminate socket-path limits for child tools using the longer worktree path.

Shared unresolved objections: `[gone]` is not merge proof; `/proc/*/cwd` misses consumers elsewhere; PID ownership remains unvalidated. Calling these existing defects does not establish the hard preservation guarantee. A size report adds no liveness protection. The Git probe tests deletion semantics, not those rails.

New weaknesses: evidence protection is still a convention plus an agent assertion. Crash GC has no equivalent evidence-promotion check before deletion. Codex/Pi’s shared `<primary>/.tmp/` lacks per-task separation and any close operation. Existing `.panel` purge ordering also remains unfixed.

**Verdict:** accept the storage convention provisionally; do not endorse automatic disposal as satisfying the brief until ambiguous liveness and evidence retention fail closed. Option 1 can proceed independently.