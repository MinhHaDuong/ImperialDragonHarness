# Imperial Dragon Harness — State

Last updated: 2026-07-10T15:14Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-07-10T15:14Z · housekeeping sweep -->

**Tickets:** 18 ready · 4 blocked — `erg ready tickets/` for full list
**Recent commits:**
  addacd8 Merge pull request #458 from MinhHaDuong/harness-ruff-shutil-which
  bcf4f51 rules(python): ruff adherence test resolves via shutil.which + pinned dev dep
  146debf Merge pull request #456 from MinhHaDuong/roar-247-memory
  ff30fd8 memory(harness): skill-lifecycle edits need whole-run reasoning
  148052d Merge pull request #455 from MinhHaDuong/rules-propose-roar-after-merge

## Blockers

(none)

## Next actions

- **Quick-win trio (do next, lowest-risk first)**: 0261 (lair step 10 → STATE via PR, not ff-merge to main) · 0258 (roar degrades in no-forge repos) · 0255 (grow prose/_all.md, size-guarded). Each is a self-contained skill/rule edit with a test.
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
