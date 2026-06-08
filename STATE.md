# Imperial Dragon Harness — State

Last updated: 2026-06-08T00:00Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-06-08T00:00Z -->

**Tickets:** 7 ready · 2 blocked — `erg ready tickets/` for full list
**Recent commits:**
  c8e8f01 Merge pull request #339 from MinhHaDuong/fix-balance-rule-idh
  138534e raid: balance rule reads deliverable off the north star, not a fixed list
  e548f55 Merge pull request #337 from MinhHaDuong/roar-followups-20260606
  f63e0ff Merge pull request #336 from MinhHaDuong/dream-aedist-v21-leftovers
  6077cf3 roar: file raid follow-ups 0233/0234, save staleness memory

## Blockers

(none)

## Next actions

- **0216 fan-out evidence**: the next substantive PR /gaze completes 0216's criterion-2 proof (PR #334's gaze hit agents=0 on a trivial diff) — no action, just observe and append to the closed ticket
- **0227 multi-repo wrapper sweep**: parent open; one session per repo (chemin-de-voix, git-erg, aedist, Climate-finance, cadens, fuzzy-corpus, llm-benchmarks, home-dir)
- **AEDIST maw-audit run**: unblocked (0226), author-deferred — launch from a session rooted in `~/aedist-technical-report`, no args, ~3-5M tokens; resolve untracked `census_bars.csv` first
- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Delete the disabled cloud raid routine (claude.ai/code/routines — API has no delete)

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
