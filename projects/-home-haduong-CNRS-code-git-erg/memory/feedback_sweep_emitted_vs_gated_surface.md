---
name: feedback_sweep_emitted_vs_gated_surface
description: "when sweeping for a fixed anti-pattern's siblings, classify by surface category (emitted-into-adopter & guaranteed-hit vs file-gated dev hint), not the surface string"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 69ab4112-39e6-4a2c-8f8e-f5606bb970a0
---

When sweeping for siblings of a just-fixed anti-pattern (roar step 3), discriminate by **surface category**, not by the literal string that was wrong.

0242 fixed build-system-specific remediation (`Run 'make build' first`) in the
pre-commit hook git-erg installs. The grep also hit `src/go/version.go:180`
(`{"./build/erg", "run: make build"}`). Surface string matched — but it is NOT
the same defect:

- **0242 (real defect):** text *emitted into the adopter's repo* (the hook),
  fired on a **guaranteed-hit** condition (`tickets/erg` missing on commit).
  Every vendored adopter hits it; they can't hand-edit it (re-emitted on every
  `erg install --hooks`). Must be agnostic. Fix upstream.
- **version.go hint:** *runtime-printed by the binary itself*, gated behind
  outdated-detection that only fires in a multi-copy git-erg **dev** tree; the
  `make build` hint is bound to `./build/erg`, which cannot exist in a vendored
  tree (EvalSymlinks fails → skipped). Correctly-scoped dev tooling.

The 0242 ticket body said so explicitly: "version.go:180 is a build-provenance
label, NOT hook text; do not touch." Filing it would be pattern-matching the
string, not the defect.

**Why:** a class-sweep that keys on the surface string over-files; one that keys
on surface category (who emits it, is it guaranteed-hit, can the adopter edit
it) files exactly the real instances. git-erg's emitted-into-adopter surfaces
are `hookBody`, `pushHookBody`, `agentsBody` (incl. `--create-agents-md`) — all
must stay build-system-agnostic; that's the complete set to check.

**How to apply:** for each grep hit, ask "is this emitted into the adopter's
environment and guaranteed to fire?" Yes → same class, file/fix. No (runtime
dev tooling, file-gated) → not the class, leave it. Confirm against the source
ticket's "do not touch" notes before filing. See [[feedback_edit_canonical_asset_not_live_copy]].
