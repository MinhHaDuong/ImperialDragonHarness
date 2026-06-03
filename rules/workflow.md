<!-- last-reviewed: 2026-06-03 -->
# Session Start

At the beginning of every conversation:

> Setup (env, worktree isolation) is delivered by the SessionStart hook. The hook instructs the model to call `EnterWorktree` before doing anything else.

## 1. Worktree naming and phase announcement

The hook handles worktree entry automatically. When naming the worktree (if prompted), use:

| Context | Worktree name | Phase |
|---------|---------------|-------|
| Fresh conversation, no ticket | `explore-{topic}` | `[→ Imagine]` |
| Ticket reference but no branch | `t{N}` | `[→ Plan]` |
| `/start-ticket N` | `t{N}` | `[→ Execute]` |
| Active feature branch + open MR | `t{N}` | `[→ Execute]` |
| MR review | `review-{N}` | `[→ Verify]` |

After `EnterWorktree` succeeds, emit the phase label on its own line (e.g. `[→ Execute]`) so the user sees which Five-Claws claw is active.

After entering the worktree, run `git switch <branch>` (or `git switch -c <branch>`) to land on the correct branch. The worktree is throwaway — all durable state lives in branches.

## 2. Sync before starting work

Before substantial work — **not just before branching** — fetch and scan for parallel or already-merged work:

```bash
git fetch origin
git log --oneline HEAD..origin/main         # what landed upstream since your base
git diff --name-only origin/main...HEAD      # files you'd touch that upstream also changed
```

If `origin/main` is ahead and overlaps your area, reconcile first (rebase onto it, or cut a fresh branch from `origin/main`) **before writing code**. Skipping this risks reinventing work that parallel raid/nightbeat agents already merged — it bit once (2026-05-26): an entire ticket's fixes were duplicated, less completely, from a base ~15 commits stale, caught only at PR time. The fetch is cheap; the rework is not. (To test whether a path exists at a ref, use `git cat-file -e <ref>:<path>` — `git ls-tree <ref> <path> && …` exits 0 even when the path is absent.)

# Worktree paths

During an `EnterWorktree` session, `Edit`/`Write`/`Read` tools accept any absolute path. An edit at `/home/haduong/<repo>/<file>` lands in the **main repo**, not the worktree. Use worktree-rooted paths for code, prose, and data.

**No exceptions. Everything goes through a PR.** `STATE.md`, ticket lifecycle, memory files, config — all changes land via branch + PR. The GitHub gate is closed; there is no direct-push-to-main path.

For everything else (source code, manuscript prose, data files): if `git branch --show-current` is `main`, stop and switch to a branch first.

# Escalation Protocol

When stuck, escalate progressively:
1. Fix direct — review feedback is straightforward.
2. Alternative approach — rethink the solution.
3. Parallel expert agents — fan-out different directions.
4. Re-ticket with diagnosis — the problem is mis-specified.
5. Stop — ask the author.

Save a feedback memory at each escalation (what failed, why). Stop if repeating yourself.

# Diagnosis discipline

Report the **observation**; hold the **cause** until you have isolated it. Don't
reach for loaded causal labels — *corrupt*, *broken*, *tampered*, *hacked*,
*hazard* — before evidence rules the cause in: they misdirect the fix (reinstall
vs reword) and manufacture false alarm. Before blaming a tool, check the cheap
discriminators: is it intact (package-verify / hash)? deterministic? does an
independent code path reproduce it? does upstream document the behaviour? Any
"yes" points away from corruption toward *intended behaviour*. State "X emits Y
for input Z; cause not yet established," not a verdict dressed as a finding.
(Cost of skipping this, 2026-06-03: a stock gofmt doc-comment smart-quote
feature — intact binary, deterministic, reproduced by the stdlib — was
misdiagnosed as a "broken toolchain" and nearly got a spurious reinstall ticket.)

# When to Ask the Author

- You're stuck after three different approaches (including expert fan-out).
- The task requires a judgment call outside your domain docs.

# Subagents

- **Don't spawn for simple tasks.** Single-file edits, grep, reading files — work directly.
- **Reviewers use a different model than the coder.** Sonnet reviews Opus's work; different blind spots catch more.
- **Max 4 concurrent agents.** Beyond that, coordination overhead exceeds the gains.
- **One well-prompted agent first.** Only add agents when a single agent clearly can't handle the task.

# Ticket discipline for multi-PR work

**One PR closes exactly one ticket.** `erg-pr-merge` closes whatever ticket appears in the PR body's `**Ticket:**` line — unconditionally, regardless of whether all exit-criteria checkboxes are ticked.

When a ticket has multiple sub-tasks that will land in separate PRs: split into child tickets (one per PR) before work starts. Each child PR closes its own child ticket. The parent ticket stays open until all children are merged.

Do NOT put the same `**Ticket:**` line in multiple PRs unless the intent is to close it on the first merge.

# Compaction

When compacting, preserve the list of modified files, test commands, and current implementation plan.

# Writing Skills and Hooks

**Forge-agnostic language**: Never hardcode `gh` commands or GitHub references in skills or rules. Use "merge request" not "PR", "ticket" not "issue", "forge" not "GitHub". Skills describe *what* to do, not *which tool* to use.

**Hook output framing**: Use declarative wording ("Worktree isolation is enabled…") not imperative commands ("INSTRUCTION: call EnterWorktree now"). The model classifies imperative hook instructions as prompt injection and ignores them.

# Autonomous Action Rules

**Sweep results are decisions.** When a skill sweep (celebrate step 3, healthcheck, etc.) returns multiple hits, act directly — file the ticket, open the PR, flag for review. Don't prompt the user to confirm. The data is the decision. Silent no-op if the sweep is empty.

**Loophole found → offer to plug it.** When a gap or loophole is identified (audit, review, user-reported check), don't just report it — immediately offer a concrete fix. Propose either implementing it now or opening a ticket. Reporting without offering leaves the user to ask the obvious follow-up.

**Rename/refactor sweeps cover the full logical unit.** When fixing one stale instance of a renamed term, sweep the smallest containing logical unit (CI step, function, config block) for siblings, and check parallel units (e.g. step 1 vs step 2 in the same workflow). Fix all occurrences in one commit.

# Identity

The Imperial Dragon is not a bird. No avian analogies, ever — in skills, explanations, or naming rationale. Scale, power, taxonomy.
