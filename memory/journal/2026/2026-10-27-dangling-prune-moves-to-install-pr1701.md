# Dangling-skill prune moves into the plain idh install — PR 1701 (2026-10-27)

Context: same session as PR 1690, Opus 5.5 in Claude Code on padme. The author listed three cleanups: the
`docs/idh-install-strategy.md` rerun summary omitting retirement, the overlap between `perch.prune_dangling` and
`lifecycle.retire_stale`, and the triple `~/.local/bin` on PATH.

Events:

- First head deleted `perch.prune_dangling` and its tests outright. Gaze round 1 (all Anthropic seats) reproduced the
  gap: `install_links` records only links it creates, so a pre-receipt or `idh install skill` link outlives its skill,
  and `idh uninstall skill` refuses a skill that left the repo.
- The orchestrator added `lifecycle.prune_unrecorded` (dangling, into `<checkout>/skills/<same name>`, not in the
  receipt). Round 2: it ignored the receipt and deleted a hand-edited receipt link (two seats reproduced). Round 3:
  the receipt was matched by path text, so a HOME alias defeated it (red team, reproduced by the gaze orchestrator).
- After three FINDINGS rounds the orchestrator asked fable, offering A (fix again), B (doc only) and C (move the
  shape-based `prune_dangling` unchanged into the plain install). Fable picked C and named D (adopt existing links
  into the receipt); D conflicts with `test_preexisting_hook_link_is_not_claimed_by_install`. The orchestrator took
  C without asking the author.
- The rework restored the branch's touched files to `origin/main` content and moved the function. Gaze on it found one
  regression against the "unchanged" claim: perch's `_unlink` treated FileNotFoundError as success, the moved code
  did not (`missing_ok=True` restores it, test pinned). The next round's only finding was the stale PR title.
  `/verify-gate` APPROVED round 1; merged at afc36395. A plain `idh install` on padme then linked the new
  `harness-doctor` skill and pruned nothing; `idh check` exit 0.
- `make check` failed once with `test_local_ci_parallel.py::test_pool_does_not_wait_for_the_callers_other_background_jobs`
  under suite load; it passed alone on the branch and on clean `origin/main`, and the rerun was green.
- PATH: `~/.local/bin` appeared three times. `~/.bashrc:1` (unconditional prepend) first appears between the
  2026-09-02 and 2026-09-03 `.bashrc` backups, together with a `zotero` alias; `~/.profile:24-26` (Ubuntu default)
  prepends unconditionally; the systemd user manager's environment already held two copies. uv's `~/.local/bin/env`
  is idempotent. The auto-mode classifier denied the orchestrator's dotfile edit; the author applied it by hand
  (deleted `~/.bashrc:1`; guarded the `~/.profile` block). In the next terminal the count was 2; the session
  environment from the earlier login still holds both copies.
- Attribution capture: the PR body block again carried `finding: blocking`, `independence=other-family`, a
  `finding: nofollow`, a duplicate anchor within one attempt and a finding anchored on `PR title`. The record was
  normalized (`verifiable`, `cross-family`, `consider`), the duplicate dropped, and the title finding dropped as
  having no repository anchor.

Outcome: PR 1701 merged; `prune_dangling` runs in every plain `idh install` over `~/.claude/skills` and
`~/.agents/skills`, perch no longer has it, and the install doc names retirement and the prune.

References: PR 1701 (gaze results, verdict comment 6437219052); PR 1690;
`memory/journal/2026/2026-10-27-review-attribution-pr1701.md`.
