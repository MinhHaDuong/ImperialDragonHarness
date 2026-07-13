# Imperial Dragon Harness — State

Last updated: 2026-07-12T18:40Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-07-12T18:40Z -->

**Tickets:** 14 ready · 4 blocked — `erg ready tickets/` for full list
**Recent commits:**
  f5f3a20 Merge pull request #504 from MinhHaDuong/t0288-track-changes-pdf
  42998c5 ticket(0288): close and archive — PR #504
  2997be3 fix(0288): guard track-changes-pdf against ref/main-tex injection
  bfca208 simplify(0288): drop dead DIFF_MARKERS constant and redundant .git check
  192a141 Merge pull request #503 from MinhHaDuong/t0287-ingest-decision-letter

## Blockers

(none)

## Next actions

- **0216 fan-out evidence**: criterion-2 proof accumulated 2026-07-11 — five substantive /gaze runs (#482 #483 #485 #487 #491) fanned out full reviewer batteries; append to the closed ticket, then drop this line
- **2026-07-11 landings**: eager local-main sync everywhere (0276/0277 — closes the 2026-06-08 stale-checkout guard gap; beat delegates to sync-local-main.sh), dream data-quality wave (0241/0263/0270/0275/0278/0279/0282), memory backlog tracked, batch-decisions doctrine in workflow.md
- **Verify-reviewer-panel cluster** (only open work left): 0206 (Copilot seat — needs forge config + ≥5-MR trial), 0217/0207 (OS-sandboxed agnostic seats), 0205 (panel contract + decorrelation evidence). 0227/0231/0232/0233/0234 closed this session; cadens now canonical (cadens PR #45)
- **AEDIST maw-audit run**: unblocked (0226), author-deferred — launch from a session rooted in `~/CNRS/papiers/actif/AEDIST-technical-report`, no args, ~3-5M tokens; resolve untracked `census_bars.csv` first
- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
