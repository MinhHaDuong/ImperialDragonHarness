# Reviewer attribution — design spec

Date: 2026-10-02
Status: approved design (author, this session) — awaiting implementation
Tracker: tickets/1004 (this doc is its deliverable)
Supersedes: the seat-runner-centric panel contract of tickets/0205 (closed
2026-10-03); residual teardown and ticket dispositions in §10 belong to 1009.

## 1. Problem

The external-reviewer coaching system built under 0205 ("review is CI") runs
external models as sandboxed seats (0217) behind a roster (panel.yml), with
agent-authored scorecards in trial tickets. Four findings from a review of its
own trial record (2026-10-02) drive this redesign:

1. **Labels, not telemetry, are the scarce resource.** The audition board's
   `defects:` anchors are empty on all 10 entries, so the unique-verified
   (UVER) column is pinned at 0 by construction. Most trial diffs were clean
   and gate-cleared; a clean diff cannot produce a catch, so "0 findings"
   games carry no sensitivity information. Ten labeled defect-bearing games
   per seat rank seats at coarse resolution (Fisher p ≈ 0.03 for 5/10 vs
   0/10); a hundred unlabeled clean diffs rank nothing.
2. **Agent-authored telemetry drifts.** 21 of the 31 most recent scorecards
   use prose variants the `scores` parser rejects; the padme trial, the
   frontier seat's strongest catches (MR #813), and the budget seat's crash
   runs are invisible to the read surface. Harvest graded quota-blocked
   never-ran seats as `status=ok` — the same disease: telemetry written by
   participants instead of by the mechanism.
3. **The seat-runner is a strong assumption.** Runtime built-in harnesses
   (Claude Code, Codex, Pi, Vibe) have their own review machinery and
   containment. Requiring every external reviewer to run behind our sandbox
   runner is neither necessary for runtimes that own their containment nor
   portable across them (the 0980 audit exists because of this friction).
4. **Decorrelation is cited from literature, not measured.** The pairwise
   concordance data needed to select lineups or compute marginal coverage has
   never been captured.

## 2. Decision

Coach reviewers by **attribution**, not by seat execution:

- **Defer to runtime harnesses.** Each runtime reviews its own way, by
  default. The harness's contract with every runtime shrinks to a record
  format, not an execution mechanism.
- **Roar captures attribution facts** in the project's memory journal:
  who wrote, who reviewed (runtime, model, version), what they found, what
  was adopted, which defects were confirmed post-merge.
- **Coaching is ex-post and offline.** Labels accumulate as a free byproduct
  of normal merges; ranking, correlation and marginal coverage are derived at
  read time by querying the records. Nothing adaptive runs in the
  interactive review path.
- **Judgment stays with the author.** Roar records facts only (harness
  constitution: no lessons, no rules, no promotion in capture). Promote/drop
  remains a manual roster decision informed by the read surfaces.

### Non-goals

- No live seat execution requirement; no mandatory roster, provider or
  transport.
- No auto-promotion, auto-demotion, or per-game lineup selection (deferred
  until measured decorrelation justifies it — anchor: 0205 squad-management
  note, 2026-07-15).
- No change to the internal gaze panel or the verify-gate disposition rules.

## 3. Architecture

Three data planes, separated; two thin skills over one shared substrate.

```
FLIGHT DATA → attribution records      project repo memory/journal/
              (facts, append-only)      YYYY/YYYY-MM-DD-review-attribution-prNNNN.md
GROUND TRUTH → defect labels: adopted findings (pre-merge)
              + defect-confirmed event lines (post-merge, backfilled)
DECISIONS    → roster + promote/drop    author-owned, manual

SHARED SUBSTRATE  docs/spec (this file) + scripts: contract shape,
                   board format, classifier, enumerate-merges utility
reviewers skill   thin DESCRIPTOR: what external routes exist, the
                  contract, how to request live. Hot path, fail-open.
coaching skill    thin REPLAY: run a candidate over the frozen labeled
                  board, offline, ex-post. Cold path, fail-loud.
```

