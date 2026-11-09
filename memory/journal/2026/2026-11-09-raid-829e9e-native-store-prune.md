# Raid 829e9e: ticket 1481, native-store prune across two hosts

Date: 2026-11-09. Single-ticket raid on the harness, PR #2323 merged at
b202667b (bookkeeping tier: journal and ticket only; the change itself was
made outside the repository, on `~/.claude/projects/<key>/memory/` of two hosts).
The prune's own record is
[2026-11-09-native-store-prune-1481.md](2026-11-09-native-store-prune-1481.md).

## Events

- Imagine (Opus seat) checked every live note of the three named stores on
  padme against harness history: all byte-matched reachable blobs. It scoped
  climate-finance-het as a partial prune and kept JETP-observer and git-erg.
- The Blind-Spot pass (Fable seat) found that doudou holds its own copies of
  every store, read-only over ssh: climate-finance-het there had 310 notes
  against 11 on padme, about 200 never imported anywhere; sen-causal-reading
  had 15 notes there and none on padme; padme's own store on doudou had never
  been pruned. No sync exists between the hosts. The raid scoped doudou in
  under the same per-note invariant. It also found free "key insights" lines in
  the native indexes that a pointer rewrite would have discarded.
- Feasibility found a live Claude Code session in climate-finance-het on
  padme; the executor skipped that store on that host and recorded the
  classification it would have applied.
- The executor (Opus, coder profile, hunt inline) deleted 265 notes on padme
  and 354 on doudou, kept the audience-excluded notes, rewrote the indexes,
  and opened six ticket-only merge requests in the projects whose stores
  changed (AEDIST #1198, Tracing-Kieu #185, fuzzy-corpus #74,
  climate-finance-het #2050, padme #258, sen-causal-reading #171), all left
  open for the author.
- `raid_land.py 2323 --ruled-head - --ruled-claims -` was refused: the close
  claims in the body (`1481`) must equal the ruled set even at bookkeeping
  tier. The call with `--ruled-claims 1481` landed the PR. The raid skill's
  Phase 7 text shows `-` for no verdict.
- The executor reported that hunt's per-command `TMPDIR="$W/.tmp"` made
  `make check-fast` hang in `tests/test_review_trajectory.py::test_unreadable_repo_is_not_checked`
  (a tmp_path inside a git worktree scans the real history); the run with the
  default TMPDIR passed (1757 passed, 2 skipped). Below the ticket floor;
  nothing filed.
- AEDIST's `erg new` warned that its next-id scan timed out; the ticket took
  id 0690, to be checked for a claim conflict at its merge.
- The first annotation append went to a filename typed from the ticket title
  instead of the real one (`1481-prune-the-native-claude-memory-stores-of.erg`);
  the pre-commit ID-claim check caught the duplicate id.

## Timing

execute about 25 min (launch to PR), merge 46 s; first sitrep to merge 1 h 02 min.
