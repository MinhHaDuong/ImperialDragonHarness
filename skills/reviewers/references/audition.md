# `/reviewers audition <model> [--endpoint URL]`

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
otherwise (see **Seat credentials** in `references/request.md`); never inline
a key into config or
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
