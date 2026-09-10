---
name: reference_agents_md_is_a_tool_owned_asset
description: tickets/AGENTS.md is an asset embedded in the erg binary, not a project file — the harness copy has forked to 3.7x the shipped text, and the shipped text itself describes an uninstalled optional check in the indicative
metadata:
  type: reference
---

`tickets/AGENTS.md` looks like a project file and is not one. It is embedded in
the `erg` binary (`git-erg/src/go/assets/AGENTS.md`, via `bootstrap_assets.go`)
and written by `erg init`. Before editing it in any repo, decide which layer the
text belongs to — see [[feedback_layer_correctness]].

**How exposed a local edit is, at the evidence level actually reached.**
`migrate.go:261` calls `installAssets(…, refuseDiverged=false)` and
`migrate_test.go:448` asserts at unit level that a diverged `AGENTS.md` is
force-overwritten by `migrateLayout` "(charter behaviour)". End to end this is
**not** demonstrated: git-erg 0278 records a fixture with a local edit that
survived `erg migrate`, the run reporting `already clean` and never reaching the
asset step. Real in the code, open in practice. Do not state it as a settled
fact — an earlier version of this note did.

**Byte-identical adopters are current, not frozen.** Nine copies on this machine
match the shipped asset (md5 `b622d4f0…`, 2 141 chars) and that reads like
staleness. Measured with `erg init --dry-run` instead of inferred from hashes
(git-erg 0278, eleven repos): six `unchanged`, four `would refresh` and since
refreshed, one stampless (`chemin-de-voix`). The problem is what the shipped
asset *says*, not its age. Inferring freshness from a checksum is the trap here.

**What the shipped asset says wrong.** Two lines, and neither is false:

- The `erg-github` sentence is a **mood error**. The helper is real (a
  5 471-byte POSIX script, verbs `install` and `verify`) and does what the
  sentence says, but the sentence is in the indicative and the check is
  installed in zero repos — the script lives only in git-erg's own `tickets/`,
  and `erg-verify.yml` is in no workflows directory anywhere. An optional
  facility described as installed.
- "Renumber to the next free ID" is **under-generalized**, not wrong: correct in
  a single-session repo, racy under parallel sessions.

**The drift runs both ways.** The harness fork *dropped* the anti-suffix rule
(`never suffix them (0134a, 0134b)`) that the asset and nine adopters still
carry.

**Cost.** The harness copy is 7 969 chars, ~2 000 tokens resident in every
session via `@tickets/AGENTS.md`, outside `tests/test_rules_resident_budget.py`
(which scopes to `rules/`). A merged version with every durable idea kept and
all narrative stripped measures 3 873 chars — the substance survives at under
half the cost.

Harness ticket 0906; upstream git-erg 0277 (ban and destination, blocked by
0278), 0278 (asset machinery), 0279 (direction-blind downgrade).
Adopter-shape detection: [[reference_git_erg_adopter_canonical_shape]].
