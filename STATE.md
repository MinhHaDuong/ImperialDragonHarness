# Imperial Dragon Harness — State

Last updated: 2026-07-13T10:43Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-07-13T10:43Z · as of 60177f1 -->

**Tickets:** 17 ready · 2 blocked — `erg ready tickets/` for full list
  next: 0206 Copilot review in the verify panel — on-demand … · 0217 Sandbox-runner reviewer-seat spinoff — OS-conta…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  60177f1 Merge pull request #535 from MinhHaDuong/roar-checkpoint-wrapup
  ca3944c Merge pull request #524 from MinhHaDuong/t0304-state-enrichment
  d5849e0 Merge pull request #522 from MinhHaDuong/t0268-state-guard

## Blockers

(none)

## Next actions

- **0216 fan-out evidence**: criterion-2 proof accumulated 2026-07-11 — five substantive /gaze runs (#482 #483 #485 #487 #491) fanned out full reviewer batteries; append to the closed ticket, then drop this line
- **Verify-reviewer-panel cluster** (only open work left): 0206 (Copilot seat — needs forge config + ≥5-MR trial), 0217/0207 (OS-sandboxed agnostic seats), 0205 (panel contract + decorrelation evidence). 0227/0231/0232/0233/0234 closed this session; cadens now canonical (cadens PR #45)
- **AEDIST maw-audit run**: unblocked (0226), author-deferred — launch from a session rooted in `~/CNRS/papiers/actif/AEDIST-technical-report`, no args, ~3-5M tokens; resolve untracked `census_bars.csv` first
- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
