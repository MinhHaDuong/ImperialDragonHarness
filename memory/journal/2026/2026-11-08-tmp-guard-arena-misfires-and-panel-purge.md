# 2026-11-08 — tmp guard: three arena misfires, and a reproduction that purged `.panel/`

Context: the arena session (a forge-less local repo) reported that
`worktree-tmp-guard.py` refused its merged worktrees, holding about 10 GB of `.tmp/`.

- Ticket 1470 (raid f1c4d5, PR #2272): the guard refused the none backend's string
  request ids. The guard now accepts an int or a single safe path component. Arena then
  cleared 13 worktrees, about 9 GB.
- Arena then reported two more misfires, fixed in PR #2274 with no ticket, below the
  floor, at the author's request:
  - a binary `.png` under `.panel/` failed the strict UTF-8 read;
  - a recorded base branch deleted after merge made the none listing refuse. Such a
    row is now listed `UNRESOLVED` under `--state all`.
- Near miss: arena labelled its reproduction command
  (`worktree-exit-preflight.sh --removal …`) read-only. This session ran it twice
  without reading the script:
  - At about 20:40, for the 1470 positive control, on arena t1211. That worktree was
    later removed by arena.
  - At about 21:56, for the 2274 positive control, on arena t1210. That run deleted
    `.panel/`, which held a raid evidence archive. Arena found a byte-identical copy on
    main (`docs/raids/arena-1210-evidence.tar.gz`), and t1211's evidence is also on
    main.
- Cause: the preflight and `worktree-gc.sh` purged `.panel/` and `build/panel-head`
  before the residue check that can still refuse the removal (design `accbe9a0`,
  2026-09-23). The guard script alone (`worktree-tmp-guard.py removal …`) deletes
  nothing.
- PR #2275 moved the purge after the check, at the author's request.
  - Gaze round 1 (an OpenAI red-team seat plus a self reproduction) found the new
    residue filter matched any status code, so a staged rename out of `.panel/` with an
    edit passed removal.
  - Fixed to drop only `??` and `!!` records. Round 2 was REVIEWED and the gate
    APPROVED.
- Open `consider:` findings, reported to the author, not adopted:
  - UTF-16 or gzip `.tmp/` citations in `.panel/` no longer block (#2274);
  - quoted scratch paths are refused rather than purged (#2275, a `git status -z`
    match would fix it).
