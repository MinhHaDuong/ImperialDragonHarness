---
name: erg log actor is a flag now
description: "erg log LINE carries VERB [detail] only — the actor goes in --author; and a lagging committed tickets/erg hides the change, so old-contract callers look correct until the binary catches up"
metadata:
  type: feedback
---
`erg log ID LINE` no longer takes the actor in LINE. Since git-erg ticket 0276,
LINE supplies `VERB [detail]` and the actor is resolved from `--author NAME`,
else `$ERG_AUTHOR`, else git config, else `$USER`. Passing it in LINE **doubles
it**: `erg log 0207 "claude note x"` writes `<ts> haduong claude note x`.

**Why:** the old format was positionally ambiguous — `<ts> A B …` parses whether
`A` is an actor or a verb — so `erg validate` rule 11 could not tell a correct
line from a wrong one. 0276 made the actor supplied rather than policed, which
removes the failure mode instead of growing a verb vocabulary to catch it.

**The trap is the latency, not the change.** A repo's committed `tickets/erg`
travels with the repo ([[erg-binary-installation]]) and can sit months behind
git-erg. IDH's was built 2026-06-08 and only caught up 2026-09-10 — for three
months the old-contract call sites in `reviewers.sh` kept producing correct
lines, because the binary that would have doubled the actor was not there yet.
The defect is **latent**: invisible in the tests, invisible in CI, and it fires
on the unrelated day someone bumps the binary. Both halves must ship in one
commit — new binary + old call site doubles the actor; old binary + new call
site exits 1 on `unknown flag "--author"`.

**How to apply:** when a call site or a doc example embeds the actor in LINE,
fix it *and* check the binary in the same breath — `./tickets/erg version` gives
the build date and revision. Bump by taking git-erg `main`'s committed
`tickets/erg` and proving provenance against the remote rather than trusting a
local build: `git hash-object tickets/erg` must equal
`gh api repos/<owner>/git-erg/contents/tickets/erg?ref=main --jq .sha`. After a
bump, `erg check tickets/` warns that `AGENTS.md` predates the embedded assets;
leave it where the repo's copy carries local edits — `erg init` preserves those
and exits 2, it does not clobber them. Related:
[[erg-verb-drift-in-skill-examples]].
