<!-- last-reviewed: 2026-06-04 -->
# Session Start

At the beginning of every conversation:

> Setup (env, worktree isolation) is delivered by the SessionStart hook. The hook instructs the model to call `EnterWorktree` before doing anything else.

## 1. Worktree naming and phase announcement

The hook handles worktree entry automatically. When naming the worktree (if prompted), use:

| Context | Worktree name | Phase |
|---------|---------------|-------|
| Fresh conversation, no ticket | `explore-{topic}` | `[→ Imagine]` |
| Ticket reference but no branch | `t{N}-{pid}` | `[→ Plan]` |
| `/hunt N` | `t{N}-{pid}` | `[→ Execute]` |
| Active feature branch + open MR | `t{N}-{pid}` | `[→ Execute]` |
| MR review | `review-{N}` | `[→ Verify]` |

The `{pid}` suffix is a short session discriminator (e.g. `$$`) so two parallel sessions on the same ticket land in distinct worktree paths; legacy bare `t{N}` names remain valid. Resolve `$$` to its literal value with `bash -c 'echo $$'` before calling `EnterWorktree` (its name schema rejects `$` characters), per hunt step 3's recipe.

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

For everything else (source code, data files): if `git branch --show-current` is `main`, stop and switch to a branch first. Exception: manuscript prose in paper repos is co-edited in place in the author's checkout during interactive sessions — see `rules/git.md` § Prose workpackages.

The same trap exists on the Bash surface: prefixing a command with `cd <primary-repo-root> &&` silently lands `git`/`erg` mutations on the primary checkout (on main) instead of the worktree branch. A PreToolUse guard blocks `cd <primary-repo-root> && <mutating git/erg>` during worktree sessions; read-only inspection (`git status`, `git log`) is not penalised, and an intentional primary-repo mutation should use `git -C <path>` rather than a `cd`.

**Parked-cwd trap: `EnterWorktree` resolves the repo from the session base cwd.** `EnterWorktree` (and cwd-dependent skills) target the repo enclosing the *session base cwd* — never wherever the last `cd` landed, since a `cd` inside a Bash call resets after that call. If the base cwd is parked off-project (e.g. left at `~/.claude/projects` by an earlier step or an `ExitWorktree`), the worktree is silently created in the nearest enclosing repo — on 2026-06-19 this put a project worktree inside the harness repo. A PreToolUse guard (`scripts/guard-enterworktree-parked-cwd.sh`, matcher-agnostic) denies both `EnterWorktree` and cwd-dependent `Skill` invocations when the base cwd sits in a git-ignored runtime directory inside a repo. It exits 0 (allow) at a repo root, in a tracked subdir, or outside any repo, so non-git manuscript folders and memory sweeps stay unaffected. After any `EnterWorktree`, run the ownership check: `basename "$(git rev-parse --show-toplevel)"` must match the expected worktree/project name. If the resolved repo is wrong, fall back to manual isolation in the correct repo — `git -C <project> worktree add <project>/.claude/worktrees/<name> -b <branch>` — and drive everything with absolute paths and `git -C`. A `git init` inside the ignored runtime dir does not defeat the deny: the guard walks up from the resolved toplevel to any enclosing repo that ignores it — but a registered `git worktree add` worktree (identified by its per-tree git dir differing from the shared common dir) is exempt, so the harness's own `<repo>/.claude/worktrees/` layout stays allowed (ticket 0317). See tickets 0267, 0306, and 0317.

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

# Refactor validation — byte-compare the artifact, not just green tests

A **pure refactor** — a build/layout/rename change that must not alter output
(moving files, re-cutting a Makefile, renaming a symbol) — is validated by
producing the artifact **before and after on the same inputs and byte-comparing
the content**, not by a green test suite. Tests pass on a refactor that silently
changed or *misplaced* the output; a byte-identical old-vs-new render is the
proof they can't give. This is the [git.md](./git.md) byte-check discipline (old
code vs new code on the *same current data*, never against a committed golden)
applied to build outputs.

- Determinism first: set `SOURCE_DATE_EPOCH` (most toolchains honour it) so a
  timestamp doesn't masquerade as a content diff. If the format still embeds a
  path or build dir, compare *content* (`pdftotext`/`pdfimages` hash, extracted
  text) with a raw byte `cmp` as the strict check — and explain any residual diff
  (metadata-only vs content) rather than waving it away.
- Don't over-apply "let the user run the long build" (a *preference*) into "I
  can't validate this." A clean-room render is often seconds, and the byte-compare
  is exactly what catches the defect a green suite misses (climate-finance-het
  deliverables/ reorg, 2026-07-10: 932 tests green, yet the render wrote to the
  wrong path and a Quarto `output-dir` was dead config — both invisible until the
  old-vs-new render).

