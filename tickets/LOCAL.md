# tickets/ — local lore

Project-specific ticket lore for this repo. `erg` never touches this file; the
generic conventions live in `tickets/AGENTS.md` and, on demand, `erg integration`.

Not imported by `CLAUDE.md`, and must stay that way: this file is cheap only
while it is not resident in every session.

## CI

`.github/workflows/CI.yml`:

- `validate-tickets` runs `erg check tickets/` on push and by hand.

Ticket-number collisions are caught by erg ID claims (`tickets/.claims/NNNN`):
two branches allocating one number conflict add/add on merge or rebase, and the
`hooks/` pre-commit and pre-merge-commit blocks refuse an unclaimed or
duplicated number. The forge-side cross-PR collision gate retired with ticket
1472.

Forge-specific calls are isolated behind `# harness-extension-point`.

## Close claims

`erg-github verify` is not installed here. Close claims are executed by the
`/merge` recipe's close step, which runs `erg close` on the ticket named in the
PR's `**Ticket:**` line, and audited afterwards by
`skills/roar/check-close-claims.sh`.
