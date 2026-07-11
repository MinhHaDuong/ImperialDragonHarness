---
name: feedback_moving_files_narrows_guard_globs
description: Relocating files silently narrows fixed-directory guard globs; a green suite hides the lost coverage
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d329f489-e346-4cba-8c47-36d92cd64019
---

Relocating files that a test guard enumerates by globbing a **fixed directory**
(e.g. `glob("<root>/*.mk")`) silently drops the moved files out of that guard's
coverage. The test keeps **passing** — not because the contract still holds, but
because it now parametrizes over fewer files. A green suite actively hides the
regression.

**Why:** these guards are class-ratchets (scan every producer/fragment for an
anti-pattern). Their teeth come from *coverage*, so narrowing coverage is a
silent defeat, invisible to a diff review and to `make lint`.

**How to apply:** when a reorg/rename moves files, `grep` the whole test tree for
every enumeration of that file type (`glob(...*.EXT)`, `listdir ... endswith`),
not just the sites that break the build. Extend each to the new location. Better:
route all of them through ONE shared discovery helper so a future move updates one
place, and add a meta-guard that fails on any hand-rolled glob outside the helper.
Concretely on climate-finance-het (0239 relocating 5 `.mk` → `scripts/analysis/`):
5 sites hand-rolled `.mk` enumeration; only 2 broke the build, 1 more was caught
by `/gaze`, and 2 (`test_makefile_contract`, `test_deliverables_layout`) had a
*latent* gap — passing but no longer covering the moved files. Filed as 0248.

This is the enumeration-glob cousin of [[feedback_reorg_tracker_first_class_guard]]
(guards must be class-level, not per-file whitelists) and the same "green tests
hide a misplaced/uncovered output" family as [[feedback_bytecheck_old_vs_new_not_golden]].
Verify a pure move with the artifact/graph itself (`make -n` recipe-identity +
one runtime build), never a green suite alone.
