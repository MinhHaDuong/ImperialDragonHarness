# Native Claude memory stores of v8 projects pruned on padme and doudou (ticket 1481)

Date: 2026-11-09, raid 829e9e. Prune of `~/.claude/projects/<key>/memory/`
on both hosts, for the projects whose v8 `memory/` disposes of the notes.

Invariant, per note, both tests before deletion: (a) the live file's
`git hash-object` is a blob reachable from `origin`'s default branch of the
harness or of the project (`git rev-list --objects`, spot-checked against
`git log --find-object`); (b) the project's `memory/SOURCES.md`, its topics'
Sources, a smelt report or its import directory names the note with a
disposition (AEDIST tombstones: a `# DELETED`/`# PROMOTED` header, the class
SOURCES.md disposes of; climate-finance-het: byte match in
`memory/imports/claude-code-native/`). Audience-excluded notes were kept
whatever the tests said. Positive control: fuzzy-corpus classified as
15 delete + `MEMORY.md` on both hosts before anything was deleted. Each
deletion re-checked the file's hash against the classified blob: 0 mismatches.

| Project | Host | Before | Deleted | Kept notes | Kept, why |
|---|---|---|---|---|---|
| AEDIST-technical-report | padme | 197 + index | 192 | 5 | audience-excluded: `feedback_autonomous_raid_doudou_pickup`, `feedback_no_ps_ef_in_claude`, `feedback_no_typo_callouts`, `reference_api_keys_location`, `user_platform` |
| AEDIST-technical-report | doudou | 198 + index | 193 | 5 | same five (doudou's extra note, the withdrawn `feedback_durable_reminder_is_blocked_open_ticket`, deleted) |
| chemin-de-voix | padme | 59 + index | 58 | 1 | personal data: `user_bio` |
| chemin-de-voix | doudou | 59 + index | 58 | 1 | same |
| fuzzy-corpus | padme | 15 + index | 15 | 0 | — |
| fuzzy-corpus | doudou | 15 + index | 15 | 0 | — |
| padme | doudou | 15 + index | 13 | 2 | blob in no repository: `project-cold-hdd-plaintext`, `project_server_management` (a newer version than the one padme's topics cite) |
| climate-finance-het | doudou | 309 + index | 75 | 234 | 230 not in the import directory; 4 with no reachable blob: `feedback_fulltext_channels_authorized`, `project_v3_ship_posture`, `reference_doudou_disk_layout`, `reference_fulltext_md_zotero_sync` |
| climate-finance-het | padme | 10 + index | 0 | 10 | **skipped**: live Claude sessions in the project (pids 1648775, 1985893); classification gave 8 delete, 2 no-blob (`feedback_dont_trade_hours_for_dollars`, `project_rel_parallel_launch_2026_11_04`) |

Totals: padme 265 deleted, doudou 354 deleted.

Indexes: each rewritten `MEMORY.md` opens its key insights with a pointer to
the repository's `memory/MEMORY.md` and this ticket, keeps the lines of
kept notes, drops lines of deleted notes, and keeps each free line unless the
project's `memory/` carries it or SOURCES.md disposes of it by name.
Kept free lines: AEDIST 4 (project description with the monorepo history,
workstation hardware and API-key location, which SOURCES.md leaves out for
audience, and the Linux-only preference of the kept `user_platform`);
padme on doudou all 7 (padme's own index kept its key insights in the
2026-11-07 model; doudou's deployment line predates the author's correction
there); climate-finance-het on doudou all 6. Dropped: AEDIST 9 (10 on
doudou), chemin-de-voix 6 (4 in its topics, 2 disposed by SOURCES.md),
fuzzy-corpus none present.

Left alone, state recorded: JETP-observer (files with index: padme 7, doudou 6; live writer,
no repository copy), git-erg (padme 67, doudou 66 files; its SOURCES.md says not
migrated, author triages through smelt), sen-causal-reading (padme 0;
doudou 14 notes and an index never seen by its smelt, no note with a reachable blob),
padme's own store on padme (2 files after the 2026-11-07 triage; the newer
`one-line-root-commands` has no blob). Seen and not touched: superseded keys
`-home-haduong-Climate-finance--superseded-20260913` (88),
`-home-haduong-Oeconomia-Climate-finance--superseded-20260913` (43),
`-home-haduong-CNRS-projets-actifs-jetp` (8), `-home-haduong-CNRS-papiers-actif-JETP-at-two` (7),
and `-home-haduong-CNRS-papiers-actif-Gavard-Scotch-2026-Climate-finance-counterproductive`
(6 per host, no v8 adoption), the harness's own `-home-haduong--agents` and
`-home-haduong--claude`.

Codex and Pi: no `~/.codex/memories` on either host; on doudou the Pi
hits for these project names are session transcripts, not memory stores
(padme: each SOURCES.md records the same).

Live-session preflight: Claude process cwds read on padme from `/proc` and
on doudou over ssh, before classification and again before each host's
deletions. A shell under an AEDIST worktree on padme belonged to a session
whose cwd is `~/CNRS` (key `-home-haduong-CNRS`), so it was not an AEDIST
session; no skip.

Backup caveat: no durable backup was kept (as for padme on 2026-11-07); the
run's scratch tarballs died with its worktree. Every deleted note's blob is
reachable from the harness's public history (the `projects/` exports) or the
project's own; a history scrub of `projects/` in the harness would void that
backup for the notes whose only copy is there.

Records in the projects (one ticket-only merge request each, left open for
the author): AEDIST-technical-report, chemin-de-voix, fuzzy-corpus, padme
(each asks its next session to add the prune paragraph to SOURCES.md, as padme
did), climate-finance-het (the doudou remnant of 230 unconsolidated notes and
the padme store skipped this run), sen-causal-reading (doudou's 14
unconsolidated notes). Review at each project's next smelt or by 2026-11-23:
count the notes in each pruned store; regrowth reopens R4 of
`design/2026-10-29-memory-system-audit.md`.

Merge requests filed (ticket-only, open): AEDIST-technical-report
https://github.com/MinhHaDuong/aedist-technical-report/pull/1198 (ticket 0690),
chemin-de-voix https://github.com/MinhHaDuong/Tracing-Kieu/pull/185 (0262),
fuzzy-corpus https://github.com/MinhHaDuong/fuzzy-corpus/pull/74 (0056),
padme https://github.com/MinhHaDuong/padme/pull/258 (0112),
climate-finance-het https://github.com/MinhHaDuong/climate-finance-het/pull/2050 (2831),
sen-causal-reading https://github.com/MinhHaDuong/sen-causal-reading/pull/171 (0113).
AEDIST's `erg new` warned that its next-id branch scan timed out: a claim
conflict on `tickets/.claims/0690` at merge means renumber.
