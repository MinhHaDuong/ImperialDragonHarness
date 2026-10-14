# R1 evidence census (scientist seat), 2026-10-14

Method: du/ls/rg/python read-only; sizes are apparent bytes (python os.walk) unless stated. Doudou reachable over ssh (BatchMode ok).

## 1. Current /tmp
- padme: tmpfs 32G, 16G used (48%). Booted 2026-10-11 21:07 (uptime -s), so all 16G accumulated in about 3 days (derived). 992 top entries; 983 haduong, 18 root. 0 haduong entries older than 7 days (find -mtime +7 = 0), consistent with the reboot.
- By pattern (measured): `t[0-9]*` 135 entries 11.9G (t2093 5.5G, t2094 6.1G; traces tie both to the climate-finance-het project: subagent agent-a298ece4fbdea3294 of session 33d7deec, plus this 1095 session); numba/nbc/nc*/nb1372 caches 1.9G; `glossary-0882-*` 85 dirs 371M (mode 700, mkdtemp-style names: per-test project leak, inferred); `/tmp/claude-1000` 248M (JETP-observer key 237M); `pytest-of-haduong` 173M (5 basetemps); `tmp*` 109 entries 2.5M; `pi-bash-*.log` 4 files about 2.3M (largest 1.7M, 12 Oct).
- doudou: tmpfs 12G, 1.7G used (15%), 1042 entries (1032 haduong). Largest: idh-1080-uv-cache 235M (harness raid 1080), legacy-inventory 196M, pytest-of-haduong 148M, many `glossary-0882-*` at about 26M each (same project test leak), rv1378, t1091-*. Not near the quota today. 226 project dirs in ~/.claude/projects there (not scanned).
- Doudou quota: ticket 0854 body: 12G tmpfs, usrquota, systemd caps a user at 80% (about 9.6G; inferred cap).

## 2. Episodes
| Date | Episode | Class | Source |
|---|---|---|---|
| 2026-09-06 | doudou /tmp EDQUOT; Bash dies exit 1 with no output in 3 sessions, ended in reboot. Filler named by the author: `/tmp/zoteus-wrong*`, `zoteus-validation-*`, upstream vitest suite leaking one per test (zotero ticket 0714). Session arenas (1.9G) were not the filler. | project test | tickets/closed/0854 body; ~/.claude/projects/-home-haduong-CNRS-code-search-works-for-zotero/memory/feedback_tmp_quota_kills_the_shell_silently.md |
| 2026-09-06 | Harness scratch `/tmp/claude-<uid>/...` never deleted (13 dirs, 3 alive an hour after reboot) -> on-end.sh, session_scratch.py, molt 1.7 (PR 812) | harness | 0854 |
| 2026-09-16 | git-erg PR 352 review: /tmp full of leftovers of unrelated sessions (`jetp-*`, `rev461*`, `t07*`); reviewer subagents told to relocate TMPDIR to a home scratch dir | agent ad hoc dirs | ~/.claude/projects/-home-haduong-CNRS-code-git-erg/a27d6179.../subagents/agent-a5f60d1fed89ed485.jsonl, 2026-09-16T12:00Z |
| 2026-07-13 | gaze review worktrees in /tmp/review-N sat outside guards -> moved under .claude/worktrees (0300); maw-audit /tmp/maw-*, /tmp/fang-* detached trees: exemption documented, self-cleaned (0303) | harness worktrees | tickets/closed/0300, 0303 |
| 2026-09-28 | a locked tree under a dead pid held the last on-disk copy of purged memory; the lock blocked every GC pass -> stale-lock rail | worktree GC | scripts/worktree-gc.sh around l.110 |
| current | worktree-gc purges only `.panel/` and `build/panel-head/` | harness evidence | skills/molt/SKILL.md l.82-84; scripts/worktree-gc.sh l.142-149 |
| 2026-10-14 | JETP-observer STATE line 31: "Parallel pytest runs exhaust doudou's /tmp quota: set TMPDIR under ~/.cache" | project test, mitigation text | ~/CNRS/projets/actifs/JETP-observer/STATE.md:31 (path is projets/actifs, with a slash) |
| 2026-10-11/12 | t2093/t2094 audit outputs 11.4G within 3 days of reboot | agent ad hoc task dirs | du above |

## 3. Counts and controls
- Trace grep over padme ~/.claude/projects jsonl: "No space left on device" 5 files, "EDQUOT" 17, "Disk quota exceeded" 1. Positive control: the grep finds the known 0854 text. Nearly all hits are the same quoted healthcheck/molt skill sentence ("kills the Bash tool with EDQUOT ... ticket 0854"), tests mocking OSError(28), or this panel. Genuine live failures: 1 (2026-09-16 git-erg review) plus the 2026-09-06 note. Inference: padme traces hold about 0-1 real disk-full events; the documented outages are doudou's. Doudou traces not scanned.
- Harness memory (journal, topics): 0 disk-full episodes; "quota" hits are API token quotas only (control: grep finds topics/runtime-observations.md:80 DashScope quota). Supports only that scope.
- Pi sessions: 60 jsonl, 1 mentions No space/EDQUOT (not opened; likely this panel).
- Cleanup that destroyed something wanted: no /tmp sweep incident found. Nearest: worktree deletion incidents (feedback_worktree_deleted_midrun_orphans_cwd, raid-217 2026-07-13) and the 2026-09-28 stale-lock near-miss. Weak null: I searched feedback_* names and the journal only.
