# Close claims and edge cases

When `/merge` reads this: step 0 (parsing the body), step 1 (closing), a
merge that skipped step 1, and the checklist of cases the retired merge
helper handled (ticket 1178).

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
  `$IDH_ROOT/skills/roar/check-close-claims.sh`, the one retained reader:
  a fence closes only on a run of the opener's character at least as long as
  the opener, so a `~~~` line inside a backtick fence stays fenced.
- An **unclosed** fence whose remaining text holds a `Ticket:` or
  `Ticket-ref:` line with a `tickets/` path or a short ID: stop and close the
  fence first; the claim would otherwise be dropped or read from fenced text.
- Title prefixes like `chore(0216):` are subject references — they **never**
  close anything.

## Attribution block warning

The body's single fenced `attribution` block records who planned, wrote,
reviewed and gated the change. Check it once at step 0:

```bash
printf '%s\n' "$body" | python3 "$IDH_ROOT/scripts/attribution_record.py" --pr-body
```

`ok` is clean; `missing` or `invalid: <reason>` is a warning; any other
output or exit is `unchecked`, which is not an all-clear. **Never refuse** on
it: a missing block costs the record, not the merge. Surface the warning in
your report and let the author decide whether to complete the block first.

## Repair

A merge that skipped step 1 lands the code and drops the claim with no
output; `erg check` passes either way. First confirm no close commit rode
the merge request; if one did, there is nothing to do. Otherwise, on a new
branch: `erg close <ID> <reason>` edits the ticket file but does **not**
stage its own edit, so `git add -u tickets/` BEFORE the move to `closed/` and
the commit — otherwise the commit carries the rename with the pre-edit blob
and silently drops the `Closed:` header (aedist PR #1008; a 100%-rename,
0-insertion commit is the tell). The sweep `check-close-claims.sh` reports
`DROPPED` and `UNRESOLVED` claims over a window; it does not audit short-ID
claims, which is why step 0 normalizes them.

## Edge-case checklist

Each duty the retired merge helper carried, and where it lives in the recipe.

| Case | Where |
|---|---|
| Body-claim grammar: fences, short ids, `Ticket-ref` is not a claim | above; `check-close-claims.sh` keeps the fence reader |
| Close-commit text `ticket(<ids>): close and archive — PR #N` | step 1; read by `$IDH_ROOT/scripts/enumerate-merges.py` |
| Never arm auto-merge on a gated base; disarm a stray one | step 5 |
| Mark a draft ready | step 2 |
| No `--delete-branch` | step 6 |
| Merge requests open at the cutover | they follow the recipe as they stand: step 1 closes a ticket the branch has not closed yet; that close is a bookkeeping delta, so an APPROVED verdict on the old head still covers it (§ Gating tiers) |
| Re-recording after the base moves | step 4: mechanical, spends no review round |
| Review approval covers the head (bookkeeping delta at most); gate record on the same head | § Gating tiers, § Before merging; step 6 pins it |
| Body edited after approval | step 3: re-read and compare the claims with the ruled set |
| Attribution-block warning | § Attribution block warning |
| A merge without a record | nothing refuses on the merge path: the guard hook (enforce mode) and `main_sweep.py` (`/lair` step 15) report it afterwards |
