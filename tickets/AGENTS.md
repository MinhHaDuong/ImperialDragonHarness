# tickets/

Local file-based tickets store for the project.

Agents should ensure the `erg` binary helper is available to manipulate tickets.
To get it: check `tickets/erg` (committed bootstrap binary, Linux x86-64 only).

As a fallback, agents can read/write directly using the example template:

```text
%erg 0.1
Title: Add retry logic for failed API requests
Created: 2026-05-04
Author: alice
Blocked-by: 0007

--- log ---
2026-05-04T09:00Z alice created
2026-05-04T14:22Z bob note Was blocked, 0007 now merged

--- body ---
## Context
The HTTP client silently drops requests when the upstream returns 503.
We need exponential backoff with jitter, capped at 3 retries.

## Exit criteria
- [ ] `client.Fetch()` retries up to 3 times on 5xx
- [ ] Backoff is 1s, 2s, 4s + random jitter less than 500ms
- [ ] Unit test covers retry exhaustion path
- [ ] `make check` passes
```

Rules agents must know:
- No `Status:` header in %erg 0.1 (use `erg migrate` for legacy files)
- Closed/not-closed is inferred from path conventions or a non-empty `Closed:` header
- `Label:` is optional and repeatable; accepted values are defined in `tickets/.ergrc` (defaults: `needs-human`, `deferred`)
- Log entries are append-only: `YYYY-MM-DDTHH:MMZ author verb detail`
- ID allocation is optimistic (git-erg#282, wontfix): `erg new` scans only the local checkout, so parallel sessions on different branches/checkouts can hand out the same ID. Fetch before allocating, run `erg check` after every fetch in ticket-heavy sessions, and on collision simply renumber to the next free ID (`git mv` + fix cross-references). Re-run the seat check **at the merge gate too**, not only at allocation: a sibling PR can renumber onto your ID after you allocated (two collisions in one afternoon, climate-finance-het 2026-07-22 — one of them caused by the other's renumber landing on main), and once the sibling has merged, the cross-PR CI gate no longer sees the collision (it compares open PRs only, not PR-vs-main). No reservation machinery exists or is planned — seat taken, move to the next one.
- A CI gate catches this trap across *open PRs*: `scripts/check-cross-pr-ticket-collision.sh` (the `cross-pr-ticket-collision` job, `pull_request` events only) lists the ticket IDs a PR adds and fails if any is also added by another open PR, naming the colliding PR and suggesting the next free ID. Per-branch `erg check` cannot see this — each branch's IDs are unique within itself. On a failure, renumber as above (`git mv` + fix cross-references) before merging. The cross-PR enumeration is the only forge-specific part, isolated behind `# harness-extension-point` calls.
- Artifacts a ticket consumes or produces (reports, data, generated files, scripts) live in their natural location in the project tree and are referenced from the body by path, not embedded wholesale, and not kept as a filename-twinned `0002-slug.md` sidecar the tooling cannot track.
- **Decision records vs. artifacts — not the same thing.** A ticket's body may hold the *decisions themselves* (a kickoff note's settled options, an arbitration verdict, the reasoning behind a choice) — that is the ticket's own process record, load-bearing for the log and exit-criteria trail, and stays in the `.erg` file. It must not hold the *material the decision was made about* (a calibration corpus, a few-shot set, mined training pairs, generated samples) — that is an artifact, and the rule above applies: natural location, referenced by path. Worked example (climate-finance-het ticket 0243, a manuscript voice-alignment pass): the four settled voice decisions stayed in the ticket body — they *are* the ticket's outcome. The few-shot comparative set moved to a file colocated with the manuscript it calibrates, and the arbitrated before/after sample pairs seeded a separate harness-level corpus schema (`voice-alignment-vision.md`) — both are reusable material the ticket merely produced, not the ticket's own record. First instinct on this exact ticket was to embed all three wholesale in the body (violating the rule above); the split above is the correction, not the original move.

Ticket validation runs in CI: the `validate-tickets` job runs `erg check tickets/` on every push and PR, and the `cross-pr-ticket-collision` job (above) guards the optimistic-ID trap across open PRs. No forge helper fails a PR for referencing a still-open ticket; closing the ticket in the same PR is a convention, enforced at merge by `erg-pr-merge`, which runs `erg close` on the ticket named in the PR's `**Ticket:**` line.

In doubt, run `erg spec` (file format) or `erg --help --all` / `erg COMMAND --help` for command documentation.

## Handoff-document sections

When a ticket is created as a handoff document (a new agent will pick it up
cold), the body should include these sections so that agent has complete
context:

```markdown
## Context
What problem or need this addresses. Why now.

## Relevant files
- `path/to/file.py` — role in this task

## Actions
1. Concrete step
2. Concrete step

## Test
- What test to write first (red step of TDD)

## Verification
- [ ] How to confirm each action worked

## Invariants
- What must not break (tests, build, existing behavior)

## Exit criteria
- Definition of done — when is this ticket complete?
```