Why the split (decided 2026-10-02, after steelmanning both sides): the two
modes have different consumers (runtime mid-review vs a batch coaching
cycle), different postures (fail-open vs fail-loud), different churn rates
(routes change monthly; replay logic rarely) and different blast radii
(visible gate noise vs silent evidence corruption). The contract's single
source of truth is this spec, so co-location bought nothing. The harness
precedent is verify-gate being its own skill inside the gaze loop.

## 4. The attribution record

A dedicated journal-entry kind written by roar step 6 whenever the merged PR
was reviewed. Fixed grep-able lines carry the facts; prose is allowed only
for context. Findings carry repository-relative `path:line` anchors (the
frozen board's basename convention is narrower and stays board-only) so
the join across reviewers is mechanical and unique.

```
memory/journal/2026/2026-10-02-review-attribution-pr1102.md

kind: review-attribution
pr: 1102 · merged 2026-10-02 · project: .agents
writer: runtime=vibe · model=<full-model-id> · effort=standard
reviewer: seat=<name-or-role> · runtime=<id> · model=<full-model-id> · status: ran|failed|skipped
  finding: verifiable · <repo-relative-path>:<line> · adopted: yes|no
  finding: consider · <repo-relative-path>:<line> · adopted: yes|no
defect-confirmed: <repo-relative-path>:<line> · source: post-merge-fix · pr: <n>
```

Rules:

1. **Fixed lines for facts.** Named fields at fixed positions; the schema-drift
   lesson (§1.2) makes this non-negotiable. A read surface must never parse
   prose.
2. **Version pinning is load-bearing.** `model=` is the full, verbatim,
   provider-qualified model id as the provider pinned it at review time
   (provider aliases silently move upstream); `model-version=` is added
   whenever the provider exposes an explicit revision. A record without
   this is unusable for re-audition (deepseek-v4-flash incident).
3. **The writer is a stratification variable, not a pair member.** The
   writer emits no findings on its own diff, so writer-reviewer
   *concordance* is incomputable; the writer line enables per-writer
   stratification of reviewer performance instead.
4. **Anchored findings are the join key.** Anchors are repository-relative
   paths with line numbers — unique within a PR. (The frozen board keeps
   basename normalization for forge-agnosticism, with its collision caveat
   noted there; project records have no reason to accept it.) Same
   path:line across two reviewer lines = shared catch; exactly one =
   unique catch.
5. **Two defect-label sources, both confirmed.** A reviewer finding with
   `adopted: yes` is a confirmed pre-merge defect — the common case, since a
   caught defect is fixed before merge. A `defect-confirmed` event line is a
   post-merge miss, append-only, repeatable (zero lines when none yet). A
   game is defect-bearing if either source labels it.
6. **Attempt status is an observation, whatever the outcome.** `status:`
   is required on every reviewer line — a failed or skipped reviewer is a
   recorded fact (the harvest `status=ok` lesson), and the read surfaces'
   run-failure rates derive from it.
7. **Project-local.** Records live in the project's repository (or its
   explicitly configured private companion), per the harness memory boundary —
   never in the harness, never in a native memory directory, never in
   machine-local telemetry.
8. **Fail-loud capture.** A reviewed PR whose record cannot name its
   reviewers is a defect to report, not an omission to fill in from memory.

### Runtime-masked identities (1038)

When the active runtime conceals a writer or reviewer's verbatim provider id,
record the observed concealment explicitly. Replace `model=` with
`model-state=runtime-masked · model-evidence=<repo-relative-path>:<positive-line>`
on that identity. Runtime, writer effort, reviewer seat and attempt status
remain required. The evidence anchor points to durable project-local facts
establishing this runtime limitation for that attempt; it is not a model alias
or a guessed identity. `model=` and `model-version=` are forbidden alongside
this state. The parser validates the anchor syntax without opening evidence;
review verifies the evidence and its connection to the recorded attempts.
Free-text placeholders and other states remain invalid.

Such a record preserves review attempts, findings, adoption and later defect
labels, but re-audition by model remains impossible. Any masked writer or
reviewer excludes the **whole PR game** from model scores, run-failure rates,
correlation and marginal coverage; even named seats in that game are excluded.
Read-side counts distinguish syntactically `valid`, `runtime_masked` and
`model_attributable` games. Explicit range coverage labels these records
`runtime-masked`, distinct from available, missing and unavailable evidence,
and emits a warning. This state does not excuse other missing required facts
or authorize an identity inferred from an alias or third-party recollection.

