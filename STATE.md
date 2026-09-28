# Imperial Dragon Harness — State

Last updated: 2026-09-28T09:03Z

## North star
A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-28T09:03Z · as of feff02e5 -->

**Tickets:** 19 ready · 19 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  feff02e5 Merge pull request #1044 from MinhHaDuong/personal-data-tracked-only-20260928
  e5bca18a Merge pull request #1043 from MinhHaDuong/tickets/0810-unblock
  024d57ae Merge pull request #1042 from MinhHaDuong/tickets/0809-guard-adapters

## Resume point
**2026-09-28.** The portability epic (0800) is closed: 0803 (path/config seam, #1040), 0809 (dirty-reset guard through three runtimes, #1042) and 0810 (gate: inventory validation, deployment suite, runbook, go/no-go, this PR). Decision recorded: stop broader abstraction — thin adapters, `bin/idh` + `adapters/install-wirings.sh` the only shared tooling, Vibe probed (2.25.8) as the next manual slice when scheduled. Earlier today: 0977 essai closed (#1031, Pi backends measured), Albert activated (gpt-oss-120b passes tool calls), 0978 filed (~/.idh relocation), 0979 filed (Pi silent reroute).

Owed to the author, outside any diff:
- **Codex hook trust**: open codex, /hooks, trust the dirty-reset guard once — until then Codex runs without the guard.
- **ILaaS key**: cle consortium -> ~/.config/keys/ilaas.env, then models.json (0977 report).
- **Rotate** the six bash -x values and the Albert key (deferred to October 2026).

## Blockers
(none)

## Next actions
- **Memory v7** (tracker 0909): foundations 0911, 0917 unblocked, nothing started. Standing red row: disjoint roots need the repo out of `~/.claude` — now ticketed as **0978** (child of 0909); re-read 0920/0923 before picking them up.
- **Portable model policy** (tracker 0974): Phase 0 is 0975.
- **Open defects worth a slot**: 0875 (hermeticity guard blind to script-path spawns), 0879 (gate writes malformed log lines), 0955 (credential-shaped names), 0979 (Pi silent reroute to openrouter).
- **Watch**: re-open 0062 (Firecracker) when agents run against secret-bearing projects; lift the merge-review gate into the harness when a second consumer project grows one (0900).

## Backlog
- Merge REALF guidelines and business rules
