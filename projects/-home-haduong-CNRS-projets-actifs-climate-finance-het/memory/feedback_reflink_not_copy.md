---
name: feedback_reflink_not_copy
description: "On this btrfs machine DVC checkout reflinks, so worktree data is nearly free; inodes and du cannot tell reflink from copy, use filefrag"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fa43f1a4-d3ce-4606-999a-f115508717f6
  modified: 2026-07-27T19:00:08.132Z
---

DVC's default `cache.type` chain is **reflink, then copy**, and this repo sits
on btrfs — so `dvc checkout` reflinks. A worktree that runs `make data` gets
the corpus for almost no disk: workspace file and cache blob share physical
extents and separate only on write. Free space was unchanged across a full
2.2 GB checkout in a probe worktree; 2.2 GB is the *apparent* size, and the real
cost only on a filesystem without reflink.

**Why:** I claimed "~2.2 GB per worktree" twice on ticket 0360 and defended it
as measured. The method was the bug: I compared inodes and ran `du`. **Neither
can distinguish a reflink from a copy** — a reflink produces different inodes
with link count 1, exactly the signature I read as proof of copying, and `du`
deduplicates by inode, not by shared extent. The error reversed a design
argument, not just a number: copy-on-write is not a price paid for isolation,
it is what *provides* the isolation, free.

**How to apply:** to tell reflink from copy, compare physical extents —
`filefrag -v <workspace-file>` and `filefrag -v <cache-blob>`; identical extent
ranges flagged `shared` mean reflink. Cross-check with free space (`df`) across
a large checkout. Never conclude "copy" from differing inodes alone.

Keep `cache.type` unset, and never set `hardlink` or `symlink` on the cache
shared by every worktree ([[reference_machine_padme]]): those alias the blob's
inode, and Phase 1 has an in-place writer — `np.savez_compressed()` truncates
the embeddings `.npz` directly. (The CSV path is safe either way:
`pipeline_io.save_csv` is write-temp + `os.replace`, an atomic rename onto a
fresh inode.) `tests/test_post_checkout_hook.py::test_dvc_cache_type_is_not_an_aliasing_type`
enforces this, because the setting can hide in the gitignored
`.dvc/config.local` where no diff would show it.
