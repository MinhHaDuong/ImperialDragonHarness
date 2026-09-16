---
name: project-ci-chore-bypass-workflow
description: DONE (PR #458, 2026-05-23) — CI.yml skips lint/tests on ticket/STATE-only diffs via dorny/paths-filter, fail-safe so any code/mixed/errored diff runs full.
metadata: 
  node_type: memory
  type: project
  originSessionId: aacff427-fd62-410d-9b06-5e233b752256
---

**Implemented in PR #458 (2026-05-23).** `.github/workflows/CI.yml` has a `changes` job using `dorny/paths-filter@v3` with `predicate-quantifier: 'every'` and **positive-only** globs (`tickets/**`, `STATE.md`). The `chore` output is true only when *every* changed file is a chore. `lint`/`tests` still run as jobs (so the required-check names always report), but each step is gated on `chore != 'true'` and skips in seconds on chore-only diffs. The `changes` job itself runs in ~5s.

**Fail-safe by construction:** positive globs (no untested negation/brace) + the `!= 'true'` gate mean a mixed diff, a code change, or an empty/errored filter output all run the full suite. The bypass fires only on a definitive chore-only signal. Job-level `if: ${{ !cancelled() }}` keeps lint/tests from being blocked if the `changes` job ever fails.

**Why:** Morning of 2026-05-23 — branch protection was hardened on `main` (strict + enforce_admins) after Copilot auto-merged 3 red PRs (#433/#434/#435). The protection works, but made ticket-close/STATE commits as heavy as a code PR. The naive `paths-ignore:` at the trigger level is a trap — it leaves required checks "Expected, waiting" forever and blocks the PR. The early-exit-job pattern is the documented workaround.

**Scope deliberately narrow:** only `tickets/**` and `STATE.md`. Do NOT add `.claude/**`, root `*.md` (`AGENTS.md`/`CLAUDE.md`/`README.md`), or `docs/**` — agent-instruction surface and handoff docs are real regression surface (see #434's deletion of `.claude/rules/tickets.md`). Expand only if a category proves restrictive.

Related: [[project-agent-identity-separation]] is the complementary identity-side fix. [[feedback-gh-pr-merge-delete-branch-worktree]] is the merge-ergonomics lesson from the same session.
