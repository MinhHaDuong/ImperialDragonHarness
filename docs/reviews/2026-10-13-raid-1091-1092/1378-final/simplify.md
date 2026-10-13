# Simplification review — PR 1378

Code review anchor: `7e1f77b1928ee49de97990940fd4b24b3df49cc7` against `origin/main`. Final documentary confirmation: `9e2fdd3fb5706f452722718967524ac8985a43cf`. The native review found no actionable bug; the regression seat approved and records the behavior constraints and prior consider/nofollow dispositions. At the final anchor, both code/test blobs are identical to the reviewed anchor; the only intervening change is ticket 1091 completion evidence for the actual primary full check. The requested diff census covers `scripts/resident_census.py`, `tests/test_resident_census.py`, and tickets 1091/1092.

## Verdict

CLEAN. I found no safe simplification that reduces complexity without weakening the tracked 7000-character contract, visibility of local inventory and session cost, or conservative handling when Git metadata is unavailable.

## Candidates considered

- **Remove `Entry.tracking` or `Entry.linked` metadata:** rejected. Rendering needs per-card tracking and whether a local card is reached through a symlink; deriving either later would require filesystem/root state that `Entry` does not retain. These fields also let the same census rows drive the detail and summary reports.
- **Combine `skills` and `skills-local` into one channel:** rejected. It reintroduces the primary-checkout budget failure, or requires special-case subtraction in the gate. Keeping the supplemental total in session accounting preserves real cost while the existing cap remains a tracked-content contract.
- **Classify by symlink status alone or drop `_skill_index`'s unknown case:** rejected. That loses tracked directory symlink ownership or misclassifies all observed cards as local when Git cannot establish the index. The metadata-free control correctly keeps all cost in the budgeted channel.
- **Remove the separate inventory from `_render`:** rejected. `--detail` repeats the card costs with token estimates, but the leading inventory adds tracking state; in summary mode it is the only per-card record. This supports distinguishing an observed overlay from an absent or unobserved one.
- **Replace the fixture's temporary index setup with `tracked_tree` alone:** rejected. The helper deliberately returns a metadata-free checkout; index semantics require initializing and populating Git metadata for the tracking controls. The tests already reuse `tracked_checkout` and `child_env` rather than adding another fixture layer.
- **Collapse `_skill_index`'s guarded subprocess/parser path:** rejected. The explicit failure-to-unknown fallback and record parsing are part of conservative behavior. A shorter expression would obscure the failure boundary without removing a meaningful abstraction.

Ticket 1091's added prose records the intended channel semantics and execution limits; ticket 1092 is annotation-only in this diff. No prose duplication there is a safe code simplification for this task.
