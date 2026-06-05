---
name: project_release_signing_model
description: "git-erg release signing model — sign tags at release cadence, curl pins to tag not main"
metadata: 
  node_type: memory
  type: project
  originSessionId: 76fda995-7a90-4d73-8bd9-1acc840f289f
---

The bootstrap binary signing model agreed during 0181–0184:

- **Sign at release cadence, not CI cadence.** One GPG tag per release; CI rebuilds the bootstrap binary freely without requiring a new signature.
- **curl download URL pins to the latest signed tag**, not `main`. Example: `raw/2026-05-30/tickets/erg`. When a new release tag is cut, update the URL in README § Install step 2.
- **main-head binaries** (CI rebuilds) are unattested by GPG; verify those with `make verify` (rebuild from source).
- **Current signed tag**: `2026-05-30` (key 4A46C91E03B83B23), attesting binary hash `087860f4…` at commit `126d9ac8`.

**Why:** Requiring a GPG signature on every CI push is ceremony without value — it would force the maintainer to sign dozens of identical-logic rebuilds. The signed tag attests the source-code state; `make verify` handles the in-between.

**How to apply:** When drafting a release ticket or updating install docs, pin the curl URL to the latest signed tag name. When cutting a release: `git tag -s <date> HEAD && git push --tags`, then update README curl URL.
