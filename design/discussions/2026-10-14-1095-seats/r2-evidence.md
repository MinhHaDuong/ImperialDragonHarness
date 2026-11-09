# R2 evidence (scientist seat)

## Measurement check
- doudou: the ssh attempt just now failed with "No route to host" (round 1 reached it). So I cannot report doudou's current /tmp or ~/.cache; the doudou half of the architect's proposed measurement is unperformed, not null.
- padme ~/.cache (du, today): 68 entries, 7 match `t*`/`tmp*` stems. Those are `tmp-t1045` 356M, `tmp-t2061` 285M, `t0279tmp` 108K, plus `jetp-check` 2.3G (pr153/, pr155/ subdirs). Tool caches dominate: huggingface 28G, uv 8.8G, pip 1.4G. So the architect's premise that ~/.cache is where the STATE-line-31 idiom lands is confirmed: the task temps there carry stems (`tmp-t<N>`) that the proposed grouping catches, but the report must exclude tool caches or the top-N is 28G of huggingface (this is a design requirement, not a finding about leaks).
- padme /tmp stems (round 1): `t<N>-*` 135 entries 11.9G; `glossary-0882-*` 85/371M; both would be surfaced by the proposed patterns (positive demonstration by my own census, using a similar sed grouping).

## Round-1 objections: answered or not
| Objection | Status |
|---|---|
| Moving 11.9G to /home transfers risk | Answered by honesty (both filesystems reported, residual 1 stated). Still a choice of failure mode. |
| Evidence (t2093 JSONs) lost to purge | Answered: no purge, only worktree removal, plus "evidence never goes there" and a size line. Remaining weakness below. |
| Zoteus/glossary untouched | Acknowledged as residual; Option 1's repeated-stem detector names them. Not fixed, correctly out of scope. |
| Other-host liveness / age rail | Answered by dropping B. |
| Skill grep misses env-set caches | Partly: the report scans by stem, so `idh-1080-uv-cache`/`arena-uv-cache` surface; the rule still names only logs/caches/venvs written by the agent, not caches set by launched raids (unaddressed). |
| Review worktrees cannot read the author's `.tmp/` | Not addressed. |

## Option 1 (report-only)
- Would have helped: 2026-10-12 (t2093/t2094 named the day they grew, ~5G/day derived); 2026-09-16 git-erg review (the `jetp-*`, `rev461*`, `t07*` stems would have been listed before the reviewers hit ENOSPC, only if molt/healthcheck had run on that host that day); 2026-09-06 only if a report ran before the fill.
- Hurt: nothing. One risk: the "repeated stem" rule is a heuristic; `glossary-0882-*` shows mkdtemp suffixes (8 chars), `tmp*` shows 109 entries at 2.5M total (noise). Rank by bytes, not count, or the signal drowns (109 `tmp*` vs 371M glossary).
- Changed nothing: the Bash-dead mode of 2026-09-06 (Write into the scratchpad failed with EDQUOT per the zotero memory note); the next fill.
- Price looks fair; the actual benefit is unmeasured on doudou, where all documented outages occurred. Recommend running it once on doudou before choosing (the architect agrees).

## Option 2 (worktree `.tmp/` removed only with its worktree, plus Option 1)
- Probe: the architect's git 2.43.0 result is consistent with my R1 expectation; I did not rerun it, but the transcript shows a positive control (untracked file visible) alongside the null, which is adequate.
- Would have helped: t2093/t2094 if they ran in worktrees (unverified; the traces show subagent use in the climate-finance-het project session 33d7deec, no worktree path checked) at the removal of the worktree: 11.4G. Also `tmp-t1045`/`tmp-t2061` in ~/.cache (641M): the stem says ticket, but those are already outside /tmp and survive; Option 2 would relocate them into the owned tree.
- Hurt: (a) crashed-but-unmerged trees keep `.tmp/` forever (accepted residual); the harness count of stale worktrees is the only relief; (b) review worktrees and subagents in separate trees cannot read an author's `.tmp/` (inferred from 0300 design); (c) nothing prevents a 2G audit JSON written to `.tmp/` anyway; the roar size line only helps if the agent reads it, and the 2026-09-28 stale-lock case shows evidence-only-in-worktree already bit once; (d) 85 `glossary` style leaks and the zoteus leak are unchanged.
- Changed nothing: the documented outages (project tests), pi-bash logs (2.3M).
- Net: Option 2's benefit is evidenced for padme's task directories only; for doudou, where the outages are, it is unevidenced. Option 1 is the cheap measurement that decides.

## Remaining objections
1. Report must separate tool caches (huggingface 28G, uv 8.8G) from task temps, else it is noise.
2. No decision on whether roar's size line must block or merely inform; a non-blocking line recreates silent loss (my inference).
3. Doudou unreachable now, so the key datum is outstanding.