### Valid capture example (synthetic fixture)

This is a parseable example, not evidence of an actual review. Never copy its
identities into a live record. Initial capture has no `defect-confirmed:` line;
post-merge events may subsequently be appended by the backfill hook. Repeated
anchors across attempts are intentional shared catches.

```text
kind: review-attribution
pr: 1164 · merged 2026-10-03 · project: .agents
writer: runtime=fixture · model=example/writer-v1 · effort=standard
reviewer: seat=correctness-round1 · runtime=fixture · model=example/reviewer-v1 · status: ran
  finding: verifiable · scripts/example.py:12 · adopted: yes
reviewer: seat=regression-round3 · runtime=fixture · model=example/reviewer-v1 · status: ran
  finding: verifiable · scripts/example.py:12 · adopted: no
reviewer: seat=external-round3 · runtime=fixture · model=example/external-v1 · status: failed
```

The reusable fixed-line reader is `scripts/attribution_record.py`. It validates
required facts, preserves separate reviewer attempts and exposes confirmed
defect anchors from adopted findings and later event lines. Context prose is
opaque. Its `--capture PROJECT --audience public|private` mode validates stdin
before calling the pinned project-memory helper; plain reading emits JSON.
The encrypted-in-repo policy supersedes §4.7's private-companion alternative:
uncleared attribution stays in the project as `.age`, never plaintext in a
companion or native store.

## 5. The coaching loop

1. **During review (unchanged, free):** the runtime reviews its own way;
   external routes optional via the descriptor skill.
2. **At wrap-up:** roar step 6 writes the attribution record.
3. **After merge, when a fix lands:** roar step 3's sweep ("review the fix
   just completed — grep for the same anti-pattern") gains one hook: a
   post-merge fix on lines a past review covered backfills
   a `defect-confirmed` event line in that PR's attribution record. This is
   a post-merge defect-label source; adopted findings also make a game
   defect-bearing. A third reviewer's adopted finding can also label a pair's
   "neither" cell. Without post-merge labels, estimates can skew optimistic.
4. **Offline, on demand (commissioned coaching cycle):** the replay skill
   runs any candidate over the frozen labeled board — same diffs for
   everyone, which the live record cannot give (selection bias: only
   reviewers who played have facts). Replay through the seat-runner is the
   containment wrapper for untrusted external CLI models only;
   runtime-native reviewers need no sandbox.

### Conservative backfill implementation

`scripts/attribution_backfill.py` uses the shared fixed-line reader. Its CLI
requires an explicitly commissioned defect-fix PR, full merged fix commit SHA,
project root and `--reviewed PR=SHA` coordinate evidence from the durable review
trail. The caller must establish that revision for all anchors across all
attempts in the record; ambiguous provenance stays unresolved. These inputs
are implementation evidence, not new record fields or context-parsing rules.

The supplied reviewed commit must belong to the project's fix-base ancestry.
By default the fix must belong to `HEAD` history. In Roar's existing wrap-up
branch below the actual merge, `--merged-through SHA` instead proves the fix
belongs to a supplied full integration tip that is itself ancestral to actual
`origin/main`. Roar resolves that tip from the project's `origin/main`; neither
a detached unintegrated fix nor an arbitrary supplied commit can substitute
for this integration proof. The helper never advances the wrap-up checkout.
Whole-file blob equality from that revision to the fix's first parent guards
line coordinates before joining literal anchors to old-side changed intervals.
Both unified and inter-hunk context are explicitly zero, so ambient Git
configuration cannot fuse changed intervals across unchanged anchored lines.
Pure insertions have no covered old lines. Renamed/missing files, drift,
unknown revisions, malformed/encrypted records and duplicate PR records warn
and remain untouched. No fuzzy recovery or implicit snapshot consolidation is
performed. A valid append preserves all original bytes, adds one event per
distinct covered anchor, and validates the candidate with `parse_record`.
Repeated invocations retain repeated factual events; successful records can
proceed while unresolved records remain visibly reported. Writes stay in the
explicit project repository; private records remain encrypted and unresolved.
A no-match leaves the record untouched. The helper reports counts and fails
visibly on a write error.

