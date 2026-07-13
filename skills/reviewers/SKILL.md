---
name: reviewers
description: Reviewer-panel management for /gaze — list, request, harvest, and scorecard reviewer seats.
disable-model-invocation: false
user-invocable: true
argument-hint: "<subcommand> [args]"
---

Manage the external reviewer panel for `/gaze`. Each seat is a sandboxed
CI-style reviewer job (ticket 0205, "review is CI"): `request` runs the
0217 seat-runner once per roster seat — one OS-sandboxed container per
seat — and `harvest` normalizes every seat's findings to the gate's
contract shape. Containment comes from the seat-runner's sandbox, not from
this skill. All I/O routes through `skills/reviewers/reviewers.sh`.

## Subcommands

### `/reviewers list`

Show panel members, their kind (forge-bot / cli-agent / local-model),
advisory/required status, and trial ticket. Empty roster → prints
`no reviewers configured`, exits 0.

### `/reviewers request <pr> [branch]`

For each roster seat, run the 0217 seat-runner over the merge request's
diff (the branch is resolved from the PR, or passed explicitly):

- **cli-agent / local-model**: the seat-runner launches the agnostic CLI
  reviewer inside an OS sandbox over an OpenAI-compatible endpoint
  (OpenRouter or local llama-server), writing per-seat findings.
- **forge-bot**: requested via the forge's reviewer-request API, using the
  seat's `login` from the roster (on GitHub: <!-- harness-extension-point -->
  `gh api --method POST repos/{owner}/{repo}/pulls/<pr>/requested_reviewers
  -f 'reviewers[]=<login>'`).
  **On-demand only** (ticket 0206): the seat fires when this subcommand is
  invoked on a specific merge request — no repo-wide auto-request, so
  trivial PRs stay unreviewed. Its findings surface as review comments on
  the merge request itself (not as `harvest` findings files); the gate
  dispositions them like any panel comment.

**Per-seat fail-open**: a seat that errors or hangs WARNs and the others
proceed — one seat never blocks the verdict (0205). Empty roster → no-op,
exits 0. No secrets in config; seat credentials load via the BASH_ENV path.

### `/reviewers harvest <pr>`

Collect every seat's findings and normalize the seat-runner's
`FINDING|severity=…|file=…|rationale=…` output to the 0205 contract shape:

```
verifiable: <file>:<line> — <rationale>  [seat]
consider: <file>:<line> — <rationale>  [seat]
```

A line that does not parse is surfaced as a `WARN` on stderr, never
silently dropped. No findings (empty panel / no seats ran) → empty output,
exit 0.

### `/reviewers scorecard <pr> <seat> <verdict-summary>`

Append a fixed-schema trial line to the seat's trial ticket via `erg log`
(verbs: `created`, `note`, `closed` only), so 0205's integration review is
evidence-based:

```
MR #42 seat=local-qwen verdict: PASS — 0 verifiable, 2 consider
```

## Configuration

`skills/reviewers/panel.yml` is the single roster file (schema in its
header). No secrets in config — credentials load via BASH_ENV (0207).

## Dependencies

- `~/.claude/scripts/seat-runner.sh` (ticket 0217) — the
  sandboxed seat execution mechanism `request` invokes. Override with
  `SEAT_RUNNER` for testing.
- `tickets/erg` — `scorecard` appends the trial log line.
