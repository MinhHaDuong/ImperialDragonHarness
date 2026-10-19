# Imperial Dragon Harness — Roadmap

This roadmap is forward looking, strategic level only. [STATE.md](STATE.md) holds the current tactical handoff, `tickets/` the acceptance criteria and implementation decisions.

## North star

A reusable, science-backed personal harness for AI-assisted research across
projects, machines and runtimes.

## Current priorities

| Workstream | Next step | Completion evidence |
|---|---|---|
| Local merge gate — 1045 | Settle the open trust and execution decisions, then implement the local gate | Revision-bound check records, enforced merge checks and a forge-outage rehearsal; full criteria in the ticket |
| Review orchestration — 1100 | File the planned children before implementation; move review planning into Hunt and consolidate review entry through Gaze | Reuse of valid review evidence, rejection of stale proof, updated callers and integration review |
| Bounded review — 1099 | After 1100, bound every review phase | Review phases end within their declared budgets; full criteria in the ticket |

These are the three open tickets as of 2026-10-19. Use `erg ready tickets/`
and `erg ls tickets/` for the live queue.

## Next: testing subsystem

After review orchestration, bounded review and the local CI gate, rework test
selection to run only the tests required by a change. Investigate AST-based
dependency analysis alongside the existing scoped checks; measure saved
runtime and missed regressions against the full suite before adopting it.
Keep conservative fallback coverage where dependencies cannot be resolved.

Design this together with review on an integration branch: establish which
revision and combined changes each test run and review cover, when evidence
can be reused, and which interactions require fresh validation before merging
to main. Test selection and review must assess the integrated result.

This is the next design workstream, not yet an implementation ticket.

## Moving targets

- **Portable installation:** registration and integration are delivered.
  Native packaging and opt-in host setup remain future design work. See the
  [installation strategy](docs/idh-install-strategy.md).
- **Runtime portability:** extend measured support rather than presume parity.
  Current evidence is in [pilot-support.json](adapters/pilot-support.json)
  and the [operations runbook](docs/adapter-operations.md).
- **Review and code:** as agents and runtimes get smarter at doing general work,
  we can remove the non-specialized harness parts.
