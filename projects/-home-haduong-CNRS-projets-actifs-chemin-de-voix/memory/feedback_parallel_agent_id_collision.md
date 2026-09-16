---
name: parallel agent ticket ID collision
description: When parallel agents split tickets simultaneously, ID collisions happen — detect before committing
type: feedback
originSessionId: e8186d50-e37d-42a0-be0d-2067de5c36c1
---
Parallel agents may create tickets with the same numeric IDs (e.g., both agents use 0034–0043 for different purposes). Git won't catch this — different filenames, same ID prefix. The validator catches it post-commit.

**Why:** During the corpus ticket restructuring, a background agent already split 0019/0021/0022 into per-voice discover tickets (0034–0043) while we were building our own split in a worktree. Our fetch tickets also started at 0034, colliding.

**How to apply:** Before creating a batch of new tickets, always run `tickets/tools/go/erg next-id tickets/` *and* check origin/master's ticket directory (`git ls-tree origin/master tickets/`) to see if origin has advanced. Never assume local max-ID equals remote max-ID when working in a worktree during active multi-agent sessions.
