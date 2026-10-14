# R1 evidence assessment of the architect's options (scientist seat)

Counts and paths: r1-evidence-census.md.

## Architect claims tested
1. "11G, about 70%, in two ticket-named dirs." Agree: t2093 5.5G, t2094 6.1G; all `t[0-9]*` (135 entries) 11.9G, 74% of 16G (derived). Missing fact: padme rebooted 2026-10-11 21:07, so this is 3 days of accumulation (about 5G/day, derived). Episodic, driven by two audit tasks.
2. "t2093/t2094 belong to a project repo." Agree: traces tie them to climate-finance-het (plus this panel).
3. "Runtime scratch about 1.5%." Agree (248M).
4. "pytest rotates itself, 179M." Measured 173M. Agree, but the architect omits `glossary-0882-*`: 85 dirs, 371M on padme and many at about 26M on doudou; mkdtemp-style per-test leaks that pytest rotation does not cover (project test, inferred).
5. "pi-bash logs show non-Claude runtimes write bare /tmp." Confirmed but tiny (4 files, 2.3M). A pattern, not a size driver.
6. "JETP-observer STATE line 31 is a project-test leak already fixed locally." Line 31 confirmed verbatim (file is ~/CNRS/projets/actifs/JETP-observer/STATE.md). "Fixed" is overstated: it is a mitigation instruction (set TMPDIR), and I did not find the leaker. The named 2026-09-06 leaker was the upstream vitest suite in the zotero repo (zoteus-*), a different project.
7. "A reboot is crash recovery." True (both hosts tmpfs), but the 2026-09-06 outage ended in a reboot: the recovery is the outage, and it also wipes evidence someone may want.
8. "Leak is agent behaviour, not harness code." Mostly supported (harness-owned: claude-1000 1.5%). Not fully: raids create caches (doudou idh-1080-uv-cache 235M; padme arena-uv-cache 275M), by env variables rather than literal `/tmp` strings, which the architect's skill grep for "/tmp" would miss.
9. "Moving to disk removes Disk full." Counter: /home is 92% used with 85G free, versus 17G free on /tmp. Moving 11.9G of evidence is a transfer to a filesystem that also hosts git, traces and DVC, where a fill is worse. The dir-level count is not a reduction of risk.

## Option A (in-worktree .tmp/)
- Helped: t2093/t2094 if run inside worktrees (names suggest so; unverified), the roar/worktree-gc purge would have freed 11.4G. Also the 09-16 task dirs (`rev461*`, `t07*`).
- Hurt: (a) the t2093 audit JSONs (2.1G, 1.6G single files) are the deliverable evidence; a purge at roar or GC removes them unless committed, and the 2026-09-28 stale-lock near-miss shows evidence held only in worktrees is already fragile; (b) separate review worktrees (gaze `review-N`, 0300) and subagents cannot read the author's `.tmp/`, whereas /tmp paths are shared (inferred); (c) disk pressure on a 92% /home; (d) GB-size files inside a tree slow status/rg scans (inferred, not measured).
- No change: the 2026-09-06 zoteus-* leak (vitest uses os tmpdir; the rule binds only if TMPDIR is set per command), `glossary-0882-*`, pytest basetemps, env-set caches.

## Option B (registered task root on the tmp base)
- Helped: t2093/t2094 (owner = worktree/branch gives an age-free test), idh-1080-uv-cache and arena-* caches (harness-owned). Keeps RAM speed for numba caches (1.9G).
- Hurt: other-host liveness is invisible, and doudou is where the outages were; an age rail would return, which the constraint forbids. Bytes stay on tmpfs and count toward the 80% quota. A fourth mechanism.
- No change: zoteus-*, glossary-*, and anything that ignores the helper.

## Option C (rule plus report-only)
- Helped: a top-N by size/owner/mtime would have named t2093/t2094 the day they grew (12 Oct), cheaply. 0854's item 12 already reports Claude's root; the post-0854 record shows 0 real EDQUOT events on padme (weak, doudou unscanned).
- Hurt: only the author's recurring minutes.
- No change: when Bash is already dead (2026-09-06 mode) no report can run; and it does not stop the next fill.

## Gaps no option closes
- Ownership today is a naming convention (`tNNNN-*`, 135 dirs). A usable age-free test is "the owning ticket is closed and its branch merged", which must be readable across repos (t2093 belongs to another repo).
- The documented outages are doudou's quota; the options are evidenced mostly on padme.
- Leaks from project tests (zoteus-*, glossary-0882-*) are the documented outage cause and are untouched by A/B; the prevention lever is per-command TMPDIR (the STATE line 31 idiom) in the project.
- No instance found where an automatic /tmp sweep destroyed wanted data; the risk is inferred from worktree-GC history, so the cost of the safety rails in A/B is unsupported by an incident.
