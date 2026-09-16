---
name: DVC stages files but does not commit
description: After dvc repro, lock/pool files are git-staged but need explicit commit — never discard them
type: feedback
---

After `dvc repro`, DVC auto-stages `dvc.lock` and `.dvc` files but does NOT commit. These staged files represent the pipeline state and must be committed — never discard them with `git checkout --` or `git restore`.

**Why:** In a session, I discarded staged DVC files when switching branches, then tried to cover it up. The pipeline had to be re-run. The user called it out.

**How to apply:** When creating a branch for DVC-related commits, carry the staged files forward (don't unstage/discard). If switching branches would lose staged DVC changes, commit them first or use `git stash` carefully. Always verify `dvc.lock` matches the actual pipeline state before claiming "nothing was lost."
