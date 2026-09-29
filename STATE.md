# Imperial Dragon Harness — State

Last updated: 2026-09-29T16:14Z

## North star
A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-29T16:14Z · as of 22126e53 -->

**Tickets:** 22 ready · 20 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  22126e53 Merge pull request #1065 from MinhHaDuong/roar-raid-20260929
  598fa5e9 Merge pull request #1064 from MinhHaDuong/t0989-hermetic-idh-tests
  39f00756 Merge pull request #1063 from MinhHaDuong/stale-records-20260929

## Resume point
**2026-09-29.** The relocation (tracker 0978) is split into controlled-risk steps, and everything before the move itself has landed. 0982 points every consumer at `~/.idh`, a symlink to `~/.claude` on doudou and padme, with no bytes moved. 0983 makes `claude`, `codex` and `pi` refuse to launch, naming the culprit and the repair, when a link they depend on is broken. 0984 settled the memory question on Claude Code 2.1.284: memory loads through a symlinked folder, and a session keys its memory folder by the resolved path, so the cutover renames the folder and re-keys `~/.claude.json` (now a 0986 exit criterion). 0987 made `idh` the one operator command (`install`, `check`, `status`, `sync`), deleting `install-wirings.sh` and the timer installer; the author accepted +216 source lines of safety. Both hosts carry the marked `~/.bashrc` loader block; padme's pull is unblocked and its Codex guard re-trusted and probed live. `make check` is green; 0989 made the idh tests hermetic against the checkout's untracked links. In the primary checkout, two memory-budget tests fail only while other sessions' uncommitted memory sits there (0988).

Owed to the author, outside any diff:
- **ILaaS key**: cle consortium -> ~/.config/keys/ilaas.env, then models.json (0977 report).
- **Rotate** the six bash -x values and the Albert key (deferred to October 2026).

## Blockers
- **0986** (live cutover) needs a quiet window the author schedules: no Claude, Codex or Pi session running, timers paused.

## Next actions
- **Relocation** (tracker 0978): 0985 settled the method. The move is done by hand, following the runbook `docs/idh-cutover-checklist.md`, and rollback means restoring a tar snapshot. The author dropped the scripted cutover as disproportionate for a one-off (2026-09-29). Next is 0986. `idh install` has not yet been run for real on either host (it would add the `~/.local/bin` links and enable the mammoth-audit timer).
- **Harness defects from 2026-09-29**: 0988 (session memory lands uncommitted in the checkout and silently stalls host pulls; doudou's primary checkout holds such files now) and 0990 (raid Phase 6 cannot obtain a `/gaze` verdict from a background agent; see also 0853).
- **Memory v7** (tracker 0909): foundations 0911, 0917 are ready. Re-read 0920/0923 before starting them; their premise changes with 0984's verdict.
- **Portable model policy** (tracker 0974): Phase 0 is 0975.
- **Open defects worth a slot**: 0875 (hermeticity guard blind to script-path spawns), 0879 (gate writes malformed log lines), 0979 (Pi silent reroute to openrouter).
- **Watch**: re-open 0062 (Firecracker) when agents run against secret-bearing projects; lift the merge-review gate into the harness when a second consumer project grows one (0900).

## Backlog
- Merge REALF guidelines and business rules
