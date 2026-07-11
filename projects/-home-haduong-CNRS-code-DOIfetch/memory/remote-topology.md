---
name: remote-topology
description: DOIfetch git remotes — origin is READ-only upstream; the real trunk is the MinhHaDuong fork
metadata: 
  node_type: memory
  type: project
  originSessionId: 20e2bac5-d52d-434d-9e46-7d8a3fce29ba
---

DOIfetch's `origin` is `hanhan6688/DoiHarvest` — READ-only (viewerPermission
READ); pushing there fails with 403. The maintained trunk is the fork
`MinhHaDuong/DOIfetch` (renamed 2026-07-08 from the auto-created `DoiHarvest`),
wired as the `fork` remote. Upstream is abandoned (last commit 2025-08-07) and
~50 commits behind; the fork carries the full modern history.

Merge flow: land feature branches locally onto `main` (fast-forward where the
branch descends from `main`; rebase `--onto main` when it diverged), then
`git push fork main`. Do NOT try to push to `origin`.

The fork still shows GitHub's "forked from" banner (isFork true); detaching it
needs a GitHub Support request — cosmetic, deferred.
