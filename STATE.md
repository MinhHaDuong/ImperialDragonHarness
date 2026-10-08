# Imperial Dragon Harness — State

Last updated: 2026-10-08T09:59Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-08T09:59Z · as of d0cfff3b -->

**Tickets:** 3 ready · 13 blocked — `erg ready tickets/` for full list
  next: 0974 Tracker: portable model capability and effort p… · 1045 Local merge gate replaces the forge's required …
**In flight:** 1 open PR, oldest #1250 0d · CI main: in progress
**Recent (first-parent):**
  d0cfff3b Merge pull request #1256 from MinhHaDuong/roar/tournament-publication-20261008
  ed159f1f Merge pull request #1251 from MinhHaDuong/tickets/arena-roles-deferred
  a6df0c4f Merge pull request #1252 from MinhHaDuong/docs/tournament-relabel

## Ready work

The remaining attribution task is 1004's separate original-criteria integration review. Its historical notes stay intact. Runtime policy 0974 and memory migration 0913 remain separate work. The model tournament cycle 2 is CLOSED (142/160 legs, 426 seats, multidimensional analysis done): skills/route + skills/arena are on main, the routing verdict is recorded in tracker 1024, and eleven follow-up tickets (1046-1058) carry the rest — report, cycle 3, HW-v2, live routing application. The original 1032 and 1009 criteria are checked in the dated coverage correction; no new criterion was added.

## Resume point
2026-10-08: tournament reports final (FR+EN, 12 pages; Mistral series relabelled "last success"/"all attempts"; Haiku 5.5 arm integrated, #1252/#1253), blog post NOT published (1047 awaits the author's go); 1061 (role-split arena redesign) filed deferred; 0974 deferral landed (#1257). Housekeeping 2026-10-08: 15 dead worktrees GC'd; raid-attribution-union holds a superseded staged snapshot (author decides).
The reference clone is `~/.agents`; helpers must resolve any checkout path portably. Portable installation (0999) is complete — integration review closed in #1104; `./bin/idh install`/`check`/`sync` are the registration surface.
Memory v8 is delivered end to end: convention/inventory (#1102), pilot (#1109), capture 0988, dreaming 0910/0916, and acceptance trials 0918 — historical verdict **No global rollout** (docs/memory-v8/evaluation-results.md); 1019/1022 subsequently lifted the acceptance blockers and 0913 now holds ready per-project migration work. The dated October 2 blocked planning note is historical; no rollout is dispatched here.
The Zotero train is COMPLETE (2026-10-03/04): 1018 consolidated into one `zotero` skill with verbs (waves A #1178 + B #1179, author force-approve on a full review round), the `~/.idh` rider landed as 1025 (#1177), and the gaze un-reviewable breaker now counts content-bearing files (1026, #1180 — pure renames no longer fire it). The 0485 byte-for-byte report reproduction remains author-side; the vendored URL-intake copy in livre-milliards-climat (already drifted) and the now-dangling installed symlink are recorded in 1018.
The external-reviewer panel train is closed (0902 #1155; 0205 retired at #1157; teardown in the attribution train 1004→1009). The verification loop is ALSO closed: 1016/1017/1021/0879/0990 all merged 2026-10-03 (WAVE_BASE wave annotations, detached-seat substitution, spawn-trust preflight, erg log placement + reroll_bump routing, orchestrator-run gaze + battery NOT-RUN signal). Agent profiles landed under 0938 (2026-10-03): five shells + contracts (agents channel 761/800), all inventory-justified call sites converted, Pi portability demonstrated live; design note with two external strong reviews merged via #1171.

## Next actions
See [ROADMAP.md](ROADMAP.md) for the trains. Verification, raid annotations, agent profiles (0938), Zotero and reviewer teardown implementation are done. Remaining: separate attribution integration 1004, runtime policy 0974, memory 0913 per-project migration. The model tournament is closed for cycle 2 — its follow-ups are ticketed (1046-1058: PDF report, blog, cycle 3, HW-v2 window, 262K rerun, scouting, live routing, drive2 v2, task-level routing, decorrelation axes, judge sensitivity). Claude adapter 0887 is active: the plugin is the single hook source; PR1211 merged the registration fix and its typed runtime-masked attribution is preserved. Portable Gaze simplification 1027 integrated in PR1189. Open 0974 owns the routing and quota question; retired 0980 is historical, and tournament evidence does not choose a subscription or provider.
This raid uses owned isolated worktrees and preserves unrelated primary-checkout changes.

## Author actions
- Review `docs/tournament-graphs/diffusion-draft.md`, decide the blog destination, then give the go for ticket 1047; review dream PR #1250.
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the client (right-click → Merge n Items), via the report regenerated by `python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html` (0485 closed; author-side chore).
- Zotero train residue: run `idh check` to clean the now-dangling installed skill symlink (retired name, path in ticket 1018); decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
