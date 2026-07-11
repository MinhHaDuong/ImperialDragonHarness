---
name: asset-edit-ci-gates
description: Two CI traps when editing git-erg embedded assets or closing tickets — ASCII-only assets and archive-before-push; both now caught by `make test`.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 340eae9b-77b2-475c-8803-c27a4823fe21
---

Editing `src/go/assets/*` (AGENTS.md, .ergrc) or closing a ticket has two gates that `make regen-assets` does NOT enforce (it only copies files). Both are now caught by `make test` locally — run it before pushing:

1. **Embedded assets must be pure ASCII.** `tests/test_init.sh` rejects any non-ASCII/non-printable byte in the init-unpacked assets. Since ticket 0245 (merged 2026-06-18, PR #308) the guard loops over every asset in `initAssetPaths` (`.ergrc` AND `AGENTS.md`), not just AGENTS.md. LLM edits routinely slip in a Unicode em-dash `—` or curly quotes; use the house ` -- ` instead.
2. **A closed ticket must be archived into `tickets/closed/` before push.** Adding a `Closed:` header but leaving the file in `tickets/` makes `erg check` fail with "closed ticket not in closed/ directory". Run `erg archive <id>` (or `git mv` it) in the same commit.

**`make test` now runs a store-shape gate.** Ticket 0246 (merged 2026-06-18, PR #309) added a `check-store` Makefile target (`erg check tickets/`) folded into `make test`'s prerequisites. So `make test` does THREE things now: Go unit tests, shell suites, AND `erg check tickets/` — an unarchived closed ticket / duplicate ID fails locally, not only in CI's `test-check`. (This is also why CONTRIBUTING.md drifted — ticket 0247.)

**Why:** PR #305 (ticket 0244) hit both gate-1 and gate-2 at once — an em-dash in the asset and an unarchived closed ticket — and `bash -e` masked the second behind the first, so each surfaced only after fixing the prior. Tickets 0245/0246 closed both gaps.

**How to apply:** after any asset edit or ticket close, run `make test` locally before pushing — it now catches both classes. `make regen-assets` alone still runs no check.
