# PR1372 review evidence and detached-seat runtime identity

Project: ImperialDragonHarness. Public audience: this entry contains published PR/code information, review outcomes and sanitized runtime identity facts, with no credentials, no private infrastructure detail and no personal data.

PR #1372 implemented ticket 1086 (raid: move the reroll-count awk parser into a tested script). It merged at 2026-10-12T15:24:41Z as integration commit 5a82a6145e3b0ae76a93696392b910723fb2a2c5.

## Writer identity (concealed by the runtime)

The writer was a detached headless Claude Code seat launched by the orchestrator as `claude -p --model haiku --dangerously-skip-permissions` in the worktree `.claude/worktrees/t1086-776433` (branch `t1086-reroll-tally-script`). The CLI's plain-text output mode reports no provider-pinned model identifier and no model revision; `haiku` is a moving provider alias, and no canonical id, `modelUsage` block or provider revision was exposed to the orchestrator. The requested alias is recorded as the only observed identity fact; no identity was inferred from it. Writer effort was not pinned by the launch command and was not reported by the runtime.

Implementation tip after the first pass: f39edf4021fb6fba861a30d3b32cea0c29a36943.

## Reviewer attempts

Round 1 — detached Pi seat, launched as `pi --no-session -n gaze-1086 --model openrouter/~openai/gpt-sol-latest --thinking high -p`, ruled tip f39edf4021fb6fba861a30d3b32cea0c29a36943. The seat's PANEL-INTEGRITY line records its own limitation verbatim: "Backend aliases unresolved, effort pins unavailable, artifact protocol replaced by synchronous collection under read-only rails." Its panel: adherence and gate children on the configured Anthropic route (`openrouter/~anthropic/claude-sonnet-latest`, high), consistency, scope, red-team and correctness-regression children on the configured OpenAI route (`openrouter/~openai/gpt-sol-latest`), doc-propagation and portable-simplify children on the configured OpenAI Luna route (a first doc-propagation attempt abstained and was retried). The mandatory native built-in `/review` perspective was honestly NOT-RUN, not simulated. Substantive verdict REROLL; terminal verdict ESCALATE. Durable trail: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1372#issuecomment-6126588222

Round 2 (after the bounce to e3039d4d33544aaffec0db351cfa9cedec75d205) — detached Pi seat, launched as `pi --no-session -n regaze-1086 --model openrouter/~openai/gpt-sol-latest --thinking high -p`, ruled tip e3039d4d33544aaffec0db351cfa9cedec75d205. Same alias-resolution limitation: no provider-pinned id or revision was attested for the seat or its children. It verified that exactly five added regression cases fail on the pre-fix tip and pass at the ruled tip, and that the permission tests execute as euid 1001 rather than being root-skipped. Substantive verdict ESCALATE: one surviving blocking finding plus the third-gate-attempt breaker and the NOT-RUN native perspective. Durable trail: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1372#issuecomment-6127079741

The implementer seat was Anthropic-family and the reviewing battery was OpenAI-family, so the substantive review was cross-family. The adherence and gate children inside the battery ran the Anthropic route and are not independent of the producer; recorded as such.

## Findings and adoption (round 1, adopted in the bounce at e3039d4d)

- `scripts/raid-reroll-tally.py:72` — glob enumeration silently omitted unreadable directories: an unreadable-only scan returned exit 0 with empty stdout and empty stderr, and a partial scan returned only the readable row with no warning. Adopted.
- `scripts/raid-reroll-tally.py:37` — an unhandled read failure returned exit 1 instead of the documented could-not-look exit 2 (reproduced with a mode-000 ticket file raising PermissionError). Adopted.
- `scripts/raid-reroll-tally.py:44` — changing only the known-positive fixture's bump verb or log marker produced exit 0 with empty stdout and stderr; the timestamp-only warning did not satisfy the drift criterion. Adopted.

## Surviving finding and the orchestrator insertion

Round 2 reported one surviving blocker at `scripts/raid-reroll-tally.py:97`: a mode-0444 directory lists its `.erg` names but `stat` raises PermissionError, so `Path.is_file()` returned False and the ticket was omitted silently with exit 0 — a surviving variant of the round-1 directory blocker, not an introduced regression.

The ticket's retry budget was already spent, so the fix was applied by the orchestrator on the caller's explicit instruction rather than by a third executor round, and the attribution is stated in the PR body. Insertion commit 69201fd6b8e2c91ae7ccb84b5417f98d7ee6d4e6: candidate filtering now stats each path explicitly, reports `cannot stat <path>: <reason>` on stderr and sets the could-not-look flag. Injection before the fix: mode 0444 gave one row, exit 0 and a silently omitted ticket. After the fix: the same scan prints the error and exits 2 while keeping the readable row. The current corpus was re-measured unchanged: 600 ticket files, 67 rows, byte-identical to the awk oracle, empty stderr. `make check` after the insertion: 1582 passed, 4 skipped.

## Local validation

The differential oracle ran the pre-change awk and the new script over the whole ticket store and compared rows byte for byte. The merged branch was deleted locally and remotely after an ancestry probe proved it contained in `origin/main`; the forge deletes merged branches itself.
