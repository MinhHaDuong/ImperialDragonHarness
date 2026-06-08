# Imperial Dragon Harness — State

Last updated: 2026-06-08T10:15Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-06-08T10:15Z -->

**Tickets:** 7 ready · 2 blocked — `erg ready tickets/` for full list
**Recent commits:**
  a106406 Merge pull request #344 from MinhHaDuong/adopt-aedist-orphan-memory
  b23e847 memory(aedist): adopt orphaned dream output from #336 (make-stamp-discipline)
  d99af53 Merge pull request #343 from MinhHaDuong/feedback/verify-each-before-batch
  c71407a memory(feedback): verify each item before a batch action
  e29db98 Merge pull request #340 from MinhHaDuong/chore/healthcheck-unarchived-probe

## Blockers

(none)

## Next actions

- **0216 fan-out evidence**: the next substantive PR /gaze completes 0216's criterion-2 proof (PR #334's gaze hit agents=0 on a trivial diff) — no action, just observe and append to the closed ticket
- **0227 multi-repo wrapper sweep**: mostly done 2026-06-08 (PRs #60/#794/#783/#19; chemin-de-voix/git-erg/.claude clean; child 0230 closed). Remaining: cadens (deferred), llm-benchmarks, home-dir, aedist -docs/-experiments/-slides
- **AEDIST maw-audit run**: unblocked (0226), author-deferred — launch from a session rooted in `~/aedist-technical-report`, no args, ~3-5M tokens; resolve untracked `census_bars.csv` first
- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Delete the disabled cloud raid routine (claude.ai/code/routines — API has no delete)

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
