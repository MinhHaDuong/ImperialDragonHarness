# Acquisition code and replay evidence

At inventory, inspect the supplied package for acquisition producers: scrapers,
API clients, remote download commands, and wrappers or configuration that invoke
them. Record each located producer's code path/version and source anchor, its
role in the raw-to-analysis chain, source service or dataset, inputs and query
parameters, requested time window, and expected outputs. Record an uninspected
producer or inaccessible script as unknown; inability to inspect is not proof
of absent acquisition code. Keep credentials out of evidence and reports;
reference authentication requirements without copying secrets or signed URLs.

Use the existing README/coverage map to retain this evidence; no manifest or
assessment schema changes follow. Distinguish the team's `fetch.sh` for an
archived package or supplied local bytes from the authors' original data
collection. Successful archive ingestion alone establishes no replay of a
scraper or upstream API pipeline. Preserve the existing source/exposure boundary,
private-byte provenance, checksums, and licence/redistribution requirements.

## State what actually ran

For each acquisition producer, report one of: not replayed, attempted but
failed/blocked, replayed with observed outputs, or replay status unavailable.
These are prose evidence descriptions, not new canonical CSV statuses. Cite
actual command/version, execution date, source/query/time-window identifiers,
log and output/hash evidence where available, and coverage limitations.
Use only approved, nonsecret evidence; unavailable historical details stay
unavailable. A code file or README execution claim alone is not observed replay.

Separate executing the acquisition step from verifying its output. A successful
process exit without inspected output proves neither complete acquisition nor
equality with the historical data. State whether the expected scope was fetched,
whether bytes or relevant data content match the original archived input,
which checks were made, and which remain unavailable. Retain partial outputs,
failures, access restrictions, and missing periods. A changed upstream service
or data vintage can explain a proposed investigation but is not a diagnosed
cause without evidence. Preserve original files and first-run outcomes.

Carry the producer inventory and actual replay evidence into each cumulative
report, including not-replayed reasons and affected claims/coverage. Using
archived analysis inputs can permit a scoped analysis run while acquisition
remains unexecuted; state both facts. Derive canonical provision and execution
categories only under `assessment.md`; this evidence adds no score condition,
automatic failure, or success claim.

## Temporal extensions and authority

Acquiring a later period to test the same hypothesis is a proposed direct
replication with new data. Keep it separate from same-data Robustness
Reproduction and from replay of the original historical query. Name the
proposed population/period, changed source/query or data vintage, target and
comparability assumptions, code changes, resource/time or monetary cost
estimates and their basis (or unavailable), API quotas, access and terms-of-use
limits, and a bounded stopping rule. Keep it proposed and not run pending
valid approval of the exact plan under `probe-approval.md` and applicable
outward/access/spending permissions. Approval of same-data checks alone does
not cover a later-period acquisition or grant contact/publication authority.

This reference authorizes no new collection, network contact, paid API use,
or scientific execution. Ordinary authorized acquisition/verification of the
assigned package under inventory's existing `fetch.sh` contract remains governed
there. Inspecting acquisition code does not execute it. Record an unauthorized
or infeasible replay/extension as not run with reasons, without inventing
missing inputs or claiming an acquisition obligation fulfilled.
