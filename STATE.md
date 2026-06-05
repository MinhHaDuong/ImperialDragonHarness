# Imperial Dragon Harness — State

Last updated: 2026-06-05T19:21Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-06-05T19:21Z -->

**Tickets:** 5 ready · 3 blocked — `erg ready tickets/` for full list
**Recent commits:**
  7a7d544 Merge pull request #312 from MinhHaDuong/chore-memory-workflow
  9aaebfd memory: Workflow agents are session-bound — isolation opt-in, repo binding structural
  9c1db30 Merge pull request #311 from MinhHaDuong/t-dream-debt
  a9b0597 ticket(0224): file Dream v2 debt — decay-confirmation loop + provenance race
  7b2a95c Merge pull request #309 from MinhHaDuong/fang-audit-process-fix

## Blockers

(none)

## Next actions

- **Balance debt**: 2026-06-05 was all tooling — next raid must advance a deliverable (STATE milestone work or a project repo)
- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207
- **0216**: convert verify phases 2-4/6 to Agent() sub-agents (orthogonal, Claude-native); lands before 0206's verify/SKILL.md edits
- **0219**: pick the second-language validation target (AEDIST Python suite is the candidate) before raiding
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Delete the disabled cloud raid routine (claude.ai/code/routines — API has no delete)

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
