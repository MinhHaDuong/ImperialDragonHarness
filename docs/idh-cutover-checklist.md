# The `.idh` cutover: checklist for the live window

Ticket 0986 runs this; ticket 0985 rehearsed it. The mechanism is
`idh relocate harness` (`adapters/cutover.py`), with the classification it acts
on in `adapters/cutover-layout.json`. The rehearsal is
`scripts/rehearse-cutover.py`, and the crash-point tests are in
`tests/test_idh_cutover.py`.

## What the command does

Before the window, the checkout is `~/.claude` and `~/.idh` is a link to it.
Afterwards the checkout is `~/.idh`, and `~/.claude` is a real directory that
holds Claude Code's own state plus one link per harness entry the runtime reads
(`CLAUDE.md`, `RTK.md`, `rules`, `skills`, `agents`, `commands`, `tickets`).
In `projects/`, each tracked `<slug>/memory` stays in the checkout and gets a
link back from the native root. Every other file under `projects/` moves to the
native root. `projects/<slug(~/.claude)>` and its worktree slugs are renamed to
`<slug(~/.idh)>`, since Claude Code keys memory by the resolved path (0984). The
path-keyed `projects` entries of `~/.claude.json` are re-keyed the same way.
`adapters/projections.json` is rewritten for the per-entry layout. `idh install`
then creates the links and `idh check` verifies them. Worktrees are repaired, and
the active timers among `claude-refresh`, `claude-telemetry-prune` and
`idh-mammoth-audit` are paused for the move, then resumed.

The plan and the pre-state (manifest and `~/.claude.json` bytes, active timers,
the `~/.idh` link text) are journalled in `~/.local/state/idh/cutover/` before
anything moves. Both directions are idempotent, and a crash at any step is
finished by rerunning either direction.

## Preconditions (quiet window)

- [ ] No Claude, Codex or Pi session is running on this host, this one included:
      run everything below from a plain terminal. `pgrep -a -x claude; pgrep -a -x codex; pgrep -a -x pi`
      prints nothing.
- [ ] No open PR still needs its worktree. Worktrees move with the checkout and are
      repaired, but a session inside one would lose its cwd.
- [ ] `git -C ~/.claude status --porcelain` prints nothing, and session memory is
      committed (0988). The command refuses a dirty tree anyway.
- [ ] A filesystem snapshot of `$HOME`, or at least a copy of `~/.claude.json`,
      exists and has been checked for readability.
- [ ] `idh install` then `idh check` pass today. Neither has run for real before
      (STATE, 2026-09-29). Every manifest link must be spelled through `~/.idh`,
      because the command refuses a declared link whose text names `~/.claude/…`.
- [ ] Nothing outside the manifest links into the old root:
      `find ~ -xdev -path ~/.claude -prune -o -lname '*/.claude/*' -print` prints
      only paths you have decided about. The preflight checks manifest entries only.
- [ ] Every top-level name in `~/.claude` is tracked, `keep` or `native` in
      `adapters/cutover-layout.json`; the command refuses the rest by name. Decide
      about the writers of the four names classified native by default:
      `.last-pull`, `beat-log.jsonl`, `nightbeat-supervisor-journal.jsonl` and
      `gh-pr-status-cache.json`. A file a script writes as `~/.idh/<name>` belongs
      in `keep`.
- [ ] Run the rehearsal the same day, against today's census:
      `python3 ~/.claude/scripts/rehearse-cutover.py --session` ends in
      `rehearsal: PASS`. The census is read from the live native root as names only.
- [ ] `claude --version` is still 2.1.284, or `scripts/probe-memory-symlink.py` has
      been re-run on the new version (0984).
- [ ] The 0986 permission-through-symlink probe has been recorded.

## The move

1. `~/.idh/bin/idh relocate harness --live`
   - Without `--live` it refuses the real HOME, and with it outside the real HOME.
   - It prints `paused:`, `moved:`, `split:`, `rewrote:`, `re-keyed:`,
     `repaired:`, then the output of `idh install` and `idh check`, then `resumed:`.
   - If `idh install` or `idh check` fails, timers stay paused and the command
     exits 1. Repair and rerun, or roll back.
2. Before the first launch, `python3 ~/.idh/scripts/validate-projections.py claude`
   exits 0 (likewise `codex` and `pi`). A launch through the shell wrappers runs
   the same check.
3. Positive controls (0986): a fresh Claude, Codex and Pi session each load hooks,
   skills, instructions and memory. Negative control: break one link, and the
   launch refuses with the culprit named.
4. `git -C ~/.idh status` shows exactly two changes: `adapters/projections.json`
   and the renamed `projects/<slug>/memory`. Commit them on a branch and open a PR
   only after the controls pass.
5. `systemctl --user list-timers` shows the paused timers back.
6. The rest of 0986: the `ln -sfn` repair texts in `scripts/shell-init.sh` and
   `scripts/bashrc-loader.sh` (then `idh install` refreshes the `~/.bashrc`
   block), the dual permission aliases, Codex `hooks.json` with its `/hooks`
   re-trust and a fresh `codex exec` probe, and the README lines. On padme, do it
   or record the deferral.

## Rollback

- `~/.idh/bin/idh relocate harness --rollback --live`. If a crash left no
  `~/.idh` (it fell between dropping the link and the move), run
  `python3 ~/.claude/bin/idh relocate harness --rollback --live`.
- The manifest and `~/.claude.json` get their pre-cutover bytes back when nothing
  has touched them since the cutover. If a session rewrote `~/.claude.json`, only
  the re-keyed entries are restored, and the command says so.
- Native files created since the cutover move back into the checkout. A new
  top-level name that `cutover-layout.json` does not classify stops the rollback
  with its name (the rehearsal found `policy-limits.json*` and
  `remote-settings.json` this way). Classify it, then rerun.
- If step 4's commit has landed, revert it after the rollback.
- The journal is kept as `~/.local/state/idh/cutover.rolled-back-<time>`.

## Known limits

- The slug rename works by prefix: every slug equal to `slug(~/.claude)` or
  starting with it plus `-` is renamed. That includes the rare session started
  under a native directory, such as `~/.claude/projects/x`.
- Only the `projects` keys of `~/.claude.json` are re-keyed. A key under a native
  entry (such as `~/.claude/projects/...`) is left alone.
- The native root keeps no link to `scripts/`, `bin/` or `adapters/`, so a
  residual `~/.claude/scripts/...` spelling (0986's ratchet list) breaks at the
  cutover. It is not silently kept alive.
