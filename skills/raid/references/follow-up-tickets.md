# Raid — creating and bundling tickets

Loaded from `skills/raid/SKILL.md` § Phase 7.

**Token economy rule**: Any time a ticket must be created in any phase, create it
with `tickets/erg new "<title>"` — never write the file directly or compute the
next ID manually. `erg new` allocates the next free ID and writes a valid
`%erg 0.1` file (preamble + `created` log line + empty body) race-safely; fill
the body, then `erg validate tickets/<new-file>.erg` (file arg, not directory)
and `erg check tickets/`, keeping mechanical work inside the tool where it belongs.

**Bundle follow-up tickets into the spawning PR.** When a raid or review
surfaces a follow-up, create it via `tickets/erg new` and commit the `.erg` onto the
current PR branch — the ticket only, never the fix. Reference it from the PR
body (`Related follow-up: tickets/NNNN`, or `Scope overflow: tickets/NNNN` when
it comes from a verify-gate verdict). The PR's `**Ticket:**` line still closes
only its own ticket on merge; the bundled follow-up stays open. Never file the
follow-up on a main checkout — main is read-only and may be dirty with parallel
work.
