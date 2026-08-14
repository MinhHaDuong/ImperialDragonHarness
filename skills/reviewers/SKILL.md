---
name: reviewers
description: Reviewer-panel management for /gaze — list, request, harvest, scorecard, scores, audition, and help reviewer seats.
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
exits 0. Fail-open is not fail-silent: every seat that did not review is
recorded in a `<seat>.status` sidecar and named by `harvest` in the report
(see **Panel integrity** below). No secrets in config.

**Seat credentials** (ticket 0393). A seat's `credential-env: NAME` is read
from the environment when the BASH_ENV path (0207) exported it — which happens
only where the cwd's `.env` `KEYS=` line selects that provider, a **default-deny**
selection. From a project selecting a different key, or any cwd declaring none,
`NAME` is simply absent. `request` then resolves it from the keystore
(`~/.config/keys/*.env`, override `REVIEWERS_KEYSTORE`): the single file
defining `NAME` is sourced under `set -a` in an `env -i` subshell, only that one
variable is extracted, and it is exported solely inside the subshell that execs
the seat-runner. The author's key files are never edited — they hold bare
assignments with no `export`, and enabling allexport at source time is what
makes such an assignment reach a child process. A value never touches argv, a
log line, or a sidecar; warnings name variables and provider files only. A seat
whose credential resolves nowhere is skipped, WARNed, and reported by `harvest`
— it is not quietly dropped from the panel.

**Per-seat latency** (ticket 0353): each `cli-agent`/`local-model` seat is timed
and its wall-clock seconds written to a `<seat>.latency` sidecar beside the
findings, whatever the outcome (a slow-then-failed seat is still evidence).
`scorecard` folds that figure into the seat's trial line. `forge-bot` seats run
async server-side and get **no** sidecar — there is nothing local to time.

### `/reviewers harvest <pr>`

Collect every seat's findings and normalize the seat-runner's
`FINDING|severity=…|file=…|rationale=…` output to the 0205 contract shape:

```
verifiable: <file>:<line> — <rationale>  [seat]
consider: <file>:<line> — <rationale>  [seat]
```

A line that does not parse is surfaced as a `WARN` on stderr, never
silently dropped.

**Panel integrity** (ticket 0393). Findings are only half the report. `harvest`
also cross-checks the roster against the run records `request` left, and names
every seat that did not review — on **stdout**, the report stream:

```
SEAT-FAILED: openrouter-frontier — credential OPENROUTER_API_KEY_IDH unresolved  [this seat did NOT review]
SEAT-MISSING: local-qwen — no findings and no run record  [this seat did NOT review]
PANEL-INTEGRITY: 2 seat(s) did not review this merge request — the findings above are NOT a full panel
```

`SEAT-FAILED` comes from the seat's `.status` record; `SEAT-MISSING` is a
roster seat that left neither findings nor a record (`request` never reached
it). A seat that ran and found nothing is not flagged — that silence is a
result. `forge-bot` seats write no local findings by design, so only their
recorded failures surface. Exit stays 0: these are visible lines, not a block,
so one dead seat still never stops a verdict.

This exists because the failure it reports is the one that hid. During a live
`/gaze` the OpenRouter seat failed **open** on a missing credential: the WARN
went to stderr, `harvest` printed nothing, exited 0, and the panel read as
complete. An empty harvest that cannot distinguish "clean" from "nothing ran"
is not a check — the same shape as the `gh pr list --json files` trap in
`tickets/AGENTS.md`.

### `/reviewers scorecard <pr> <seat> <verdict-summary>`

Append a fixed-schema trial line to the seat's trial ticket via `erg log`
(verbs: `created`, `note`, `closed` only), so 0205's integration review is
evidence-based:

```
MR #42 seat=local-qwen verdict: PASS — 0 verifiable, 2 consider latency=48.7s
```

When `request` left a `.latency` sidecar for the seat (a `cli-agent`/
`local-model` seat — see below), its wall-clock seconds fold into the line as a
trailing `latency=<s>s` field (ticket 0353). Absent a sidecar the line is
byte-identical to the pre-latency schema — the field is appended at the end, so
every existing parser is unaffected.

### `/reviewers scores [seat-or-candidate]`

Read back the trial cards (`scorecard` lines and `audition` blocks) that the
two commands above append to trial tickets, as one sortable comparison table.
The read surface for 0205's integration review ("trial scorecards reviewed;
promote/drop decided"): comparing candidates no longer means opening ticket
files and eyeballing log lines.

The search is **corpus-wide** and **read-only**: it greps every trial ticket's
log section under `tickets/`, recursing into `tickets/closed/`, so a retired
seat's archived cards are still read. It never edits a roster or writes an
`erg log` line. (This corpus-wide reach is `scores`-only: `scorecard` *writes*
via `erg log <ID>`, which resolves IDs among *open* tickets only — logging a new
card to an archived trial ticket fails "no ticket found". `scores` reads by
grep, so it is not bound by that.)

```
KIND      NAME                 MR/BOARD                   VERIF  CONS  FIND  DUP  UVER  UHAL  OVERLAP   LATENCY      P95     COST  FLAG
audition  hy3-free             10MR                           -     -    59   23     0    36      38%      9.4s    41.0s      n/a  SLOW
scorecard copilot              ImperialDragonHarness#537      0     0     -    -     -     -        -     48.7s        -        -     -
```

