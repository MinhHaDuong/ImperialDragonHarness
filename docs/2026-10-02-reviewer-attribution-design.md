# Reviewer attribution — design spec

Date: 2026-10-02
Status: approved design (author, this session) — awaiting implementation
Tracker: tickets/1004 (this doc is its deliverable)
Supersedes: the seat-runner-centric panel contract of tickets/0205 (which stays
open until the ticket dispositions in §10 land)

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
GROUND TRUTH → defects-confirmed lines (inside the same records; backfilled)
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
for context. Findings carry anchors normalized `basename:line` (the board's
existing convention) so cross-reviewer matching is mechanical.

```
memory/journal/2026/2026-10-02-review-attribution-pr1102.md

kind: review-attribution
pr: 1102 · merged 2026-10-02 · project: .agents
writer: runtime=vibe · model=<model-id> · effort=standard
reviewer: seat=<name-or-role> · runtime=<id> · model=<model-id>
  finding: verifiable · <basename>:<line> · adopted: yes|no
  finding: consider · <basename>:<line> · adopted: yes|no
defects-confirmed-post-merge: none | <basename>:<line> ...
```

Rules:

1. **Fixed lines for facts.** Named fields at fixed positions; the schema-drift
   lesson (§1.2) makes this non-negotiable. A read surface must never parse
   prose.
2. **Version pinning is load-bearing.** Model ids are recorded at review time;
   upstream models are silently retired (deepseek-v4-flash incident), so a
   record without a version is unusable for re-audition.
3. **The writer is part of the pair.** Decorrelation is reviewer-vs-writer;
   the writer line makes that measurable.
4. **Anchored findings are the join key.** Same basename:line across two
   reviewer lines = shared catch; exactly one = unique catch; anchored by
   nobody but later confirmed = panel-miss defect.
5. **Project-local.** Records live in the project's repository (or its
   explicitly configured private companion), per the harness memory boundary —
   never in the harness, never in a native memory directory, never in
   machine-local telemetry.
6. **Fail-loud capture.** A reviewed PR whose record cannot name its
   reviewers is a defect to report, not an omission to fill in from memory.

## 5. The coaching loop

1. **During review (unchanged, free):** the runtime reviews its own way;
   external routes optional via the descriptor skill.
2. **At wrap-up:** roar step 6 writes the attribution record.
3. **After merge, when a fix lands:** roar step 3's sweep ("review the fix
   just completed — grep for the same anti-pattern") gains one hook: a
   post-merge fix on lines a past review covered backfills
   `defects-confirmed-post-merge` in that PR's attribution record. This is
   the only source of the pair table's "neither" cell and the only thing
   that makes a game defect-bearing; without it correlation estimates skew
   optimistic.
4. **Offline, on demand (commissioned coaching cycle):** the replay skill
   runs any candidate over the frozen labeled board — same diffs for
   everyone, which the live record cannot give (selection bias: only
   reviewers who played have facts). Replay through the seat-runner is the
   containment wrapper for untrusted external CLI models only;
   runtime-native reviewers need no sandbox.

## 6. Read surfaces (derived, never stored)

A scores-style query over all attribution records of a project:

- **Scores:** per seat, labeled-game catch rate with credible intervals;
  noise rate; run-failure rate.
- **Correlation:** pairwise concordance table (both / unique-to-A /
  unique-to-B / neither), including writer-reviewer pairs; Jaccard
  catch-overlap and shared-hallucination rate. Conditions on defect-bearing
  games only (§1.1's base-rate discipline).
- **Marginal coverage:** unique-catch rate of seat B given seat A already
  plays — the squad-management quantity; raw catch rate overstates it.

## 7. Statistics policy (pre-registered)

- Per seat: Beta-Binomial credible intervals on labeled-game catch rate;
  eliminate when the noise or hallucination upper bound crosses threshold
  (the ling-flash 459/478 verdict was correct and is the template);
  promote only when the catch-rate lower bound beats the incumbent's upper
  bound on the same labeled board.
- Report correlation always; act on it only when intervals are narrow enough
  to matter (≈60 labeled games per pair for fine distinctions; 10 per seat
  resolves only extreme gaps).
- Estimates are valid only per recorded model version; a model change
  splits the history (§4.2).

## 8. The reviewers skill (redesigned, thin)

Kept as the portable discovery surface the harness constitution requires
("let the runtime find who is available and route"). It stops managing
seats and trials.

| Keep | Drop (replaced by) |
|---|---|
| Needs-description + contract prose | panel.yml roster governance (author roster) |
| Seat-runner + sandbox, as replay tool | scorecard/scores/trial machinery (§6) |
| Benchmark board + replay logic | audition promotion logic (§7) |
| Padmé / OpenRouter route docs | gaze auto request/harvest wiring |
| Fail-open semantics for live routes | CLAUDE_TELEMETRY-style write seams |

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
