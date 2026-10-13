# PR 1374 review round 1

Forge review: PRR_kwDORsAV3c8AAAABR1coPA
Reviewed commit: e2c79395c8861cc7d8ab4604009b704d3698e670
Submitted: 2026-10-12T14:01:59Z

## /review-pr round 1 — PR #1374 (anchor e2c79395)

Panel: proportional, 4 of 5 seats (Scope omitted). Width: 6 files, over the small-diff maxima, `skills/**` matches a pipeline path. All seats are same-family (Anthropic: opus correctness and red team, sonnet consistency and doc propagation); none is independent. Gate: `make check` 1558 passed, 4 skipped (full gate; no `.idh-checks.json` scoping).

### Blocker
1. **Step 10 snippet is broken in the real flow** (consistency, doc propagation; confirmed by me). `skills/roar/SKILL.md:316` calls `"$ROAR_DIR/close-and-clean.sh"`, but `ROAR_DIR` is defined only at :216 (step 7). Each Bash call is a fresh shell and ExitWorktree intervenes, so it runs `/close-and-clean.sh`. Repeat the two-line `ROAR_SKILL_MD`/`ROAR_DIR` preamble in step 10 (and 9a if it calls the script).

### Should fix
2. **Fresh branches at the base tip are swept, local and remote** (red team F1, correctness F2). A branch with no commits yet is an ancestor of origin/main and gets deleted, including a colleague's just-pushed branch. Repro: red-team report (`git branch colleague-new; git push origin colleague-new` then the sweep). The inherited recipe had the hole, but the script now runs it unattended. Skip refs whose tip equals the base tip.
3. **`%(refname:short)` ambiguity bypasses the worktree and default guards** (red team F2, reproduced). Ambiguous names print as `heads/x` / `remotes/origin/x`; only a failing `-D` saves it. Use `%(refname:lstrip=2)` and `lstrip=3`.
4. **The "no forge exits 2" test never reaches the forge** (correctness F1). The world has no `tickets/erg`, so `check_claims` returns early at close-and-clean.sh:86-88. Use `ticket_world` with `run_nogh` and assert the `CLAIMS: COULD-NOT-LOOK (exit` line.

### Minor
- verifiable: `bash close-and-clean.sh --ticket; echo $?` prints 1 (unbound `$2`); the contract says 2 (red team F4, :29-32).
- verifiable: `git update-ref refs/heads/-x HEAD` makes `merge-base --is-ancestor` fail with a usage error, and the run reports `RESULT: clean`, rc 0. Branch kept, so safe, but a could-not-look reads as clean (red team F3, :173,190). Use rc>1 -> 2 and `refs/heads/$b`.
- consider: tests write `skills/roar/.mutant-*-$$.sh` into the tracked tree; a kill -9 leaves them (commit f0763790 shows one leaked). Copy into `$T` or ignore (correctness F3, consistency 5).
- consider: tickets/1089 (pi-subagent-link) is unrelated to roar, though the 1084 log says "follow-up filed as 1089". Move it to its own PR or fix the log; also align the `Minh Ha-Duong` / `Minh-Ha-Duong` author spelling (consistency 2, 3, doc propagation 2).
- consider: `git fetch --prune` without `origin` lets an unrelated stale remote block the sweep with exit 2 (red team F5).
- consider: `scripts/worktree-exit-preflight.sh:11` header still says "from /roar step 9" (doc propagation 4).
- consider: the PR body must keep a non-closing reference to 1084; its last exit criterion is open.
- nofollow: cwd-relative `tickets/` (fails closed with 2); unbounded Parent match at :109 (4-digit ids); `--default-branch` undocumented.

### Verdict roster
- correctness: comment
- consistency: comment
- red team: comment
- doc propagation: comment
- scope: not run (proportional panel)

Synthesis verdict: request-changes on item 1 alone; items 2-4 recommended in the same round. dissent: none among the four reported seats; every seat is same-family, so no cross-family check was done.
