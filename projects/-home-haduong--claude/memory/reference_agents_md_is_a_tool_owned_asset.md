---
name: reference_agents_md_is_a_tool_owned_asset
description: "tickets/AGENTS.md is an asset embedded in the erg binary, not a project file — restored to pristine 2026-09-16 and now gated; erg check compares it to the committed stamp, never to the running binary's embedded hash"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c1559b8c-fb50-4f07-9cc7-8204a2db11f7
  modified: 2026-09-16T12:55:45.400Z
---

`tickets/AGENTS.md` looks like a project file and is not one. It is embedded in
the `erg` binary (`assets/AGENTS.md`, via `bootstrap_assets.go`) and written by
`erg init`. Before editing it in any repo, decide which layer the text belongs
to — see [[feedback_layer_correctness]].

**Settled 2026-09-16, harness ticket 0906.** The harness copy had forked to
8 005 chars against a shipped 2 356 and was resident in every session of every
project via `@tickets/AGENTS.md`. It is now pristine and gated by
`tests/test_erg_assets_pristine.py`, which hashes `AGENTS.md` and `.ergrc`
against `tickets/.erg-assets`. Do not edit the file; edit upstream, or use the
shelf below.

**`tickets/LOCAL.md` is the shelf for adopter-specific lore** — CI job names,
local scripts, past incidents. `erg` never touches it. It is deliberately NOT
imported by `CLAUDE.md` and must stay that way: it is cheap only while it is not
resident. The harness copy holds ~290 chars, all of it CI wiring.

**Generic long-form conventions print on demand: `erg integration`.** ID
collision recovery, the `gh pr view` scan, `erg check` against the default
branch, decision-records-vs-artifacts, the handoff-document template. A local
copy of any of it is duplication, not documentation.

**The check compares your file to your committed stamp, never to the running
binary's embedded hash** (`isCleanUpgrade`, `manifest.go:391`). With a stamp
present the test is `diskHash == stampedHash`; only a *stampless* store falls
back to a known-hash list. So a repo whose `.erg-assets` records 2 356 stays
green after upstream ships 2 393 — being behind the binary is a *warning*
meaning "a re-init would refresh you", not a divergence. Vendor a new binary
whenever convenient and `erg init` refreshes through the stamp path. This is
why no binary-bump coordination was needed at 0906, contrary to what both
sessions assumed before reading the code.

**Restore by running the tool, not by copying the file.** `erg init --force`
makes the equality true by construction; a hand copy makes it true by care, and
care is what produced the fork. Corollary that nearly bit: the asset's last line
promises the long-form conventions "print on demand", and with a stale vendored
binary that promise is false — measured 7 531 bytes and 0 of 4 sections before
the refresh, 13 506 and 4 of 4 after. Refresh the binary and confirm the channel
carries the content *before* deleting any local copy.

Two claims the shipped asset used to get wrong — an `erg-github` sentence in the
indicative for a check installed nowhere, and an allocator premise contradicted
by [[feedback_cross_pr_ticket_id_collision]] — were corrected upstream the same
day. Adopter-shape detection: [[reference_git_erg_adopter_canonical_shape]].
