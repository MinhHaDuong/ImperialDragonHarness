# merge — cases
Updated: 2026-11-01 · skill version: 8bc0d4d2

## Rebase after a sibling merge, PR 2150 — 2026-11-01
Context: PR 2150 (Pi case notes) was ready when PR 2155 landed first. What happened: rebase onto main conflicted in the shared test file. Reaction: resolved as the union of the Codex and Pi tests, re-gazed narrow, gated again. Outcome: APPROVED in round 1, merged as a5fd217e; `raid_land.py --cleanup` removed worktree and branch. Use: this conflict needed a rebase and a narrow re-gaze, not the author. Source: memory/journal/2026/2026-11-01-raid-1f0534-late-merges.md.

## Stale gate records, PR 1725 — 2026-10-27
Context: ticket-only PR 1725, gate record on a busy main. What happened: two records went stale as PRs 1726 and 1722 merged meanwhile. Reaction: stopped after one re-record and reported, as the recipe says; the author answered "Just merge, dont rerun the tests", and the merge used `--match-head-commit`. Outcome: MERGED, bypass noted on the PR. Use: record, merge, retry once, then report; an author waiver covers that PR only. Source: memory/journal/2026/2026-10-27-raid-sitrep-ticket-1246.md; memory/topics/commission.md.

## Hand close dropped a ticket, PR 1924 — 2026-10-28
Context: PR 1924 for ticket 1316, closed by hand. What happened: `erg close` already moved the file, so `git add -u tickets/` staged only the deletion; the pushed commit dropped the ticket and `erg check` passed. Reaction: amended, force-pushed with lease before the gate. Outcome: no ticket lost. Use: land through `scripts/raid_land.py`, which stages both sides; after any hand close, read `git show --stat HEAD`. Source: memory/journal/2026/2026-10-28-erg-close-hand-recipe-dropped-ticket.md.

## Gate record push, PRs 2033 and 2035 — 2026-10-30
Context: the gate record reached local `refs/notes/gate` but not origin's. What happened: another process rewound the local ref, so a push by ref name exited 0 and sent nothing (ticket 1366). Reaction: PR 2033 pushed by commit id with an `ls-remote` read-back; PR 2035 kept the commit-id push and dropped the read-back. Outcome: the author ruled 2026-11-01 (ticket 1373) that the exit code answers for a commit-id push; the exception stays in memory, `rules/git.md` unchanged. Use: add no read-back to a push by commit id (`scripts/merge-gate.py`); a push by ref name still needs one. Source: memory/journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md.
