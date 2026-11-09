# Third-party review: the Codex dirty-reset hook wiring (2026-09-28)

Two independent seats reviewed the Codex hook wiring built in ticket 0809
(PR #1042): the roster's frontier seat (openai/gpt-5.6-luna via OpenRouter)
and its budget seat (deepseek — see the roster note). The seats ran as
direct dossier reviews rather than sandboxed seat-runner jobs: the PR is
merged, so there is no branch diff to run over, and the seat-runner is
built for in-flight branches. The deviation is recorded here, not hidden.

## Round 1 — without the live evidence

- **gpt-5.6-luna: APPROVE-WITH-FINDINGS** (8 findings).
- **deepseek: REJECT** (6+ findings, truncated by its reasoning budget).

The dossier bug that shaped round 1: the Limits section of the runbook was
extracted empty (slicing on the wrong heading order), so both reviewers
believed the Codex limits were undocumented. That was my curation error,
not the runbook's state, and it is admitted here because it drove a REJECT.

## Round 2 — with the live evidence and the real limits

The addendum supplied: the official Codex hooks documentation (shell
commands "match as `Bash`"; `tool_input.command`; "exit code `2` and ...
stderr" denies), the 2026-09-28 block transcript (the hook fired on the
dirty fixture, the guard parsed the real payload, exit 2 denied the
command, the fixture survived), and a fresh measurement of the timeout
semantics.

- **gpt-5.6-luna: APPROVE-WITH-FINDINGS**
- **deepseek-v4.1-flash: APPROVE-WITH-FINDINGS**

Convergence: both seats now confirm the core contract is correctly wired
and turn to boundary precision. The round-1 REJECT findings (wrong tool
name, assumed payload, wrong cwd) were refuted by documentation plus the
live transcript — the lesson recorded: an independent reviewer without the
measurements adversarially assumes their absence, and only the
measurements adjudicate.

## Findings and dispositions

| # | Finding (both seats) | Disposition |
|---|---|---|
| 1 | Codex hook trust authenticates the hook definition, NOT the script it invokes; a changed guard script does not untrust the hook | **Documented** in the runbook limits and the inventory assertion; the script's integrity stays the git checkout's business (git + CI) |
| 2 | Hook timeout is fail-open; 5s was above one 4s git check but below a multi-target worst case | **Fixed**: wiring timeout 5→8s (test band 5–10s), the measured fail-open semantics and the residual multi-target risk **documented**; an internal global deadline in the guard itself was **declined** this cycle (a canonical-guard design change; recorded as residual risk) |
| 3 | The static-test assertion read as proving the runtime contract | **Fixed**: the assertion now says wiring shape only and points at the manual-smoke assertion for the runtime proof |
| 4 | "Git-mutating" wording overclaimed the guard's scope | **Fixed**: inventory and hooks.json description narrowed to "the one wired dirty-reset guard" |
| 5 | Unquoted `$HOME` in the hook command | **Fixed**: `bash "$HOME/.claude/scripts/guard-destructive-bash.sh"` per the official example; re-verified live — the quoted form blocks identically |
| 6 | Guard header overclaims ("any cd DIR earlier", "leaves untracked files alone") | **Fixed**: narrowed to linear cd/git -C forms and detected-tracked-modifications as the protected condition |
| 7 | The persistent /hooks trust path was never exercised empirically | **Documented** as documentation-only evidence (the smokes used --dangerously-bypass-hook-trust); exercising it is the author's trust step |
| 8 | No smoke procedure to verify the guard fires | **Fixed**: preflight command added to the runbook (expect BLOCKED + exit 2) |

Observed and fixed in passing: the budget seat's roster model ID was stale
(`deepseek-v4-flash` retired upstream) — the seat was dead and silently
so; moved to `deepseek/deepseek-v4.1-flash` with a note about its
reasoning budget. The Claude-side wiring still carries the unquoted form;
its quoting is left to the drift reconciler (0886) rather than smuggled
into this cycle.

Verdict of record: the Codex hook wiring is approved with findings, the
findings are dispositioned above, and the two survive-as-documentation
items (trust scope, timeout fail-open) live in the runbook the operator
actually reads.

## Postscript, same day: the author's trust, exercised and measured

The author approved the hook. Codex's startup review dialog ("Trust all
and continue" — our guard was the one hook pending) was driven over a real
pty, the trust landed in `~/.codex/config.toml` under
`[hooks.state]` with a `trusted_hash`, and `codex exec` **without any
bypass flag** then blocked a dirty reset on the fixture.

Finding 7 of this review ("the persistent /hooks trust path was never
exercised empirically") is closed. And the exercise surfaced a sharper
version of finding 1: the first trust attempt recorded a hash that a
later session computed differently, the mismatching status (Modified) made
the hook **silently skipped in exec** — no warning, no block, the reset
would have run. The runbook now carries both facts: trust is
hash-recorded per definition, and a stale hash silently disables the
guard. Preflight before relying on it.
