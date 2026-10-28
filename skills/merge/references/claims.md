# Close claims and edge cases

When merge reads this: step 0 (parsing the body), step 1 (closing), a
merge that skipped step 1, and the index of where each edge case lives.

## Ticket lines in the body

Close intent is read from the merge request **body** only — never the title:

- `**Ticket:** tickets/NNNN-...` or `**Ticket:** tickets/closed/NNNN-...`
  (bold or bare `Ticket:`) — a **close claim**: step 1 closes and archives
  the named ticket. An already closed and archived ticket is a clean no-op.
- `Ticket-ref: tickets/NNNN-...` — references a ticket **without closing it**
  (for annotating a deliberately-open ticket). Not a claim.
- `Ticket: NNNN` (short form) — a claim, once normalized: when exactly one
  `tickets/NNNN-*.erg` or `tickets/closed/NNNN-*.erg` matches, rewrite the
  body to the canonical path and read it back in the same command
  (`gh pr edit N --body-file <file> && gh pr view N --json body`), <!-- harness-extension-point -->
  so the claim audit can see it; zero or several matches: stop and fix the
  line by hand. Only a 4-digit ID alone after `Ticket:` qualifies — never
  `NNNN-slug`, `NNNN, MMMM` or `#NNNN`.
- `Ticket: none`, or no recognised `Ticket` line — the merge closes nothing.
  A malformed `Ticket: tickets/...` path is a stop, not a silent skip.
- Ticket lines inside Markdown code fences are examples and are ignored.
  The fence rules are the CommonMark subset implemented by `fence_map` in
  `$IDH_ROOT/skills/roar/check-close-claims.sh`: a fence closes only on a
  run of the opener's character at least as long as the opener, so a `~~~`
  line inside a backtick fence stays fenced.
- An **unclosed** fence whose remaining text holds a `Ticket:` or
  `Ticket-ref:` line with a `tickets/` path or a short ID: stop and close the
  fence first; the claim would otherwise be dropped or read from fenced text.
- Title prefixes like `chore(0216):` are subject references — they **never**
  close anything.

## Attribution block warning

The attribution block records who planned, wrote, reviewed and gated the
change. Its one record is the review's notes (ticket 1307), both modes:
`writer` entries hold the writer lines, each gaze answer's `attribution` field
the reviewer lines. Nothing on the review path edits a PR body. Check it once
at step 0:

```bash
python3 "$IDH_ROOT/scripts/attribution_record.py" --from-notes pr:N   # no forge: branch:<name>
```

It prints the block, or `missing` (no review) or `invalid: <reason>`. A request
opened before the switch, whose notes hold no valid block, is checked from its body:
`printf '%s\n' "$body" | python3 "$IDH_ROOT/scripts/attribution_record.py" --pr-body`.
On a forge, step 5a renders the notes block into the body, one whole-block edit
read back (`--render-pr N`); with no forge the block stays on notes.
`raid_land.py` runs both. `ok` is clean; `missing` or `invalid: <reason>` is a
warning; any other output or exit is `unchecked`, which is not an all-clear.
**Never refuse** on it: a missing block costs the record, not the merge. Surface
the warning in your report and let the author decide whether to complete the
block first.

## Line formats

The one home of the block's line shapes; raid, hunt and gaze cite it and do not
restate the fields. Facts come in order: `kind`, `pr`, writers, then reviewers.
The block assembled from notes keeps that order whenever a writer line was
recorded, so writers may be recorded at any time:

```bash
python3 "$IDH_ROOT/scripts/attribution_record.py" --record-writer '<line>' --unit pr:N   # or branch:<name>
```

writes a `writer` entry on the unit's review, locally, no network call (a unit
with no review yet gets one, opened on the current branch or `--branch`); the
latest line per `step=` wins. A no-forge unit's `pr:` line reads
`pr: branch:<name> · merged …`.

```text
writer: step=execute · runtime=claude · model=<provider>/<model-id> · effort=not-stated · route=<route> · independence=not-stated
reviewer: step=review · seat=correctness · runtime=codex · model=<provider>/<model-id> · effort=not-stated · route=<route> · independence=cross-family · status: ran
```

- Writer: `runtime`, `effort`, `model` (verbatim provider-qualified id), plus `step`
  (`plan`, `execute`; distinct per line), `route`, `independence`. `effort`, `route`
  and `independence` take `not-stated` when unknown.
- Reviewer: `seat`, `runtime`, `model`, `status: ran|failed|skipped`, plus `step`,
  `effort`, `route`, `independence`; `finding:` lines follow a `ran` reviewer.
- A masked identity replaces `model=` with `model-state=` and `model-evidence=`.
- Gaze generates the reviewer lines from the plan and the worker headers (`gaze_close.py`;
  no seat types them, ticket 1303) into its answer on notes; a bare model id takes the
  seat's `family` as provider prefix. Every answer's lines join the block, one per attempt.
- Check with `--from-notes` (strict), or `--pr-body` for a body: the block, `missing` or `invalid: <reason>`.

## Repair

A merge that skipped step 1 lands the code and drops the claim with no
output; `erg check` passes either way. First confirm no close commit rode
the merge request; if one did, there is nothing to do. Otherwise, on a new
branch: `erg close <ID> <reason>` edits the ticket file but does **not**
stage its own edit, so `git add -u tickets/` BEFORE the move to `closed/` and
the commit — otherwise the commit carries the rename with the pre-edit blob
and silently drops the `Closed:` header.

## Where each case lives

| Case | Where |
|---|---|
| Body-claim grammar: fences, short ids, `Ticket-ref` is not a claim | above |
| Close-commit text `ticket(<ids>): close and archive — PR #N` | step 1 |
| Never arm auto-merge on a gated base; disarm a stray one | step 5 |
| Mark a draft ready | step 2 |
| No `--delete-branch` | step 6 |
| Re-recording after the base moves | step 4: spends no review round |
| Approval covers the head (bookkeeping delta at most); gate record on the same head | merge § Gating tiers and § Before merging; step 6 pins it |
| Body edited after approval | step 3: re-read and compare the claims with the ruled set |
| Attribution-block warning | § Attribution block warning |
