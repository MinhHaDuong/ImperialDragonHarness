# Audit — worktree isolation vs ownership (ticket 0252)

Nightbeat audit, 2026-07-12. Read-only; fix tickets deliberately NOT filed —
the ticket's exit criteria require an author discussion of the ownership
model first. Decision requested: ratify the A+C-now, B-design-later model or
amend.

Thesis confirmed: every guard checks the weak predicate ("cwd is some
worktree") where the material predicate is ownership ("MY registered,
unmutated worktree"). Test incidents: I1 = deregistered worktree, bare git
falls through to the primary repo; I2 = sibling checks out its branch in a
foreign worktree path.

## Audit table (condensed; 15 surfaces swept)

| Surface | Predicate actually checked | I1 | I2 |
|---|---|---|---|
| SessionStart hook (`on-start.sh`) | none — advises EnterWorktree | no | no |
| EnterWorktree | writes git-native lock file — the ONLY ownership artifact anywhere | creates it; nothing self-verifies against it | — |
| Naming table (`rules/workflow.md`) | generic names (`t{N}`), no uniqueness | — | root cause of collisions |
| Fork-boundary anchor (`rules/git.md`) | rev-parse check only after forks; codifies weak predicate for linear flow | no — I1 is mid-session | partial |
| `guard-cd-primary-repo.sh` | explicit `cd <primary> && mutate` only | no — I1 has no cd | no |
| `pretooluse-worktree-path-guard.sh` | file-writes to primary, advisory | partial | no |
| `guard-commit-on-main.sh` | branch == main | **false-negative: I1's `checkout -B` moves the branch off main, guard then allows the commit on the primary** | no |
| `worktree-gc.sh`, remove/exit guards | loss-prevention, ownership-agnostic | — | — |
| `beat.py` cleanup, `molt` step 0 | the only two readers of the lock file — both protect OTHERS from this session, never self-verify | dead-PID only | no |
| `hunt` step 3, `raid` Phase 7, `gaze` postcondition | the right rev-parse check, but one-shot at checkpoints, model-executed | partial | partial |
| `erg-pr-merge` `in_worktree()` | `[ -f .git ]` — the weak predicate verbatim | no | no |
| gaze review worktrees | live under `/tmp/`, outside every guard's `.claude/worktrees/` fast-path | uncovered | uncovered |

Root gap: the lock file EnterWorktree writes is read in exactly two places,
both self-protective; no per-command check re-derives "does rev-parse match
my registered identity" on the hot path.

## Proposed ownership model

- **A — live identity preflight (ship first).** New PreToolUse guard on
  mutating git/erg commands: fast-path when cwd contains
  `/.claude/worktrees/`, then compare the cwd worktree-name segment against
  `basename $(git rev-parse --show-toplevel)`; block on mismatch or on
  resolving to the primary root. One rev-parse (~5–20 ms). Closes I1; also
  fixes the guard-commit-on-main false-negative by checking tree identity
  instead of branch name.
- **B — session→worktree claim binding (author design call).** Claim marker
  written at EnterWorktree success, verified by the guard. Closes I2.
  Depends on where EnterWorktree can be hooked (CLI built-in vs repo
  script) — needs the author before scoping.
- **C — collision-resistant naming (cheap complement).** Suffix worktree
  names with a session discriminator (`t{N}-{shortpid}`) in the naming table
  and hunt/raid; update `beat.py`'s `_HARNESS_WORKTREE_RE` if needed.

## Candidate fix tickets (menu for the author, not filed)

1. Live worktree-identity guard for mutating git/erg commands (closes I1).
2. Fix `guard-commit-on-main.sh` false-negative; consume `.cwd` from hook
   JSON like sibling guards.
3. Collision-resistant worktree naming.
4. Design ticket: EnterWorktree claim-file binding (closes I2).
5. Cover gaze's `/tmp/review-<pr>` worktrees (move under `.claude/worktrees/`
   or broaden guard fast-paths).
6. Tighten or justify `erg-pr-merge`'s `in_worktree()` weak predicate.