No argument → all seats and candidates. An argument filters to one seat or
candidate name. A malformed trial line WARNs on stderr, never silently dropped
(the harvest convention). Only each ticket's `--- log ---` section is read, so
a card quoted in a ticket body as documentation is never mistaken for a result.
`scorecard`'s per-MR columns (`VERIF`/`CONS`) and `audition`'s per-board columns
(`FIND`/`DUP`/`UVER`/`UHAL`/`OVERLAP`) share one table; a `-` marks a column that
does not apply to that row. `LATENCY` shows a candidate's `latency-p50` (the
gate-relevant stat, falling back to the running-sum `latency=` for older cards)
and a seat's per-MR latency; `P95` is the candidate's tail latency; `FLAG`
surfaces the peer-relative `SLOW` verdict (ticket 0353).

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
  overlap=<pct>% latency=<s>s cost=<$x|n/a> \
  latency-p50=<s>s latency-p95=<s>s [SLOW]
```

`overlap%` is the share of the candidate's findings that merely duplicate the
panel. `cost` is `$ per review` from the token counts the seat reports on its
`SUMMARY` line, priced via `REVIEWERS_PRICE_IN_PER_M` / `REVIEWERS_PRICE_OUT_PER_M`
(USD per 1M tokens); it is `n/a` when the seat reports no tokens or no price is
configured — an honest blank, never a fabricated `$0`.

`latency=` is a running **sum** of wall-clock across the board PRs.
`latency-p50` / `latency-p95` are the per-PR latency distribution (nearest-rank,
appended after `cost=` so existing parsers are unaffected; ticket 0353).

**Peer-relative SLOW gate** (ticket 0353): a candidate whose `latency-p50`
exceeds `REVIEWERS_SLOW_FACTOR` × the cross-candidate median p50 (default factor
**3**) earns a bare trailing ` SLOW` token, and its verdict becomes
**eliminate-slow** — it does not proceed to the live advisory trial. The
comparison is against **other candidates that replayed the same board size**:
identical work, so the statistic is host- and diff-size-independent. It fires
only with **≥1 peer** (a lone candidate has no basis for comparison) and is a
**strict** `>`, so a candidate at exactly `factor × median` is kept. The gate
only reads peers' logged cards and appends to the new candidate's own card — it
**never edits a prior candidate's line** (append-only) and never touches the
roster; roster promotion stays the manual call at 0205's integration review.

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
scorecard; default the model id — an **identifier**, so no spaces, `=`, or
newlines: those are the space-delimited card's field delimiters and would
corrupt read-back).

Environment: `REVIEWERS_SLOW_FACTOR` (default `3`) sets the SLOW threshold as a
multiple of the cross-candidate median p50.

## Candidate scouting

Where candidate models come from — the mechanics of finding something to
`audition`, so a fresh session need not reinvent them. Model **choice** stays a
judgment call; this section documents only how to enumerate the options.

**Endpoint inventory.** The authenticated providers are the `*.env` files in
`~/.config/keys/` — one file per provider (e.g. `openrouter.env`), each holding
that endpoint's API key. Keys load via the BASH_ENV path (0207) where the cwd's
`KEYS=` selection covers the provider, and are resolved from the keystore
otherwise (see **Seat credentials** above); never inline a key into config or
argv. The commented seat examples in `panel.yml` show the
two endpoint shapes: a local llama-server (`http://127.0.0.1:8012/v1`, no
credential) and OpenRouter (`https://openrouter.ai/api/v1`, key via
`credential-env`). Probe a local `llama-server` by hitting its base URL.

**Models per endpoint.** `GET <base>/v1/models` lists what an endpoint serves.
OpenRouter's catalog is public (`https://openrouter.ai/api/v1/models`) and
carries per-token pricing, which is what feeds `REVIEWERS_PRICE_IN_PER_M` /
`REVIEWERS_PRICE_OUT_PER_M` for the audition `cost` column.

**Rankings.** OpenRouter's usage rankings are website-only
(`https://openrouter.ai/rankings`, fetched as a page, not exposed as an API) —
a coarse popularity signal, not a review-quality signal.

**Privacy asymmetry.** Auditioning on a free tier is risk-free: the benchmark
board replays *already-merged* PRs of a public repo, so nothing unpublished
leaves the machine. A live advisory trial is different — it ships the *unmerged*
diff of a real merge request to the endpoint. Weigh a free/third-party endpoint
accordingly before promoting a candidate from audition to a live seat.

## Configuration

`skills/reviewers/panel.yml` is the single roster file (schema in its
header). No secrets in config — a seat names its credential *variable*, and
the value is resolved at run time (see **Seat credentials** above).

Environment: `REVIEWERS_KEYSTORE` overrides the credential keystore directory
(default `~/.config/keys`); `REVIEWERS_PANEL`, `REVIEWERS_FINDINGS_DIR`,
`REVIEWERS_REPO`, `SEAT_RUNNER`, and `ERG` override the roster, the findings
directory, the repo under review, the seat mechanism, and the ticket binary.

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
