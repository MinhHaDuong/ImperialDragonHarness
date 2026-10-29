# Imperial Dragon Harness — Roadmap

This roadmap is forward looking, strategic level only. [STATE.md](STATE.md) holds the current tactical handoff, `tickets/` the acceptance criteria and implementation decisions.

## North star

A reusable, science-backed personal harness for AI-assisted research across
projects, machines and runtimes.

## Current priorities

The three workstreams listed here on 2026-10-19 (1045 local merge gate, 1100
review orchestration, 1099 bounded review) are closed. No open workstream is
named. Use `erg ready tickets/` and `erg ls tickets/` for the live queue.

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
  [installation strategy](conception/idh-install-strategy.md).
- **Runtime portability:** extend measured support rather than presume parity.
  Current evidence is in [pilot-support.json](adapters/pilot-support.json)
  and the [operations runbook](conception/adapter-operations.md).
- **Review and code:** as agents and runtimes get smarter at doing general work,
  we can remove the non-specialized harness parts.
