# PR1373 review evidence and detached-seat runtime identity

Project: ImperialDragonHarness. Public audience: this entry contains published PR/code information, review outcomes and sanitized runtime identity facts, with no credentials, no private infrastructure detail and no personal data.

PR #1373 implemented ticket 1085 (molt: script the ticket close/archive blocks, fix the merged-branch probe, fix the fixed /tmp reconcile path). It merged at 2026-10-12T15:25:30Z as integration commit 1e8ccb3874f2f7bd0c12be05ae3d35f1cc656b53.

## Writer identity (concealed by the runtime)

The writer was a detached headless Claude Code seat launched by the orchestrator as `claude -p --model sonnet --dangerously-skip-permissions` in the worktree `.claude/worktrees/t1085-776266` (branch `t1085-molt-ticket-sweep`). The CLI's plain-text output mode reports no provider-pinned model identifier and no model revision; `sonnet` is a moving provider alias, and no canonical id, `modelUsage` block or provider revision was exposed to the orchestrator. The requested alias is recorded here as the only observed identity fact; no identity was inferred from it. Writer effort was not pinned by the launch command and was not reported by the runtime.

Implementation tip after the first pass: d2409c7d60a2af3bb2db0860fb4b19d23a956a07. `make check` in that worktree: 1578 passed, 4 skipped.

## Reviewer attempts

Round 1 — detached Pi seat, launched as `pi --no-session -n gaze-1085 --model openrouter/~openai/gpt-sol-latest --thinking high -p`, ruled tip d2409c7d60a2af3bb2db0860fb4b19d23a956a07. Pi reported only the configured route alias; the seat's own PANEL-INTEGRITY line states "Exact resolved models/efforts unverified", so no provider-pinned id or revision was established for this seat or its reviewer children. The seat ran its panel as separate children: adherence (`openrouter/~anthropic/claude-sonnet-latest`, Anthropic family), correctness, consistency, scope, red-team and doc-propagation (`openrouter/~openai/gpt-sol-latest`, OpenAI family), plus semantic-adherence, portable-simplify and gate children. The mandatory native built-in `/review` perspective was NOT-RUN and reported as unavailable in the detached Pi seat, not simulated. Substantive verdict REROLL; terminal verdict ESCALATE on the unresolved-phase breaker and the missing native perspective. Durable trail: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1373#issuecomment-6126632952

Round 2 (after the bounce) — detached Pi seat, launched as `pi --no-session -n regaze-1085 --model openrouter/~openai/gpt-sol-latest --thinking high -p`, ruled tip 6a184167403ab8eee6c3bc25742ddd2e9a87d931. Same route-alias situation: the seat attests the installed route `openrouter/~openai/gpt-sol-latest` (OpenAI family, different family from the Anthropic producer) but records "exact alias resolution/effort was unattested" for its seats. Five reviewer subagents completed correctness, consistency, red-team, doc-propagation and a cleared-scope regression; all approved. Adherence and portable-simplify seats observed `openrouter/~anthropic/claude-sonnet-latest` at high effort. A separate gate worker verified the current git and forge HEAD and returned substantive APPROVED. Native `/review` remained NOT-RUN. Substantive verdict APPROVED; terminal verdict ESCALATE on the missing native perspective alone. Durable trail: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1373#issuecomment-6127085043

The implementer seat and the reviewing battery are from different model families (Anthropic producer, OpenAI reviewers). The adherence and gate seats inside the Pi battery ran the Anthropic route and are therefore not independent of the producer; that is recorded rather than smoothed over.

## Findings and adoption (round 1, all adopted in the bounce at 6a184167)

- `skills/molt/ticket-sweep.sh:82` — the merged-probe subject signal scanned all `main` subjects instead of divergence-scoped history, falsely certifying newer unmerged work as merged; reproduced with merged=0 against ancestry=1 plus a historical PR match. Adopted.
- `skills/molt/SKILL.md:140` — the newly added `echo` masked a reconciliation failure: a forced Python exit 7 still returned 0 and announced a report. Adopted.
- `skills/zotero/references/backfill.md:27` — the new anonymous `mktemp` substitution neither retained nor announced the report pathname. Adopted.
- `tests/test_molt_ticket_sweep.py:24` — the replacement suite carried `env=None`, letting default children inherit `BASH_ENV`; interception of the real helper confirmed it. Adopted (children use `child_env()`).
- `skills/molt/ticket-sweep.sh:40` — the extracted archive suppressed `erg` failure and diagnostics and continued pruning, so the sweep exited 0 on a failed archive; healthcheck inherited this. Adopted.

Round 2 verified each fix with an injection and a mutant control and reported no new findings. Ticket exit criteria were checked against the diff; none was accepted as met on assertion alone.

## Local validation

`make check` in the implementation worktree: 1578 passed, 4 skipped. The bounce ran the focused suite for each fix. The merged branch was deleted locally and remotely after an ancestry probe proved it contained in `origin/main`; the forge deletes merged branches itself.
