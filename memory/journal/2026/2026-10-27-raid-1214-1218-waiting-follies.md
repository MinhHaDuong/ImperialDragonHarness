# Raid 1214, 1216, 1217, 1218 — waiting follies (2026-10-26/27, night mode)

Context: `/raid 1214 1216 1217 1218` on the harness, orchestrator Opus 5.5 in Claude Code. During the run the author
stated night mode: escalations go to Fable to finish, not to the author.

Events:

- Imagine (four opus seats) and a blind-spot pass (fable). The blind-spot pass reported that arena commit 390ee03 (ticket
  1114) already rails `pgrep`/`pkill` with `-A` on the leg PATH, that `rules/` projects to `~/.claude/rules` only
  (adapters/projections.json), and that the arena stall census ranks sleep-polling on one's own job (161 stalls, 26,151 s)
  far above self-matching `pgrep` (10, 4,147 s). The orchestrator checked the first two directly.
- Positive control on padme, procps-ng 4.0.4: a shell whose command line holds a marker is matched by plain
  `pgrep -f marker` (2 hits) and not by `pgrep -A -f marker` (0).
- The author asked the orchestrator to put the 1216–1218 decisions to Fable. Fable's one-shot verdict: a harness-side
  `pgrep`/`pkill` wrapper projected to `~/.local/bin` for all three runtimes (fix the primitive) instead of a rule line or
  a guard clause; 1217 narrowed (denial counts as data, verdicts to /pulse; bounds instead of hours); 1218 closed and
  routed. Fable named three errors in the raid's framing, recorded in ticket 1216's log.
- The author added an exit criterion to 1216 mid-run: the wrapper is checked on `idh install`.
- PR 1678, 1679, 1681: ticket-only annotation PRs, bookkeeping tier, merged by the gated recipe. PR 1681 also closed 1218.
- PR 1680 (1214): hunt's gaze rounds 1–3 returned FINDINGS (a bare script path; a non-UTF-8 diff crashing the snapshot
  and exiting with the wake code; untracked rewrites invisible). Hunt escalated after round 3; a Fable finisher clamped the
  sleep to the deadline, made a failed git poll "no observation", and reached REVIEWED in round 4. verify-gate round 1
  APPROVED; merged at d6b09a4c.
- PR 1682 (1216): gaze REVIEWED in two rounds. verify-gate round 1 REROLL: the pipefail guard flagged the POSIX sh wrapper,
  and `test_mammoth_audit` failed because `idh install` exited 1 on SHADOWED. The redteam seat had raised the SHADOWED
  exit as a non-blocking consider in both gaze rounds; nothing ran the full suite before the gate. The orchestrator made
  SHADOWED advisory (reported, exit 0; RECURSION, NOREAL and LEAKY still fail). Round 2 APPROVED; merged at 63f3620b.
- PR 1683 (1217): gaze REVIEWED in round 3; verify-gate round 1 APPROVED; merged at bdb7bc8b. All cycles, 472 Pi
  sessions at 45 s or more: detector 589 stalls (123,192 s) vs census 586 (122,954 s); self-matching pgrep 11 vs 10–11.
- All review seats were Anthropic (sonnet or fable); no cross-family seat ran.

Outcome: 1214, 1216, 1217 closed by merged PRs; 1218 closed and routed to 1216 and the next /pulse visit. `make check` on
main 9bf9ab4a passed (2309 passed, 4 skipped). The 1216 re-measure is due on or after 2026-11-03 (ticket 1217 log).

References: tickets/closed/1214-*, 1216-*, 1217-*, 1218-*; PRs 1678–1683; docs/2026-10-27-follies-c4-census-comparison.md.
