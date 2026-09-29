---
name: hermetic-test-rebase-home-prefix
description: "A test that resolves a $HOME-prefixed path against the filesystem must rebase that prefix onto the checkout root (from __file__), not the live $HOME — else it passes only where $HOME/.claude IS the checkout and fails on CI"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ea16dbd8-a049-4677-9d6d-eaa68830a321
---

Ticket 0328, PR #580 (2026-07-14): a static test asserted every PreToolUse hook
command in `scripts/beat-settings.json` resolves to an existing executable. The
commands are stored in the agnostic `$HOME/.claude/...` form. The first version
expanded the command against the live `$HOME` and called `is_file()` on the
result. It passed on the dev box — where `$HOME/.claude` *is* the harness
checkout — purely by coincidence, and went RED on CI (`$HOME=/home/runner`, the
checkout elsewhere; run 29321962507). Gaze caught it; the reroll rebased any
`$HOME/.claude/` prefix onto `REPO_ROOT` (computed from `__file__`) before the
filesystem check.

**Why:** a hermetic test must resolve every env-dependent path relative to the
artifact under test, never to the runner's real environment. When a stored path
happens to overlap the dev machine's real layout, `is_file()` passes locally by
coincidence and the coincidence hides the defect until a runner with a different
`$HOME` exposes it. The fix pattern: `expanded.relative_to(HARNESS_INSTALL_PREFIX)`
then `REPO_ROOT / relative`, falling through unchanged when the path is not under
the prefix. Distinguish this from a pure *expansion-logic* equality check
(`assert expand("~/foo") == Path.home()/"foo"`), which is hermetic by
construction because both sides share `Path.home()` and never touch the disk —
that pattern is fine (see `tests/test_beat.py::TestLoadProjects`).

**The other half: the checkout itself (2026-09-29, ticket 0989).** Faking
`HOME` is not enough when the code under test also reads the *checkout* it runs
from. The idh tests pointed `HOME` at a tmp dir but kept the real repo as
`$IDH_ROOT`; the author's primary checkout holds untracked private-skill
symlinks into `~/.config/harness/private/`, so manifest entries resolved into
the real home on one side and the tmp home on the other: 13 failures there,
green in CI and every fresh worktree. Fix: `tests/tracked_tree.py` copies the
tracked files once per session and the tests run from that copy. Positive
control: plant untracked links in a scratch clone; old tests fail, new pass.
Several other tests still fake `HOME` while loading code from the real checkout
(`test_perch_*`, `test_skill_seam`, `test_projection_validator`, …); they pass
today, so they were reported, not ticketed.
