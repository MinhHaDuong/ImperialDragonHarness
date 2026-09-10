---
name: reference-erg-update-fetches-from-the-repos-own-origin
description: "In an adopter repo `erg update` fetches from that repo's own origin, compares the binary to itself and says \"already up to date\" — the default update path cannot ever move an adopter forward"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 66e60b89-dd60-41a4-8f88-17567531b19a
  modified: 2026-09-10T10:04:07.081Z
---

erg has no network client; distribution is git. Each adopter repo **commits**
the binary at `tickets/erg`. `erg update` locates the ticket store, runs
`git fetch <remote> HEAD` in its repository, extracts the committed binary at
that remote's default branch, and swaps itself for it. `<remote>` defaults to
`origin`.

In a **fork of git-erg** that works: `origin` is git-erg, so "fetch origin's
committed binary" means "get the newer erg". The code says so deliberately —
*"makes update fork-kind: you update from where you cloned"*.

In an **adopter** repo it cannot work. `origin` is that project (padme.git,
climate-finance-het.git…), so `erg update` re-fetches the binary the repo
already committed, compares it to itself, and prints `already up to date`,
exit 0. It is a team-sync command, not an upstream-upgrade command. Verified
directly in padme, 2026-09-10, while it was running a binary three months old.

**Three silences stack.** `erg update` bare says "up to date" (true statement,
misleading answer); fetch errors exit 0 by design, so a missing `origin`
(CNRS/html has none) is also silent; and `erg check`'s drift WARN compares the
stamp to the *running* binary's embedded asset, which in a never-updated repo
agree. The repo is quiet on every channel because everything it compares is
internally consistent with itself. Internal consistency is not currency.

**The fix, per repo**, in `tickets/.ergrc` under `[update]` (which ships with
the key commented out — decommenting beats appending, no duplicate):

    url = https://github.com/MinhHaDuong/git-erg.git

Cost, measured: an edited `.ergrc` counts as a local edit, so every later
`erg init` exits 2 after preserving it and the canonical `erg update &&
erg init` chain reports failure. The effect is intact — only the exit code
changes. Applied to aedist, padme, CNRS/html and climate-finance-het on
2026-09-10, with the reasoning written into `.ergrc` itself so the next reader
does not read exit 2 as a fault.

Related: [[asset-edit-ci-gates]], [[feedback-bare-gh-pr-merge-drops-close-claim]].
