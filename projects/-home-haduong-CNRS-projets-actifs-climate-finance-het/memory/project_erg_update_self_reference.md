---
name: project_erg_update_self_reference
description: "erg update pulls from the current repo's origin, so a repo that commits its own erg binary compares to itself and never advances — fixed by the [update] url key, at the cost of erg init exiting 2 forever"
metadata: 
  node_type: memory
  type: project
  originSessionId: 78accd55-356d-44d9-b79e-e6471e94c518
  modified: 2026-09-10T09:08:56.112Z
---

`erg update` fetches the committed binary from the **current repository's**
`origin`. In this repo, which commits its own `tickets/erg`, it therefore
refetched the binary this repo had itself committed, compared it to itself, and
answered "already up to date" while doing nothing. The binary sat on the
2026-06-11 build for three months — not an oversight, a closed loop.

Fixed 2026-09-10 (PR #1315) by activating the key already present as a comment
under `[update]` in `tickets/.ergrc`:
`url = https://github.com/MinhHaDuong/git-erg.git`. Binary and assets moved to
rev `089cd31` (2026-06-29); `tickets/AGENTS.md` 1862 → 2141 bytes.

**Accepted cost, measured on two repos:** once `.ergrc` is edited, `erg` classes
it "local edits -- preserving" and **every later `erg init` exits 2**. The effect
is intact — `AGENTS.md` is still refreshed — only the exit code lies. Verified
here by dry-run. A dead update path costs more than a noisy exit code. The
reasoning is written into `.ergrc` itself, not just the PR body, so the next
reader of the file finds it.

**Commit all four together** — `tickets/erg`, `tickets/AGENTS.md`,
`tickets/.erg-assets`, `tickets/.ergrc`. `isCleanUpgrade` compares asset to stamp
without checking which is older, so a binary older than its stamp overwrites the
newer asset with its embedded copy, prints "refreshed", and exits 0. A partial
commit arms that trap for the next clone. Never run `erg init` alone here.

**Caveat on the content:** the one-line `AGENTS.md` diff advises renumbering to
the next free ID on collision — exactly what the harness abandoned in favour of
renumbering clear of the frontier. It was accepted so stamp and content agree,
never for its merit; `.claude/rules/git.md` remains the rule. Do not cite that
line.
