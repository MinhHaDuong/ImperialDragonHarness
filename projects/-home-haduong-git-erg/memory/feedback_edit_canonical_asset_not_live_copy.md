---
name: feedback_edit_canonical_asset_not_live_copy
description: "GIT-ERG ONLY — erg's agent docs must be edited in src/go/assets/ (the embedded, propagating source), not the diverged live tickets/ copy"
metadata: 
  node_type: memory
  type: project
  originSessionId: 80a9388c-9a6a-429f-8b09-8c555e28e3ed
---

**Specific to the git-erg repo:** it is the repo that *builds* erg and ships erg's own
docs as embedded assets. Ordinary projects have a single `AGENTS.md` with no asset/live
split — edit that directly. Do not generalize the rule below to other repos.

In git-erg, erg bundles its agent-facing docs — `AGENTS.md`, `spec-erg-v1.md`, `integration.md`,
`.ergrc` — as **embedded assets in `src/go/assets/`**, compiled into the binary via
`//go:embed` (`src/go/bootstrap_assets.go`) and unpacked by `erg init` into a repo's
`tickets/`. The live `tickets/AGENTS.md` and `tickets/spec-erg-v1.md` are already-unpacked
copies that have **diverged** from the assets; nothing syncs them.

To change guidance/doctrine that should reach all erg users, edit the **canonical
`src/go/assets/<file>`** — NOT the live `tickets/<file>`. Editing only the live copy is
local to this repo and propagates to no one. (Ironically this is the same name-coupled
sidecar-drift the artifact-storage guidance warns about.)

Editing an embedded asset makes the committed `tickets/erg` stale — but do **NOT** rebuild it
by hand. A local `make update-bootstrap-binary` is non-reproducible (its size/content depend
on the local Go toolchain, and it records the current HEAD revision), so it would fail
`make verify` and produce a binary that differs from the canonical one. **CI rebuilds the
bootstrap binary reproducibly on embedded-asset changes** — let it. Just commit the asset
edit (plus the live `tickets/` copy) on a branch; CI handles the binary on the PR. Likewise
do not `make install-erg-binary` to "propagate" — it installs a non-canonical local build
over `~/.local/bin/erg`, which other concurrent agents share.

**Why:** the asset is the source of truth that ships in the binary and seeds `erg init`;
the live `tickets/` copy is derived and diverged, so edits there silently fail to propagate.

**How to apply:** when asked to update erg's agent docs or ticket-format guidance, edit
`src/go/assets/` first (and keep the live `tickets/` copy consistent if git-erg's own agents
rely on it), commit both on a branch, and let CI rebuild `tickets/erg`. Do not rebuild or
reinstall the binary locally. Related: [[feedback_rename_hard_not_aliased]],
[[feedback_doc_writing_conventions]].
