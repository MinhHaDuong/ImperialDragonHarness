# tickets/ — local lore

Project-specific ticket lore for this repo. `erg` never touches this file; the
generic conventions live in `tickets/AGENTS.md` and, on demand, `erg integration`.

Not imported by `CLAUDE.md`, and must stay that way: this file is cheap only
while it is not resident in every session.

## CI

`.github/workflows/CI.yml`:

- `validate-tickets` runs `erg check tickets/` on push and PR.
- `cross-pr-ticket-collision` runs `scripts/check-cross-pr-ticket-collision.sh`
  on `pull_request` and fails a PR whose added ticket ID is also added by an
  open PR, or already present on the base tip.

Forge-specific calls are isolated behind `# harness-extension-point`.

## Close claims

`erg-github verify` is not installed here. Close claims are enforced at merge by
`erg-pr-merge`, which runs `erg close` on the ticket named in the PR's
`**Ticket:**` line (`/merge`).
