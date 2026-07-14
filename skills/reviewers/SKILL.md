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

### `/reviewers scores [seat-or-candidate]`

Read back the trial cards — `scorecard` lines and `audition` blocks — that the
two commands above append to trial tickets, as one sortable comparison table.
The read surface for 0205's integration review ("trial scorecards reviewed;
promote/drop decided"): comparing candidates no longer means opening ticket
files and eyeballing log lines.

The search is **corpus-wide** and **read-only**: it greps every trial ticket
under `tickets/` (recursing into `tickets/closed/`, so a retired seat's archived
ticket is still read), and never edits a roster or writes an `erg log` line. A
scorecard/audition card outlives its ticket's move to `closed/` because both
resolve the ticket by its 4-digit ID, not by the roster path.

```
KIND      NAME                 MR/BOARD                   VERIF  CONS  FIND  DUP  UVER  UHAL  OVERLAP   LATENCY     COST
audition  hy3-free             10MR                           -     -    59   23     0    36      38%   3419.1s      n/a
scorecard copilot              ImperialDragonHarness#537      0     0     -    -     -     -        -         -        -
```

No argument → all seats and candidates. An argument filters to one seat or
candidate name. A malformed trial line WARNs on stderr, never silently dropped
(the harvest convention). Only each ticket's `--- log ---` section is read, so
a card quoted in a ticket body as documentation is never mistaken for a result.
`scorecard`'s per-MR columns (`VERIF`/`CONS`) and
`audition`'s per-board columns (`FIND`/`DUP`/`UVER`/`UHAL`/`OVERLAP`/`LATENCY`/
`COST`) share one table; a `-` marks a column that does not apply to that row.

### `/reviewers help`

Print the usage block to stdout and exit 0. The no-argument and unknown-verb
paths keep printing usage to stderr and exiting 1.

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
audition candidate=<label> model=<id> board=<N>MR findings=<F> \
  duplicate=<d> unique-verified=<uv> unique-hallucinated=<uh> \
  overlap=<pct>% latency=<s>s cost=<$x|n/a>
```

`overlap%` is the share of the candidate's findings that merely duplicate the
panel. `cost` is `$ per review` from the token counts the seat reports on its
`SUMMARY` line, priced via `REVIEWERS_PRICE_IN_PER_M` / `REVIEWERS_PRICE_OUT_PER_M`
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

## Candidate scouting

Where candidate models come from — the mechanics of finding something to
`audition`, so a fresh session need not reinvent them. Model **choice** stays a
judgment call; this section documents only how to enumerate the options.

**Endpoint inventory.** The authenticated providers are the `*.env` files in
`~/.config/keys/` — one file per provider (e.g. `openrouter.env`), each holding
that endpoint's API key. Keys load via the BASH_ENV path (0207); never inline a
key into config or argv. The commented seat examples in `panel.yml` show the
two endpoint shapes: a local llama-server (`http://127.0.0.1:8012/v1`, no
credential) and OpenRouter (`https://openrouter.ai/api/v1`, key via
`credential-env`). Probe a local `llama-server` by hitting its base URL.

**Models per endpoint.** `GET <base>/v1/models` lists what an endpoint serves.
OpenRouter's catalog is public (`https://openrouter.ai/api/v1/models`) and
carries per-token pricing, which is what feeds `REVIEWERS_PRICE_IN_PER_M` /
`REVIEWERS_PRICE_OUT_PER_M` for the audition `cost` column.

**Rankings.** OpenRouter's usage rankings are website-only
(`https://openrouter.ai/rankings`) — fetched as a page, not exposed as an API —
a coarse popularity signal, not a review-quality signal.

**Privacy asymmetry.** Auditioning on a free tier is risk-free: the benchmark
board replays *already-merged* PRs of a public repo, so nothing unpublished
leaves the machine. A live advisory trial is different — it ships the *unmerged*
diff of a real merge request to the endpoint. Weigh a free/third-party endpoint
accordingly before promoting a candidate from audition to a live seat.

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
