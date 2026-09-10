---
name: reference_agents_md_is_a_tool_owned_asset
description: tickets/AGENTS.md is an asset embedded in the erg binary that `erg migrate` force-overwrites by charter — local edits to it are unbacked, and the harness copy has forked to 3.7x the shipped text
metadata:
  type: reference
---

`tickets/AGENTS.md` looks like a project file and is not one. It is embedded in
the `erg` binary (`git-erg/src/go/assets/AGENTS.md`, via `bootstrap_assets.go`),
written by `erg init`, and **force-overwritten by `erg migrate`** — deliberately:
`git-erg/src/go/migrate_test.go:448` asserts "a diverged AGENTS.md IS
force-overwritten by migrateLayout (charter behaviour)". Anything a repo adds to
its own copy is one routine tool run away from silent deletion.

Measured 2026-09-10 across this machine:

- shipped asset and **nine** adopter copies: byte-identical, 2 141 chars,
  md5 `b622d4f0…` (DOIfetch, git-erg, search-works-for-zotero, aedist,
  archiveCIRED, climate-finance-het, padme, polycentric_activity, zoteus-fts5)
- `chemin-de-voix`: 1 388 chars, a pre-0175 fossil — `Tag:` for `Label:`, and a
  U+FFFD where `≤` was, the corruption git-erg repaired 2026-05-29
- `~/.claude`: **7 969 chars**, forked, five additive edits 2026-07-11 → 2026-09-01,
  none propagated upstream

Two consequences that bite in opposite directions:

- **Local rules are unbacked.** The harness's collision discipline, frontier
  rule, `gh pr view` scan and decision-records/artifacts split live only in the
  forked copy.
- **Adopters are stale.** The shipped asset still teaches the `erg-github`
  `verify` check (dropped here as fiction 2026-07-12, `9703af3`) and
  "renumber to the next free ID" (reversed 2026-07-27). `climate-finance-het`
  and `search-works-for-zotero` — the repos whose incidents produced the
  correction — are still told the wrong thing.

Third, quieter: `AGENTS.md` is resident in every session via `@tickets/AGENTS.md`
in `CLAUDE.md`, but `tests/test_rules_resident_budget.py` scopes to `RULES = REPO
/ "rules"`, so none of the 0572 invariants reach it — ~2 000 tokens untaxed on top
of a gated set with 74 chars of headroom. Applying them by hand, it would fail the
ticket-number rule and **pass the shell-recipe rule while carrying a recipe**:
`SHELL_FENCE` anchors the fence at column zero and the block is indented two
spaces under a list item. That anchoring blind spot applies to `rules/**` too.

Before editing `tickets/AGENTS.md` in any repo, decide which layer the text
belongs to — see [[feedback_layer_correctness]]. Tracked as harness ticket 0906.
Adopter-shape detection: [[reference_git_erg_adopter_canonical_shape]].
