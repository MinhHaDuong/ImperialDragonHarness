# Imperial Dragon Harness — State

Last updated: 2026-09-24T15:37Z

## North star
A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-24T15:37Z · as of ace2a5dd -->
**Tickets:** 25 ready · 22 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  ace2a5dd Merge pull request #1014 from MinhHaDuong/housekeeping-20260924
  b969cb28 Merge pull request #1002 from MinhHaDuong/design/portable-model-capability-policy
  a09093c6 Merge pull request #1013 from MinhHaDuong/roar-step9-path-entry

## Resume point
**2026-09-24.** Directive-coherence train closed (0956–0971, `docs/2026-09-24-rules-coherence-audit.md`); resident rules halved (#1010). In flight: **0976**, the guard cut from a strict transcript audit — keeps only `reset --hard` on a dirty tree, the pre-commit hook and the CI ticket-collision check; it makes 0877 moot.

Owed to the author, outside any diff:
- **Re-align live `settings.json`** to `settings.shared.json` after 0976 merges; it still wires a deleted script (0886 is the reconciler).
- **Rotate** the six values a plain `bash -x` exposed (`~/.codex/auth.json` holds its own OpenAI key).
- **Decide** the fate of `scripts/projects.json` (orphaned by 0941).

## Blockers
(none)

## Next actions
- **Memory v7** (tracker 0909): foundations 0911, 0917 unblocked, nothing started. Standing red row: disjoint roots need the repo out of `~/.claude` (author ruling, #944); re-read 0920/0923 before picking them up.
- **Portable model policy** (tracker 0974): Phase 0 is 0975.
- **Open defects worth a slot**: 0875 (hermeticity guard blind to script-path spawns), 0879 (gate writes malformed log lines), 0955 (credential-shaped names).
- **Watch**: re-open 0062 (Firecracker) when agents run against secret-bearing projects; lift the merge-review gate into the harness when a second consumer project grows one (0900).

## Backlog
- Merge REALF guidelines and business rules
