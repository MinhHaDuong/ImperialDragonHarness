# D3 evidence (scientist seat): investigate-and-report at roar and lair

## Attribution probe (padme, read-only, python3 -I, script in this directory: probe.py / probe2.py)
Universe: 5993 history files, 4668 MB (Claude projects + subagents, Pi, Codex rollouts). Method: file list bounded to mtime >= the candidate's earliest file mtime minus 60 s; exact-bytes search of the full path per line, stop at the first hit per file. The 1095 panel's own files excluded in probe2 (they quote these paths and contaminate the first run; this is a real hazard for the design, see below). Whole-universe scan of all four runtimes took under 4 s for any candidate.

| Candidate | Files scanned | Hit files | Time | Creator found? |
|---|---|---|---|---|
| /tmp/t2093-historical-audit (5.5G) | 839 | 43 | 0.4 s | Yes, but ambiguous: first hits are Claude subagent 33d7deec/agent-a298ece4fbdea3294 line 47 (climate-finance-het) and Codex rollouts 2026-10-12T13:24 (line 2106), 14:54, 14:57. Many sessions cite it; the creating line is the earliest, but "creator" vs "reader" is not decided by the grep (inferred). |
| /tmp/t2094-switch (6.1G) | 784 | 16 | 0.4 s | Same: agent-a298ece4 line 163; Codex 2026-10-12T13:24 line 4884. |
| ~/.cache/tmp-t1045 (356M) | 2603 | 1 | 2.3 s | Yes, unique: Claude session in the t1045 harness worktree, 3f82806b line 426. |
| ~/.cache/tmp-t2061 (285M) | 3105 | 2 | 2.5 s | Yes: JETP-observer subagents ad2bc103 line 35, a5a5325a line 66. |
| /tmp/arena-uv-cache (275M) | 456 | 2 | 0.3 s | Yes: Codex 2026-10-13T21:19 rollout line 118 and 21:21 line 31 (a harness arena run). |
| /tmp/nb1372 (240M) | 30 | 0 | 0.0 s | MISS. Candidate is recent; only 30 files qualified and none non-panel cited the path (inferred: referenced relatively, via env var, or created by a shell variable). |
| /tmp/glossary-0882-035cog0o | 30 | 0 | 0.0 s | MISS by path, as expected: random mkdtemp suffix never appears in a trace. |

Positive controls: (1) the first run found t2093/t2094 in traces I know contain them (this panel's files and agent-a298ece4), and found the known path in the known session; (2) a nonexistent path returned MISSING (not a zero-hit claim). Note a null for nb1372 and glossary is a miss of this method, not proof of no creator.

## Glossary attribution
- Path search fails; stem search works: "glossary-0882" occurs on 15 trace lines, all Codex rollouts (e.g. 2026-10-01T15-49, line 176; session cwd = ~/CNRS/projets/actifs/climate-finance-het, from the rollout header). The line is a source listing: `base = Path(tempfile.mkdtemp(prefix="glossary-0882-"))` under an `@cache` fixture `glossary_site()`, with no cleanup visible. So attribution "test fixture in repo climate-finance-het, ticket 0882" is available from stem plus cwd, not from the directory name (derived/inferred). Cheaper and more reliable than traces: grep the prefix in the repo source.
- Those 85 dirs (371M) arise per test process (`@cache` only per process), consistent with parallel pytest.

## Assessment against episodes
- Helps: t2093/t2094 (11.6G, 74% of padme usage): a lair would have named the Codex/Claude sessions of 2026-10-12 and project climate-finance-het in under 1 s, and shown the creating session as dead or live. `tmp-t1045` (356M, ~/.cache) is attributed uniquely to a harness session. The 2026-09-16 git-erg case (`jetp-*`, `rev461*`, `t07*`) would have produced creators, if the traces are retained.
- Hurts or limits: (a) hits are sets of readers and creators, not creators; the "first hit by mtime" rule could pick a reviewer who only `ls`'d it; (b) a report run inside a panel quotes the candidate paths and so pollutes later scans; exclude the running session; (c) it needs the history to exist on the host: doudou unreachable now, no data (round 2); remote sessions' histories live elsewhere; (d) roar's scope "creating line in this session or its nested agents" is well-defined for Claude (subagents/ dir) but for Codex I did not verify a nesting link: rollouts are flat files per session (inferred).
- Changes nothing: the 2026-09-06 Bash-dead mode (the report cannot run); the leaking stems themselves (still the project's fix).
- Prices: a 4668 MB scan at <4 s per candidate means per-candidate bounded grep is cheap (under a minute for ~15 candidates, derived). The estimate 6-8 h is plausible; the Claude+Codex+Pi readers are the likely 2-3 h.

## Objections
1. "Creator unknown" must not be read as ownerless; nb1372 is a miss.
2. Disposal by the reading session still depends on judging "cited as evidence": the grep also finds the PR/verdict citations only if they are in traces (inferred), so require the guard to also search git log and PR bodies.
3. Doudou, the documented outage site, remains unmeasured.
