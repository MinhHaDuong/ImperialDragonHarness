# Imperial Dragon Harness — State

Last updated: 2026-06-05T10:01Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-06-05T10:01Z -->

**Tickets:** 6 ready · 11 blocked — `erg ready tickets/` for full list
**Recent commits:**
  14ab396 Merge pull request #293 from MinhHaDuong/t-normalizer-leak
  2f23ba1 ticket(0218): harden /reviewers harvest normalizer — drop template-echo, dedupe
  cf98c82 Merge pull request #292 from MinhHaDuong/t0208-reviewers-ci
  e1f97ec skill(0208): /reviewers panel management wired to the 0217 seat-runner
  d48d4f6 Merge pull request #273 from MinhHaDuong/chore-close-0167

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **Harden 0217 seat-runner**: network isolation (drop `--network=host`), `fs/read` path-allowlist, credential denyRead, BASH_ENV-stripped minimal env — unblocks 0207/0208
- **0218**: drop template-echo + dedupe in the /reviewers harvest normalizer
- **0216**: convert verify phases 2-4/6 to Agent() sub-agents (orthogonal, Claude-native)
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Delete the disabled cloud raid routine (claude.ai/code/routines — API has no delete)

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
