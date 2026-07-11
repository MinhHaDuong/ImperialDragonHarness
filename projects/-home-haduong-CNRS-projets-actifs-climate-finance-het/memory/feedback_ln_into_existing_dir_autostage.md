---
name: feedback_ln_into_existing_dir_autostage
description: ln -s into an existing dir drops the link INSIDE it; dvc autostage + broad git add then commits the machine-specific loop symlink
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a3584f5c-bfd3-4b93-b0bb-06c5d1a89788
---

`ln -s <primary>/data/catalogs data/catalogs` when `data/catalogs` already
exists creates `data/catalogs/catalogs` — a self-looping, absolute,
machine-specific symlink. With `.dvc/config` `autostage = true`, a later broad
`git add` sweeps it into an unrelated commit (431af0ce, 0240 epic close); it
then loops every recursive traversal (`glob('**')`, `find -L`) in every
checkout. Caught and fixed in ticket 0252, PR #1038.

**Why:** the worktree data-sharing idiom ([[feedback_verify_datadep_worktree_symlink]])
uses exactly this `ln -s` shape, so the trap re-arms every time a worktree
needs contract data.

**How to apply:** use `ln -sfn <target> <linkname>` only when the linkname does
not yet exist as a directory — or symlink individual contract *files*, never
the directory onto itself. Guard exists: adherence test
`test_phase_layout.py::test_no_committed_symlink_under_data` fails any tracked
mode-120000 entry under `data/`.
