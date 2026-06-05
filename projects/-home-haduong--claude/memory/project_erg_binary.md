---
name: erg binary installation
description: erg binary travels with every repo at tickets/erg (committed, not gitignored); must be built or copied manually on new machines if not present
type: project
originSessionId: 3018d397-cd2c-496a-afc5-027ba8189c6a
---
The `tickets/erg` binary is committed in IDH. External projects: `erg init` gitignores `tickets/erg` by default (post git-erg PR #92); skills fallback `${ERG:-tickets/erg}` works when PATH-installed erg is present. PRs #103-104 (2026-05-05) committed the binary; 2026-05-06 it moved from `tickets/tools/go/erg` to `tickets/erg`.

**Why:** The binary travels with the repo so CI and nightbeat runs on any machine without a separate build step.

**How to apply:** New machines get the binary from `git pull`. If the binary is missing or stale, build it from the git-erg source repo and copy to `tickets/erg`. Skills resolve the binary via `${ERG:-tickets/erg}`.

Current nightbeat targets with pre-commit hooks + erg: aedist-technical-report, chemin-de-voix, git-erg (all on padme).
