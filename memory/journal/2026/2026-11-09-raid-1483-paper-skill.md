# 2026-11-09 — raid 8d6894 on ticket 1483: /paper skill, PR #2325

Context: single-ticket raid on padme, author live in parallel on doudou.
Merged 01d7c2f4 (PR #2325, ruled tip cf23bcba, gate session cd0959c4).

Observable events:
- The ticket changed under the raid three times while Imagine and Plan ran:
  skill renamed fly → paper (4ab448e0), a sixth exit criterion added (344f3fe3,
  skill/AGENTS.md boundary), and `~/CNRS/papiers/AGENTS.md` written on doudou at
  17:33 with the memory file reduced to a pointer. The executor rebased onto
  main and picked the criterion up; the orchestrator rewrote its annotations.
- Gate round 1 ruled REROLL: two criteria were acts on doudou (the directory
  AGENTS.md, the live dry run). The author chose option A in chat. The
  directory half was verified read-only over ssh (doudou, 3241 B, names /paper
  and 1483); the dry run moved to ticket 1489 (needs-human) because the CNRS
  directory has no ticket store. Round 2 APPROVED on a bookkeeping-only delta.
- WAVE_BASE a9c436fd is not an ancestor of main: the executor's rebase replayed
  the annotation commits, so the raid session branch raid-1483-session ended
  patch-equivalent but not merged by ancestry.
- `make check` in the executor's worktree failed 4 tests asserting "outside a
  git repository" with TMPDIR set inside the worktree (hunt § Worktree); the
  same tests passed by name with the default TMPDIR. No single clean run on record.
- Inputs the ticket named were absent on padme: the REALF How-to 44 PDF, the
  memory file `reference-realf-howto-44-release-checklist.md`, the CNRS registers.
  The `accepted` HAL step carries "confirm against How-to 44".
- After-merge runner on 01d7c2f4: pass, six checks, pytest-guard 34 s.

Decisions already made: author's naming rule (object skills carry the
directory's name; dragon verbs stay for the harness on itself); author decision
A (split the doudou acts out). Queued, not decided: who runs 1489 and when;
whether "nothing to do except HAL" is still the expected row set given 1484's
HAL PUT; Zenodo related identifiers and a git tag per event as convention.

References: tickets/closed/1483, tickets/1489, PR #2325 comments, raid log
raid=8d6894, review rv-20261109-pr-2325-0a7a.
