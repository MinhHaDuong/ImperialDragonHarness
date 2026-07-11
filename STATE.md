# Imperial Dragon Harness — State

Last updated: 2026-07-11T22:30Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-07-11T22:30Z -->

**Tickets:** 13 ready · 4 blocked — `erg ready tickets/` for full list
**Recent commits:**
  b3378cf ticket(0286): derive setup-claude-agent.sh project list from projects.json
  9477071 Merge pull request #497 from MinhHaDuong/t0284-home-reorg-stale-paths
  666f41e ticket(0284): close and archive — PR #497
  331d24b Merge pull request #496 from MinhHaDuong/t0262-cross-pr-ticket-collision
  49db3cf ticket(0262): close and archive — PR #496

## Blockers

(none)

## Next actions

- **0216 fan-out evidence**: criterion-2 proof accumulated 2026-07-11 — five substantive /gaze runs (#482 #483 #485 #487 #491) fanned out full reviewer batteries; append to the closed ticket, then drop this line
- **2026-07-11 landings**: eager local-main sync everywhere (0276/0277 — closes the 2026-06-08 stale-checkout guard gap; beat delegates to sync-local-main.sh), dream data-quality wave (0241/0263/0270/0275/0278/0279/0282), memory backlog tracked, batch-decisions doctrine in workflow.md
- **Verify-reviewer-panel cluster** (only open work left): 0206 (Copilot seat — needs forge config + ≥5-MR trial), 0217/0207 (OS-sandboxed agnostic seats), 0205 (panel contract + decorrelation evidence). 0227/0231/0232/0233/0234 closed this session; cadens now canonical (cadens PR #45)
- **AEDIST maw-audit run**: unblocked (0226), author-deferred — launch from a session rooted in `~/CNRS/papiers/actif/AEDIST-technical-report`, no args, ~3-5M tokens; resolve untracked `census_bars.csv` first
- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Delete the disabled cloud raid routine (claude.ai/code/routines — API has no delete)

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
