# Imperial Dragon Harness — State

Last updated: 2026-06-08T13:36Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-06-08T13:36Z -->

**Tickets:** 2 ready · 2 blocked — `erg ready tickets/` for full list
**Recent commits:**
  d582878 Merge pull request #357 from MinhHaDuong/rescue/dream-git-erg-memory-20260608
  2c941df dream(git-erg): commit leftover MEMORY.md index update
  df92753 dream: consolidate -home-haduong-git-erg memory (47→47)
  b94dd7c Merge pull request #356 from MinhHaDuong/memory/cross-repo-ticket-placement
  f58a805 memory(feedback): cross-repo tickets live at the destination repo

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