## 6. Read surfaces (derived, never stored)

A scores-style query over all attribution records of a project:

- **Scores:** per seat, labeled-game catch rate with credible intervals;
  noise rate; run-failure rate (from the `status:` field of rule §4.6).
  A catch is a confirmed defect label attributed to that seat — an adopted
  finding (pre-merge) or a defect-confirmed event matching its anchor.
- **Correlation:** reviewer-pairwise concordance table (both / unique-to-A /
  unique-to-B / neither), conditioned on defect-bearing games only
  (§1.1's base-rate discipline); Jaccard catch-overlap and
  shared-hallucination rate. The writer is a stratification variable
  (§4.3), not a pair member.
- **Marginal coverage:** unique-catch rate of seat B given seat A already
  plays — the squad-management quantity; raw catch rate overstates it.

### Read-side implementation (1007)

Run `python3 scripts/attribution_query.py [PROJECT]` for readable tables or
add `--json` for the same derivation. Only current-project journal attribution
filenames are read through the strict shared parser; malformed whole records
WARN with the filename and parser diagnostic. Identifiable filename/header PRs
are reserved before parsing: multiple record sources for a PR WARN and are all
excluded, including malformed or encrypted siblings. Encrypted records are
unavailable, never decrypted. Discovery recognizes the capture writer's actual
`.age` suffix as well as `.md` and legacy `.md.age`, reserving the filename PR
before any read. Symlink components, including internal record
links and a symlinked journal/year root, are unavailable and never read.
No data or coaching judgments are persisted.

A game is one PR. An identity is the exact seat/runtime/model/model-version
tuple (absent version stays unrecorded); writer runtime/model/version/effort
stratifies every score and pair. Repeated attempts union anchors for binary
game catches, while raw ran/failed/skipped counts remain separate. A catch trial
is a labeled game where that identity ran; a success has any globally confirmed
anchor, including labels supplied by another seat or a later event. Clean games
are excluded. Run failure is failed/(ran+failed), with skipped separate.

Noise is explicitly a **nonconfirmed emitted-finding share proxy**: later
confirmation applies to all attempts with that literal anchor; repeated emitted
findings count as emitted findings, never extra game trials. Unconfirmed does
not prove a hallucination. This proxy cannot by itself establish the fixed
§7 false-finding threshold; author judgment remains manual. Pair cells are
binary any-catch over labeled games
where both ran, with per-cell intervals. Anchor Jaccard sums same-game anchor
intersection/union counts; shared nonconfirmed-anchor share is likewise an
explicit proxy over same-game unconfirmed-anchor unions. Marginal B counts games
with any confirmed B anchor absent A, over the same labeled both-ran games,
and reports unique-B anchor counts separately. Thus both-catch games can still
show complementary coverage at different anchors. Pairs use deterministic
identity ordering, but both A given B and B given A are reported independently
with their respective unique-anchor counts. Neither direction is pooled or
hidden by pair ordering; a both-catch game can contribute directional coverage.

Declared bounded SciPy `special.betaincinv` supplies Beta(s+.5,n-s+.5) central
.05/.95 quantiles, including prior-only intervals when trials are zero (see
[official API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.betaincinv.html)).
Section 7's fixed guidance is printed literally as guidance; no promotion
verdict is inferred from live games with different selections.

Optional `--since SHA [--until REF]` enumerates only the requested git range
through `scripts/enumerate-merges.py`, labeling missing/unavailable evidence
without inferring reviewers. Enumeration preserves legacy celebration fields
and adds actual merge-subject PR number (null for non-PR merges), merge SHA
and commit date. Roar's legacy celebration writer remains compatible until its
separate retirement. No new sentinel is introduced.

## 7. Statistics policy (pre-registered, values fixed)

Fixed before implementation so post-hoc choices cannot reverse a verdict:

- **Prior and intervals:** Beta-Binomial with Jeffreys prior Beta(1/2, 1/2)
  per rate; report 90% credible intervals.
- **Eliminate** a seat when, over at least 10 labeled games, the 90% CrI
  upper bound of its false-finding share (hallucinations + noise findings
  ÷ findings emitted) exceeds 0.5 — the ling-flash 459/478 verdict is the
  template — or its run-failure rate upper bound exceeds 0.5.
- **Promote** a candidate only when its labeled-game catch-rate 90% lower
  bound exceeds the incumbent's 90% upper bound on the same labeled board,
  and its false-finding share upper bound is below 0.5.
- Report correlation always; act on it only when intervals justify it
  (≈60 labeled games per pair for fine distinctions; 10 per seat resolves
  only extreme gaps).
- Estimates are valid only per recorded model version; a model change
  splits the history (§4.2).

## 8. The reviewers skill (redesigned, thin)

Kept as the portable discovery surface the harness constitution requires
("let the runtime find who is available and route"). It stops managing
seats and trials.

| Keep in `reviewers` | Move to the coaching skill | Drop (replaced by) |
|---|---|---|
| Needs-description + contract prose | seat-runner + sandbox (replay tool) | panel.yml roster governance (author roster) |
| Padmé / OpenRouter live route docs | benchmark board + replay logic | scorecard/scores/trial machinery (§6) |
| Fail-open semantics for live routes | — | audition promotion logic (§7) |
| | | gaze auto request/harvest wiring |
| | | CLAUDE_TELEMETRY-style write seams |

Its SKILL.md scope statement changes from "manages seats" to "offers
external routes and board replay; coaching lives in attribution".

## 9. Celebration telemetry: teardown, not demotion

Investigated 2026-10-02. `~/.claude/telemetry/celebrations.jsonl` (2,182
records, 2026-04-06 → 2026-10-02, 26 projects):

- **Zero readers** anywhere in the harness (only the writer and its tests
  reference it).
- **Zero unique data**: every project is a git project (no
  `none-non-git-project` records exist), so every field is reconstructible
  from repo history + forge — which is what `enumerate-merges.py` does.
- The forge is the *better* source: it holds the cross-machine union the
  per-machine cache structurally cannot.

Teardown: delete roar step 2 (the fenced block), the `roar-last-sha`
sentinel, `log-celebration`, both telemetry tests, and the
`CLAUDE_TELEMETRY_DIR` seam (whose only setter was a test). **Migrate**
`enumerate-merges.py` to read-side tooling (attribution backfill and read
surfaces need exactly this capability). Leave `events.jsonl` and
`permission-diffs/` alone (different writers, out of scope). Merge-level
facts (project, PR, date) come from git/forge at read time; the
attribution records add what git never knew.

## 10. Teardown and ticket dispositions

Ordering: **capture lands before teardown** — a teardown-first sequencing
creates a recording gap.

- tickets/0356 (mined-defect benchmark) — absorb as the ground-truth seeding
  child of the tracker.
- tickets/0980 (audit seats across runtimes) — close WONTDO; its premise
  (seat each runtime behind the runner) is dropped by this design.
- tickets/0205 — close with an integration-review note once the tracker's
  capture children land; the trial verdicts already recorded (frontier
  retained; budget and padme-qwen not promoted) stand.
- Closed trial tickets (0206/0207/0217/0208/0346/0348/0353) — one annotation
  log line each pointing here; scorecards are historical evidence and are
  never deleted.
- tickets/0870/0936/0902/0990 (panel integrity) — untouched; internal panel.
- Delete at teardown: `skills/reviewers/` write path per §8, seat-runner
  tests, gaze panel-extension verbs. Keep: `benchmark-board.yml` (labeled
  corpus seed), `docs/research/ensemble-decorrelation-evidence.md`,
  decorrelation rule in `rules/workflow.md` (reworded off the seat
  mechanism), gaze fail-open semantics.

## 11. Portability

- The record format is plain markdown in the project repo: any runtime that
  can review a diff and write a file can participate, across Claude Code,
  Codex, Pi and Vibe. No runtime-branded paths (the `~/.claude/telemetry`
  lesson: a portable harness writing into a directory named for one
  runtime).
- Containment is the runtime's concern for its own reviewers; the
  seat-runner is containment only for untrusted external CLI routes.
- Skills state needs; the runtime routes. No fixed roster is mandatory.
