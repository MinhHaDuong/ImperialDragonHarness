---
name: feedback_verify_makefile_pathrefactor_with_make_n
description: "Verify a data-dependent Makefile path/variable refactor with `make -n` + one runtime target spot-check + grep — never a full downstream build, which needs the corpus and can fail on unrelated phase entanglement."
metadata:
  node_type: memory
  type: feedback
  originSessionId: 4ffdf7ae-8403-47bc-87ed-e116676de228
---

For a Makefile refactor that only moves **where** outputs are written (a
directory-variable flip like `DIV_TABLES := content/tables` → `$(DERIVED)`,
ticket 0231), the correct verifier is:

1. **`make -n <every affected target>`** — executes nothing, but performs Make's
   real variable expansion, so it proves producer `--output` AND consumer
   `--input` both resolve to the new location and that zero old-location paths
   survive in any recipe. This is the load-bearing proof. Symlink the primary
   checkout's contract files into the worktree first so `-n` gets past
   prerequisite checks ([[feedback_verify_datadep_worktree_symlink]]).
2. **One runtime spot-check** — build a single cheap target and confirm the file
   lands at the new path (0231: `venue-concentration-table` wrote to
   `data/derived/`). The other subsystems use the identical `--output $@`/`$(VAR)`
   mechanism, so one is enough; skip the heavy compute.
3. **grep** for hardcoded old-location paths in the scripts (the fallback defaults
   `make -n` can't see because Make always passes explicit args).

**Why:** 0231 session (2026-07-10). The ticket's stated gate was a full
`make papers`. It was the WRONG gate: it needs the 322 MB corpus, is slow, and it
died twice on things unrelated to the refactor (a missing Phase-1 `citations.csv`,
then `import umap` in a Phase-2 clustering step) — a full writing/render build
drags in the whole analysis, so its failures rarely implicate your path change.
`make -n` + the venue spot-check + grep confirmed 0231 in seconds; the full build
confirmed nothing about the flip before failing on an env gap.

**How to apply:** don't accept "run `make <big-target>`" as the confirmation for a
path/variable refactor. Prove the graph with `make -n`, spot-check one target at
runtime, grep the scripts. Reserve the full build for changes that alter analysis
*content*, not artifact *location*. (The phase-entanglement those build failures
exposed — `make papers` is not Phase-3 — is ticket 0237.)