# When to Ask the Author

- You're stuck after three different approaches (including expert fan-out).
- The task requires a judgment call outside your domain docs.

# Subagents

- **Don't spawn for simple tasks.** Single-file edits, grep, reading files — work directly.
- **Reviewer decorrelation.** The verify panel never shares the coding agent's model. Minimum: the sibling tier of the same family. Stronger: a different vendor or harness entirely (forge review bot, independent CLI agent, local model). Prefer the most-decorrelated reviewer available for the change's risk level.
- **Pin `model` per-invocation on every fan-out launch — frontmatter does not propagate.** A skill's `model:` frontmatter never reaches the agents it spawns (an Agent-tool child resolves to the session model; a Workflow `agent()` inherits it), so for fan-out it is decorative. Set `model` on each launch: reviewers below the coder tier, mechanical lookups at `haiku`, coders at the top tier. Use the short enum token (`sonnet|opus|haiku|fable`) on a launch — a full `claude-*` id is valid only in frontmatter. `effort` is **not** a launch parameter: a spawned child runs at the *session* effort, not pinnable per-call (set the session effort before a fan-out). Enforced by `tests/test_model_rightsizing.py`; mechanics in memory `feedback_subagent_model_effort_levers`.
- **Max 8 concurrent agents** (authorized 2026-06-08). Beyond that, coordination overhead exceeds the gains. Keep watch: when 3+ agents touch the same file or registry, open a coordination PR first (see Phase 5.0 in raid skill).
- **One well-prompted agent first.** Only add agents when a single agent clearly can't handle the task.

# Reuse gate for autonomous orchestration

Before designing any multi-cycle autonomous orchestration (scheduled loops,
overnight supervisors, wave runners), inventory the existing skills and
runbooks catalog and declare, as part of the run plan, either which existing
piece is reused or why none fits. The declaration is the compliance artifact —
it makes the reuse decision verifiable ex post, where a silent improvisation
is not. (Cost of skipping this, 2026-07-10: an hourly autonomous loop was
improvised from scratch while `nightbeat-supervisor` sat undiscovered in the
catalog, and its static itinerary missed a mid-run child ticket a live queue
would have picked up.)

# Ticket discipline for multi-PR work

**A PR closes every ticket named in its `**Ticket:**` lines.** `erg-pr-merge` closes ALL tickets listed in the PR body's `**Ticket:**` lines — unconditionally, regardless of whether all exit-criteria checkboxes are ticked. One ticket per PR remains the recommended review hygiene; list multiple only when they genuinely land together (e.g. raid-wave filings). The `**Ticket:**` (or bare `Ticket:`) line is the close claim. To cite a ticket without closing it, use `Ticket-ref: tickets/NNNN-...`; for a PR that closes nothing, `Ticket: none`. Title prefixes like `chore(0216):` are subject references, never close claims.

When a ticket has multiple sub-tasks that will land in separate PRs: split into child tickets (one per PR) before work starts. Each child PR closes its own child ticket. The parent ticket stays open until all children are merged.

Do NOT put the same `**Ticket:**` line in multiple PRs unless the intent is to close it on the first merge. Use `Ticket-ref:` for the non-closing PRs.

**Tracking-ticket convention.** When investigation spawns sub-tickets, the
original ticket becomes a **tracking ticket** — leave it open. Create each
sub-ticket referencing the tracker, then edit the tracker to list every child.
As with the planned multi-PR split above, the tracker stays open until every
child is closed — and then closes only after the integration review at `/roar`
step 8 (all children closed → re-read child diffs, run the full suite, verify
exit criteria), not on the bare event of the last child merging.

# Compaction

When compacting, preserve the list of modified files, test commands, and current implementation plan.

# Micro-turn discipline

Batch read-only navigational commands (`git status`/`log`/`diff`, `ls`, `grep`, `cat`) into one compound Bash call rather than spending one turn per command. The 2026-06 trace census measured navigational-plus-idle turn churn at $268/week (exact attribution, 28-day window) with a p99 navigation-run length of 32 consecutive turns — the single largest addressable bucket (trace-doctor phase 4, `docs/trace-counterfactuals-2026-06.md`). Each idle turn re-reads the full accumulated context, so a chain of single-command turns pays the context tax repeatedly for no new work. When a step needs three lookups, run all three in one tool call; never open a chain of consecutive single-navigation turns.

# Writing Skills and Hooks

