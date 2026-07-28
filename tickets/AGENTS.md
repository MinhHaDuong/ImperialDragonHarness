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
- ID allocation is optimistic (git-erg#282, wontfix): `erg new` scans only the local checkout, so parallel sessions on different branches/checkouts can hand out the same ID. Fetch before allocating, run `erg check` after every fetch in ticket-heavy sessions, and on collision renumber (`git mv` + fix cross-references) — but **not to the next free ID**. Re-run the seat check **at the merge gate too**, not only at allocation: a sibling PR can renumber onto your ID after you allocated (two collisions in one afternoon, climate-finance-het 2026-07-22 — one of them caused by the other's renumber landing on main), and once the sibling has merged, the cross-PR CI gate no longer sees the collision (it compares open PRs only, not PR-vs-main). No reservation machinery exists or is planned.
- **Renumber clear of the frontier, never to the next free ID.** The next-free ID is the most contended seat in the repo: every parallel session computes the same value and races for it, so a renumber is exactly as collision-prone as the original allocation, and chasing the frontier cannot converge while siblings are still filing. Pick a number well above the high-water mark — IDs are free and a gap costs nothing. Cost of the old advice (climate-finance-het, 2026-07-27): one filing collided **three times in one session** — 0384 hit an open PR, the renumber to 0385 hit a PR that merged minutes later, the renumber to 0386 hit another — leaving `origin/main` red on a duplicate ID twice. It settled first try at 0400, twelve clear of a frontier at 0388.
- **Scan for collisions with `gh pr view`, never `gh pr list --json files`.** `gh pr list` does not populate `files`, so a one-shot list-plus-filter returns empty regardless of content — "no collision found" and "I never looked" are the same output, and that is what let the first 0384 collision through. Enumerate, then query each PR:
  ```bash
  for n in $(gh pr list --state open --limit 60 --json number --jq '.[].number'); do
    gh pr view "$n" --json files --jq '.files[].path' | grep -q "tickets/$ID" && echo "PR $n uses $ID"
  done
  ```
  General form of the trap: a check whose "all clear" is indistinguishable from its "I could not look" is not a check. Before trusting a scan that returns nothing, run it against a case known to be positive.
- **After a ticket PR merges, run `erg check` against `origin/main`, not the branch.** A branch-local `erg check` passes by construction — each branch's IDs are unique within itself — so it structurally cannot see a cross-PR duplicate. This is the same blind spot the CI gate covers for *open* PRs, and it is the only check that catches a duplicate that has already landed. **In a repo with no CI, it is the only collision check at all**: climate-finance-het has no `.github/workflows/` by decision (its ticket 0321), so the `cross-pr-ticket-collision` job described below never runs there, and both times main went red nothing noticed until a `/roar` hygiene step happened to list two identically-numbered PR titles side by side.
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
