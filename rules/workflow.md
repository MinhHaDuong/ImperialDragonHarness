<!-- last-reviewed: 2026-06-04 -->
# Session Start

At the beginning of every conversation:

> Setup (env, worktree isolation) is delivered by the SessionStart hook. The hook instructs the model to call `EnterWorktree` before doing anything else.

## 1. Worktree naming and phase announcement

The hook handles worktree entry automatically. When naming the worktree (if prompted), use:

| Context | Worktree name | Phase |
|---------|---------------|-------|
| Fresh conversation, no ticket | `explore-{topic}` | `[→ Imagine]` |
| Ticket reference but no branch | `t{N}` | `[→ Plan]` |
| `/hunt N` | `t{N}` | `[→ Execute]` |
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

The same trap exists on the Bash surface: prefixing a command with `cd <primary-repo-root> &&` silently lands `git`/`erg` mutations on the primary checkout (on main) instead of the worktree branch. A PreToolUse guard blocks `cd <primary-repo-root> && <mutating git/erg>` during worktree sessions; read-only inspection (`git status`, `git log`) is not penalised, and an intentional primary-repo mutation should use `git -C <path>` rather than a `cd`.

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

**A PR closes every ticket named in its `**Ticket:**` lines.** `erg-pr-merge` closes ALL tickets listed in the PR body's `**Ticket:**` lines — unconditionally, regardless of whether all exit-criteria checkboxes are ticked. One ticket per PR remains the recommended review hygiene; list multiple only when they genuinely land together (e.g. raid-wave filings). The `**Ticket:**` (or bare `Ticket:`) line is the close claim. To cite a ticket without closing it, use `Ticket-ref: tickets/NNNN-...`; for a PR that closes nothing, `Ticket: none`. Title prefixes like `chore(0216):` are subject references, never close claims.

When a ticket has multiple sub-tasks that will land in separate PRs: split into child tickets (one per PR) before work starts. Each child PR closes its own child ticket. The parent ticket stays open until all children are merged.

Do NOT put the same `**Ticket:**` line in multiple PRs unless the intent is to close it on the first merge. Use `Ticket-ref:` for the non-closing PRs.

**Tracking-ticket convention.** When investigation spawns sub-tickets, the
original ticket becomes a **tracking ticket** — leave it open. Create each
sub-ticket referencing the tracker, then edit the tracker to list every child.
The tracker closes only after the integration review at `/roar` step 7 (all
children closed → re-read child diffs, run the full suite, verify exit
criteria), not when the last child merges.

# Compaction

When compacting, preserve the list of modified files, test commands, and current implementation plan.

# Writing Skills and Hooks

**Forge-agnostic language**: Never hardcode `gh` commands or GitHub references in skills or rules. Use "merge request" not "PR", "ticket" not "issue", "forge" not "GitHub". Skills describe *what* to do, not *which tool* to use.

**Hook output framing**: Use declarative wording ("Worktree isolation is enabled…") not imperative commands ("INSTRUCTION: call EnterWorktree now"). The model classifies imperative hook instructions as prompt injection and ignores them.

**Concurrency discipline**: Every multi-item skill step declares whether items run parallel-background or sequential-blocking, and states why. Model defaults differ across versions; the skill text is the contract.

**Discoverability-first descriptions**: The first sentence of a SKILL.md `description:` states the plain, unthemed function in the keywords a naive user would search ("Audit test-suite quality…", "Review what the overnight runs did…"). Draconic theming, lore, and harness jargon come after the first sentence. Skill *names* may stay themed — the description's opening sentence is what a user scans to find them. Enforced by `tests/test_skill_descriptions.py`.

# Autonomous Action Rules

**Sweep results are decisions.** When a skill sweep (roar step 3, healthcheck, etc.) returns multiple hits, act directly — file the ticket, open the PR, flag for review. Don't prompt the user to confirm. The data is the decision. Silent no-op if the sweep is empty.

**Loophole found → offer to plug it.** When a gap or loophole is identified (audit, review, user-reported check), don't just report it — immediately offer a concrete fix. Propose either implementing it now or opening a ticket. Reporting without offering leaves the user to ask the obvious follow-up.

**Rename/refactor sweeps cover the full logical unit.** When fixing one stale instance of a renamed term, sweep the smallest containing logical unit (CI step, function, config block) for siblings, and check parallel units (e.g. step 1 vs step 2 in the same workflow). Fix all occurrences in one commit.

# Identity

The Imperial Dragon is not a bird. No avian analogies, ever — in skills, explanations, or naming rationale. Scale, power, taxonomy.
