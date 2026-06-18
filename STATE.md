# Imperial Dragon Harness — State

Last updated: 2026-06-18T09:32Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-06-18T09:32Z -->

**Tickets:** 14 ready · 2 blocked — `erg ready tickets/` for full list
**Recent commits:**
  fdb6cf9 Merge pull request #409 from MinhHaDuong/rule-uv-cache-venv-fs
  6dc56da rules(python): require uv cache and project env on one filesystem
  269565e Merge pull request #407 from MinhHaDuong/dream-consolidate-2026-06-16
  18a367a dream: consolidate -home-haduong-CNRS-papiers-actif-AEDIST-technical-report memory (69→69)
  e2ca7c0 Merge pull request #406 from MinhHaDuong/harness-release-codedata-doi-check

## Blockers

(none)

## Next actions

- **0216 fan-out evidence**: the next substantive PR /gaze completes 0216's criterion-2 proof (PR #334's gaze hit agents=0 on a trivial diff) — no action, just observe and append to the closed ticket
- **dream/beat-on-stale-checkout guard gap** (NEW, found 2026-06-08): the 0234 main-commit guard is inert on a primary checkout that never pulled it — a dream session committed git-erg memory straight to local main and diverged (rescued via PR #357). Fix: dream/beat pre-flight should sync (or refuse on a diverged) primary checkout before committing. Needs a ticket.
- **Verify-reviewer-panel cluster** (only open work left): 0206 (Copilot seat — needs forge config + ≥5-MR trial), 0217/0207 (OS-sandboxed agnostic seats), 0205 (panel contract + decorrelation evidence). 0227/0231/0232/0233/0234 closed this session; cadens now canonical (cadens PR #45)
- **AEDIST maw-audit run**: unblocked (0226), author-deferred — launch from a session rooted in `~/aedist-technical-report`, no args, ~3-5M tokens; resolve untracked `census_bars.csv` first
- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Delete the disabled cloud raid routine (claude.ai/code/routines — API has no delete)

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
