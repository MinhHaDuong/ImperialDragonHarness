# Raid — Phase 5.0 coordination PR

Loaded from `skills/raid/SKILL.md` § Phase 5.0.

**When**: 3+ PRs in a wave will edit the same file holding a shared
hash-set / dict / dispatch registry (test allowlists like `VALID_ROUTES`,
dispatch keys, config-file conventions). If ≤2 PRs touch it, skip — a manual
rebase is cheaper than the coordination overhead.

**Why**: when N parallel PRs each append to the same cross-cutting set, the
rebase onto sibling-merged main silently drops each PR's own addition.

**How**: before opening any Wave-N PR, open one tiny PR that adds ALL of the
wave's entries to the shared registries at once, and merge it first. Each
Wave-N PR then makes a purely additive change (new file, new entry referencing
a pre-registered key) without mutating the shared set. The coordination PR
itself follows the normal verify/merge gates.
