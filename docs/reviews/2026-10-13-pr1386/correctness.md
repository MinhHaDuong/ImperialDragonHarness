# Correctness perspective — PR 1386

Reviewed SHA: `b731a7287d1448ae57396197c3a9a219bbe9715a` (local HEAD checked before and after). Read actual integration diff against origin/main and ticket 1094. Distinct correctness pass after simplification; no earlier approval substituted for this review.

Route: caller-selected gpt-6.1-sol, medium, OpenAI. Reused seat/context, same-family replication; **no new independent context or model-family independence claimed**. This was a serial recovery perspective requested by the orchestrator; the profile's preference for a parallel seat is not satisfied and remains an integrity limitation for the caller to disclose. Source read-only; exactly this report artifact written, no commits, pushes, fixes or outward mutations.

Findings: none.

Concrete evidence checked:
- Migration manifest (`arena/migration/from-harness-2026-10-13.json:2`) names source commit c98bef7fcf0b2dab7f7b346aa3537022f7f4965b. Recomputed all **96 original SHA-256 hashes** from `git -C <review-tree> show <source>:<path>`; every hash matched. Recomputed current destination hashes; differences match exactly the six adaptation paths listed in `.panel/1386/manifest-verification.json:4–11`. All other transferred manifest files exist and retain original bytes.
- All eight arena ticket files (1048, 1049, 1050, 1051, 1058, 1061, 1087, 1093) compare byte-identically with their origin/main harness versions, retain unresolved criteria, and have no Closed header. All eight original paths are absent from the harness open-ticket directory. The harness wontdo copies preserve entire original bodies and prior journals, adding only transfer disposition: tickets/closed/1048-model-tournament-cycle-3-locals-medium-v.erg:5 and tickets/closed/1087-arena-runner-provider-error-with-empty-o.erg:5. Their close notes explicitly say the work remains open in arena.
- Retained route grid and coverage compare structurally identical with origin/main after removing documentary comments/role notes; numeric, coverage and family data are unchanged. docs/arena-integration.md:9–12 records this ownership and historical-data boundary. tests/test_route_grid.py:5–12 preserves the join contract at the live harness boundary.
- docs/arena-integration.md:18–23 targets the independent existing analysis CLI and explicitly writes the harness grid, with routes.json review in the same pass. Existing arena CLI accepts the documented source/destination flags and writes sibling coverage (scripts/tournament-analysis.py:233–248).
- pyproject.toml:34–37 retains remaining dev dependencies while removing migrated plotting dependencies. Search over retained scripts/tests found no numpy or matplotlib imports. The earlier declared adherence runner independently passed its dependency/ruff checks, with output retained in adherence-lint-host.log; correctness conclusions above use current bytes, not that approval.

Ticket evidence boundary: arena/migration/validation.md:9–19 records standalone tests, FR/EN reproduction, correction archive hashes and full harness checks. This bounded perspective read that record but did not rerun rendering/full suites; PDF equality is correctly limited to extracted text because wall-clock metadata differs. The caller supplied arena main d322b10 as the external revision coordinate; this seat verified destination files directly and did not independently resolve that git coordinate.

Confidence: high for directly checked transfer hashes, ticket preservation, routing invariance and integration CLI shape; recorded validation remains caller/external evidence.

Verdict: approve (correctness perspective only; no PR merge or gate decision).
