# Regression seat — PR 1378

Reviewed SHA (final): 9e2fdd3fb5706f452722718967524ac8985a43cf (base origin/main); earlier pass at 7e1f77b1928ee49de97990940fd4b24b3df49cc7, retained below
Seat: regression (prior Correctness/Consistency/Doc-propagation claims + adversarial assumptions); claude-sonnet-5-5, medium; Anthropic family, so decorrelated from the gpt-6.1-sol producer/prior seats.
Anchor: review-pr-anchor.py 1378 --worktree <tree> run before and after; both returned HEAD 7e1f77b1 and the same 4 changed files (census script, census test, tickets 1091, 1092). Tree untouched (no writes except this artifact).
Limitation: pytest cannot import `yaml` in this sandbox, so I did not re-run the suite; suite claims rest on the supplied logs, and behaviour on my own /tmp experiments (a `git archive` of HEAD, indexed in a scratch repo).

## Prior claims tested
| Claim | Result |
|---|---|
| Tracked directory symlink owns its card | Holds. Scratch: staged `skills/tl` symlink → `tracked`, `skills` +5. `scripts/resident_census.py:228`. |
| Untracked regular dir and untracked link → `skills-local` | Holds. `ud` and `ul` both `untracked`; links line reads `present`. |
| Unavailable Git metadata → conservative full cost | Holds. No `.git`, `GIT_DIR=/nonexistent`, root nested in another repo: all cards in `skills`, "unknown". Test at tests/test_resident_census.py:213. |
| Session total includes supplement | Holds. `channel_chars` includes `skills-local`; `session_chars` sums it. primary log 43994 = 43162 + 832. |
| 7000 cap on tracked cards; real 832 visible | Holds. Primary log: skills 6952, skills-local 832 (282+275+275), inventory lists the three as untracked. Old control log: 7784 vs 7000 (reproduces the overflow). |
| Counted inventory / link presence-absence | Holds in both detail and non-detail modes (`_render`). |
| Do not demand a local-content cap | Respected; none required. |

## Gate evidence (judged)
- /tmp/t1091-full-clean-final.log and full-overlay-final.log: each `1606 passed, 4 skipped` (1610 items). Log mtimes (11:47:57 / 11:48:17) fall after the HEAD commit (11:46:10) and a ~104 s run, so they plausibly ran on this head; the logs themselves do not print a SHA. The overlay clone's HEAD reads back as 7e1f77b1, status clean, with the three live symlinks present.
- Same-head overlay clone is a legitimate contained proxy. It does not prove the literal primary gate (different checkout path, full repo with worktrees). The ticket and prior review both say the primary gate runs after merge, and I do not count it as passed.
- /tmp/t1091-primary-observed-using-new-census.log is a read-only census at the primary, not a test run; it supports the 6952+832 numbers only.

## Findings
No blockers. No correctness regression found.

1. consider: a new skill card that is not yet `git add`ed escapes the 7000 cap locally. Confidence high; severity minor; scripts/resident_census.py:228 with tests/test_resident_census.py:83 (the `entries` fixture runs `rc.census(REPO)` on the live checkout). Scratch: a 5007-char unstaged `skills/newcard` reports `skills 6952` and `skills-local 5007`; after `git add` it reports `skills 11959`. So `test_channel_budgets` is green on the author's machine until staging, red in CI. This follows from the ticket's chosen Git-index semantics and the cap still holds for committed content, so not a blocker. The failure surfaces at the gate, not at the merge.
2. consider: inherited `GIT_DIR`/`GIT_INDEX_FILE` are honoured by the git subprocesses (no `child_env`). Confidence medium; minor; scripts/resident_census.py:197-207. Scratch: `GIT_DIR` pointing at an unrelated empty repo yields `skills 0`, `skills-local 11959`, "Git index". The `skills` floor in `test_every_channel_is_populated` would catch it, so the blind spot is bounded.
3. nofollow: stale SHA in ticket 1091 execution evidence. "Code commit `0de58dd4`" is not an ancestor of HEAD (`merge-base --is-ancestor` exit 1); HEAD differs by a 2-line test change plus ticket text. Final-head logs were run at 7e1f77b1, so the numbers hold; only the reference is stale.
4. nofollow: "Local skill links: absent" can coexist with non-zero `skills-local` when the local cards are ordinary directories (verified: `newcard`). The wording says links, the inventory shows the cards; accurate, slightly easy to misread.
5. nofollow: PR also edits ticket 1092 (annotation only, no script change in this diff); the wave annotation is consistent with 1091 and introduces no code.

## Residual
Literal primary full gate unverified until after merge (explicitly acknowledged by the PR). Proxy result: contained same-head clone with the exact live overlay is a reasonable stand-in; the old-census red control shows the test can fail.

## Final-head update (9e2fdd3f)
- Anchor run before and after: HEAD 9e2fdd3f, same 4 changed files.
- Code identity: `git rev-parse HEAD:<path>` gives scripts/resident_census.py = 53cc93c6f9bbd67c6bf94672e98152d39041e5fa and tests/test_resident_census.py = e577eb10bdd5ceed22fcaf34f587debc61b0b8a8, as stated. `git diff --name-only 7e1f77b1 HEAD` lists only tickets/1091-...erg (+41/-4). All earlier code-level conclusions and the suite logs transfer unchanged; I did not re-run the suite.
- Ticket delta: the four criteria are checked; a log note and a "Completed criteria" section are added. The text matches the logs: 6952+832, 43994/43162, 7784 old control, 1606 passed / 4 skipped on the clean tree (104.06 s) and on the primary (76.91 s). The prior historical sections are preserved.
- Actual primary evidence: /tmp/t1091-actual-primary-manifest.log records HEAD 7e1f77b1928ee49de97990940fd4b24b3df49cc7, original branch housekeeping-20261012 at 1e8ccb3874f2f7bd0c12be05ae3d35f1cc656b53. /tmp/t1091-actual-primary-full.log shows rootdir /home/haduong/.agents (the primary), 1606 passed, 4 skipped in 76.91 s. So the literal primary gate has passed before merge on the same code as the tree at 9e2fdd3f. This supersedes my earlier "unverified until after merge" residual. Not independently checkable by me: the three live links being present during that run, and the branch restore being clean; these rest on the ticket and manifest statements, and I did not access the primary.
- Prior findings carried unchanged: 1 consider (unstaged new card escapes the local cap), 2 consider (inherited GIT_DIR), 3 nofollow (stale `0de58dd4` reference; the ticket keeps it as historical evidence), 4 nofollow ("links: absent" wording), 5 nofollow (1092 annotation only). Nothing new.

## Verdict
approve (final head 9e2fdd3f)