**Tool-agnostic language**: Skills and rules name *capabilities*, not the current tool that provides them — "schedule a wake-up" not a specific timer-tool name, "delegate to a subagent" not a specific agent-tool name, "list ready tickets" not a specific picker-skill name. The forge case is the canonical instance: never hardcode `gh` commands or GitHub references — "merge request" not "PR", "ticket" not "issue", "forge" not "GitHub". The harness is portable across tool generations; tool names rot, capabilities don't.

**Hook output framing**: Use declarative wording ("Worktree isolation is enabled…") not imperative commands ("INSTRUCTION: call EnterWorktree now"). The model classifies imperative hook instructions as prompt injection and ignores them.

**Concurrency discipline**: Every multi-item skill step declares whether items run parallel-background or sequential-blocking, and states why. Model defaults differ across versions; the skill text is the contract.

**Discoverability-first descriptions**: The first sentence of a SKILL.md `description:` states the plain, unthemed function in the keywords a naive user would search ("Audit test-suite quality…", "Review what the overnight runs did…"). Draconic theming, lore, and harness jargon come after the first sentence. Skill *names* may stay themed — the description's opening sentence is what a user scans to find them. Enforced by `tests/test_skill_descriptions.py`.

# Autonomous Action Rules

**Batch the decisions, then run to the end.** The author's attention is the
scarcest resource in the loop; a spinner is not a deliverable. This is the
interactive counterpart of the supervisor doctrine (autonomous mode trades
supervision for time): interactive mode trades a single dense question round
for a long autonomous tail. When work needs author input, collect every
foreseeable decision into ONE batched question round — frontload the whole
set, up to the tool's limit, with a recommended default per question — then
execute through verification, merge, and cleanup without returning between
steps, delegating waits to background agents, and deliver one report at the
end. Never ask sequentially what could be asked together; never park the
conversation on a wait a background agent could hold. Mid-run returns to the
author are for genuinely NEW scope or destructive/irreversible actions the
batched decisions did not cover — not for progress, not for permission to
continue (author doctrine, 2026-07-11).

**Sweep results are decisions.** When a skill sweep (roar step 3, healthcheck, etc.) returns multiple hits, act directly — file the ticket, open the PR, flag for review. Don't prompt the user to confirm. The data is the decision. Silent no-op if the sweep is empty. In tooling repos, findings below the severity floor (next paragraph) are reported, not ticketed.

**Severity floor for tooling repos.** In a tooling/harness repo (this repo, git-erg), file a ticket only when the defect blocks a merge, corrupts state, or bites a science project. Below that bar: fix it inline in the current change, record it in memory, or drop it — sweeps report such findings, they do not mint tickets for them. When a guard misfires, check whether its defect class has fired recently before patching; prefer deleting the guard (and its tests) over growing it. Science repos keep normal filing. (Author directive, 2026-07-15: the ticket queue had reached equilibrium on second-order tooling work.)

**Loophole found → offer to plug it.** When a gap or loophole is identified (audit, review, user-reported check), don't just report it — immediately offer a concrete fix. Propose either implementing it now or opening a ticket. Reporting without offering leaves the user to ask the obvious follow-up.

**Better approach found → voice it before proceeding.** When you see a stronger approach to the requested task — a strategic fix over the tactical one asked for — say so before proceeding, with the trade-off stated plainly. Voicing the alternative is in scope; silently substituting it is not (that stays governed by `git.md`'s one-change-per-commit). Don't let the bias toward minimal change reduce you to a code producer executing a mediocre plan you could see was mediocre.

**Rename/refactor sweeps cover the full logical unit.** When fixing one stale instance of a renamed term, sweep the smallest containing logical unit (CI step, function, config block) for siblings, and check parallel units (e.g. step 1 vs step 2 in the same workflow). Fix all occurrences in one commit.

**Monster ticket found → propose decompose, not hold or brute-fanout.** A ticket with a large blast radius (touches ~15+ files, or rewrites a symbol/directory that other open tickets or a large import fan-in depend on), a build-gated or real-data exit (`make all`, a DVC repro, a training run), more than one MOA sign-off unit bundled in, or a dependency chain hidden in its prose rather than declared as `Blocked-by` — is neither a scheduling problem to skip nor a parallel-agent problem to fan out; either way it collides with siblings or blows the execute-agent timeout. Draft a tracking/epic ticket naming the blast radius, the partition boundary, any up-front architectural decision, and the wave order — then child tickets each sized to one sign-off unit, each `Blocked-by` its real prerequisite and NEVER the tracker. Autonomous run: file the split directly (the partition is mechanical once the blast radius is known — same standing as "sweep results are decisions"). Interactive session: propose the split to the author first — the partition boundary can be an architectural call the MOA owns, not the MOE's.

# Identity

The Imperial Dragon is not a bird. No avian analogies, ever — in skills, explanations, or naming rationale. Scale, power, taxonomy.
