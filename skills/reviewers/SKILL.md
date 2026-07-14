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

### `/reviewers audition <model> [--endpoint URL]`

Replay a **candidate** model over a frozen benchmark board of already-merged
merge requests and score its decorrelation value against ground truth (ticket
0346). This is the cheap filter that runs **before** the live advisory trial:
every candidate runs the **same** board in about an hour, so cross-candidate
comparison is sound — a live trial cannot give this, because each candidate
there sees different merge requests.

For each board PR, `audition` runs the 0217 seat-runner over that PR's
reconstructed diff (the same sandboxed, read-only invocation path `request`
uses), then classifies each finding against the board's recorded ground truth:

- **duplicate** — matches an internal-panel finding on that PR (redundant; no
  decorrelation value).
- **unique-verified** — not found by the panel, and confirmed real against a
  recorded panel-missed defect (the payoff).
- **unique-hallucinated** — not found by the panel and matching no known
  defect (the noise; e.g. the devstral-small-2 failure mode).

Findings match ground truth by **basename + line** (`file:LINE`, or `file:*`
for any line in a file) — the board stores anchors basename-normalized so it
stays forge/stack-agnostic.

One **scorecard block** is emitted per run and appended to the candidate's
trial ticket via `erg log` (verb `note`):

```
audition candidate=<label> model=<id> board=<N>PR findings=<F> \
  duplicate=<d> unique-verified=<uv> unique-hallucinated=<uh> \
  overlap=<pct>% latency=<s>s cost=<$x|n/a>
```

`overlap%` is the share of the candidate's findings that merely duplicate the
panel. `cost` is `$ per review` from the token counts the seat reports on its
`SUMMARY` line, priced via `AUDITION_PRICE_IN_PER_M` / `AUDITION_PRICE_OUT_PER_M`
(USD per 1M tokens); it is `n/a` when the seat reports no tokens or no price is
configured — an honest blank, never a fabricated `$0`.

**Fail-loud**: unlike `request`'s per-seat fail-open, audition aborts non-zero
if the seat-runner cannot replay a board PR (unreachable endpoint, sandbox
failure) — a partial score is more misleading than none.

**Audition never touches the roster.** It reads no `panel.yml`, writes no
`panel.yml`, and files no seat. The pipeline is:

```
audition (filter)  →  advisory trial (0205 rule 2: ≥5 MRs / ≥3 projects)  →  promote/drop
```

Promotion — adding a seat to `panel.yml` — stays a **manual** panel edit + merge
request at 0205's integration review. Audition informs that decision; it does
not make it.

Options: `--endpoint URL` (OpenAI-compatible base; default is the seat-runner's
local endpoint), `--board FILE` (default `benchmark-board.yml`), `--trial-ticket
tickets/NNNN-...` (where the scorecard is logged; default the 0207 trial ticket),
`--credential-env NAME` (for an authenticated endpoint; threaded to the
seat-runner, never written to config), `--name LABEL` (candidate label in the
scorecard; default the model id).

## Configuration

`skills/reviewers/panel.yml` is the single roster file (schema in its
header). No secrets in config — credentials load via BASH_ENV (0207).

`skills/reviewers/benchmark-board.yml` is the frozen audition board: ~10
already-merged multi-file code PRs of this repo, each with `base`/`head` commit
SHAs (immutable, so the diff is reconstructable forever) and ground-truth
`panel`/`defects` anchors recovered from the PR's gate verdict. It is a data
artifact — `audition` reads it, never edits it. Schema in its header.

## Dependencies

- `~/.claude/scripts/seat-runner.sh` (ticket 0217) — the
  sandboxed seat execution mechanism `request` invokes. Override with
  `SEAT_RUNNER` for testing.
- `tickets/erg` — `scorecard` appends the trial log line.
