# Imperial Dragon Harness — State

Last updated: 2026-09-28T17:13Z

## North star
A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-28T17:13Z · as of 0bcbb35d -->

**Tickets:** 19 ready · 19 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  0bcbb35d skills: trim resident descriptions to restore budget
  9fc31285 state: record relocation pause and resident-budget failure
  267ab6bb Merge pull request #1049 from MinhHaDuong/memory-privacy-session-20260928

## Resume point
**2026-09-28.** The author deferred migration 0978 today. Disposable-home probes: Claude follows per-entry links for instructions, rules, settings, hooks, plugins, skills and commands; native memory remains unproved, and broken links silently drop instructions and hooks. A fixture rollback restored bytes and links after 23 crash points and partial writes. Read-only split census: `projects/` holds 1,271 tracked memory files (1.8 MiB) and 17,409 native runtime files (5.15 GiB); `skills/` also mixes three private links and `synced/` with tracked skills. No live data moved. The portability epic 0800 is closed; thin adapters remain the chosen scope. `make check`: 1,114 passed after the resident skills budget fix (0981).

Owed to the author, outside any diff:
- **ILaaS key**: cle consortium -> ~/.config/keys/ilaas.env, then models.json (0977 report).
- **Rotate** the six bash -x values and the Albert key (deferred to October 2026).

## Blockers
- **0978:** memory control and visible broken-link check remain open; wait for the other Codex sessions to exit before preparing the live data split.

## Next actions
- **Memory v7** (tracker 0909): foundations 0911, 0917 are ready. Prepare the 0978 native/canonical split and startup validator after the quiet window; schedule the actual move another day. Re-read 0920/0923 before starting them.
- **Portable model policy** (tracker 0974): Phase 0 is 0975.
- **Open defects worth a slot**: 0875 (hermeticity guard blind to script-path spawns), 0879 (gate writes malformed log lines), 0979 (Pi silent reroute to openrouter).
- **Watch**: re-open 0062 (Firecracker) when agents run against secret-bearing projects; lift the merge-review gate into the harness when a second consumer project grows one (0900).

## Backlog
- Merge REALF guidelines and business rules
