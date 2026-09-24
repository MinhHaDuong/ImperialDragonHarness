---
name: feedback_erg_binary_refresh_is_not_init
description: "Copying a newer erg binary into an adopter leaves its tickets/AGENTS.md at the old text; only `erg init` upgrades the conventions file, and it preserves a locally edited .ergrc"
metadata:
  type: feedback
---

The 2026-09-24 coherence audit found three repos whose `tickets/AGENTS.md` still
told agents to renumber a colliding ticket to the next free ID — the race
climate-finance-het had documented after 0384 → 0385 → 0386. One of them
(aedist) had refreshed its binary two weeks earlier in a PR titled "refresh erg
binary and assets"; the asset it cared about was never rewritten, because the
binary carries the new text and only `erg init` unpacks it.

**Why:** the binary and the conventions file travel separately. A refresh that
copies the binary looks complete — `erg version` reports the new rev, `erg check`
passes — while every session keeps reading the old instructions.

**How to apply:** upgrading an adopter is two steps, copy `tickets/erg` then run
plain `tickets/erg init` (no `--force`: it refreshes `AGENTS.md` and preserves a
locally edited `.ergrc`, printing which). Verify by byte-comparing
`tickets/AGENTS.md` with the harness copy, not by the version string.
