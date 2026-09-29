# The `.idh` cutover: runbook for the live window

Ticket 0986 follows this runbook by hand in one quiet window. Rollback means
restoring the snapshot taken in step 2. There is no cutover script: the author
judged a resumable state machine disproportionate for a one-off move
(2026-09-29, PR #1067). The findings of that attempt appear below as warnings.

**Before:** the checkout is `~/.claude`, and `~/.idh` is a link to it.
**After:** the checkout is `~/.idh`. `~/.claude` is a real directory that holds
Claude Code's own state, plus one link per harness entry the runtime reads.

Every command runs from a plain terminal, never from inside Claude, Codex or Pi.
`U=$HOME` stands for the account's home throughout.

## Steps

1. **Preconditions.**
   - The window is quiet: `pgrep -a -x claude; pgrep -a -x codex; pgrep -a -x pi` prints nothing.
   - The tree is clean: `git -C ~/.claude status --porcelain` prints nothing, and session memory is committed (0988).
   - No open PR still needs its worktree mid-flight.
   - `claude --version` is still 2.1.284, or `scripts/probe-memory-symlink.py` has been re-run (0984).
   - The 0986 permission-through-symlink probe is recorded.
   - `idh install && idh check` pass. This will be the first real run on the host.

2. **Snapshot. This is the rollback.**
   ```bash
   snap=~/idh-cutover-$(date +%Y%m%dT%H%M).tar
   tar -C ~ --one-file-system -cpf "$snap" .claude .claude.json .idh && tar -tf "$snap" | wc -l
   ```
   Check the free space first, because `projects/` alone is several GiB. The
   snapshot holds credentials and `~/.claude.json`: keep it mode 600, and delete it
   once the window has been accepted.

3. **Pause the timers.**
   ```bash
   systemctl --user stop claude-refresh.timer idh-mammoth-audit.timer claude-telemetry-prune.timer
   ```
   Note which of them were active (`systemctl --user list-timers --all`). A
   `.service` still running from one of them must finish first.

4. **Take a worktree census.**
   `git -C ~/.claude worktree list --porcelain` and `git -C ~/.claude worktree prune --dry-run -v`.
   A registration whose path is gone, or whose path now holds an ordinary clone
   (its `.git` is a directory, not a file), makes `git worktree repair` fail at
   step 7. Remove such registrations now with `git worktree prune` or
   `git worktree remove`.

5. **Move the checkout, then rebuild the native root.**
   ```bash
   rm ~/.idh && mv ~/.claude ~/.idh && mkdir ~/.claude && chmod --reference=~/.idh ~/.claude
   ```
   - What stays in `~/.idh`: every tracked top-level entry (`git -C ~/.idh ls-files | cut -d/ -f1 | sort -u`), plus `.git .claude .env .worktrees worktrees .agents .codex .pytest_cache .ruff_cache`.
     - `.env` stays because `UV_ENV_FILE` names it as `~/.idh/.env`.
   - What moves back with `mv ~/.idh/<name> ~/.claude/`: every other top-level name. These are Claude Code's own state (`.credentials.json`, `history.jsonl`, `settings.json`, `sessions`, `plugins`, `backups` and the like).
     - List the names and read the list before moving anything. An unfamiliar name is a question, not a default.
     - Decide first about `.last-pull`, `beat-log.jsonl`, `nightbeat-supervisor-journal.jsonl` and `gh-pr-status-cache.json`: find who writes them and under which path.
   - Then link the harness entries: `for n in CLAUDE.md RTK.md rules skills agents commands tickets; do ln -s ~/.idh/$n ~/.claude/$n; done`.
     - `CLAUDE.md` imports `RTK.md` and `tickets/AGENTS.md` by relative path.
     - No link is made for `scripts`, `bin` or `adapters`, so a residual `~/.claude/scripts/...` spelling breaks here, visibly (0986's ratchet list).

6. **Split `projects/` and rename the harness slug.**
   - `mv ~/.idh/projects ~/.claude/projects`.
   - Rename the harness's own slug. `slug(path)` turns every non-alphanumeric character into `-`. Rename exactly `-home-<user>--claude` to `-home-<user>--idh`, and each harness worktree slug `-home-<user>--claude--claude-worktrees-<name>` to `-home-<user>--idh--claude-worktrees-<name>`.
   - For every `~/.claude/projects/<slug>/memory` that git tracks (`git -C ~/.idh ls-tree -d --name-only HEAD projects/` before the move), bring it back into the checkout and link it:
     ```bash
     mkdir -p ~/.idh/projects/<slug>
     mv ~/.claude/projects/<slug>/memory ~/.idh/projects/<slug>/memory
     ln -s ~/.idh/projects/<slug>/memory ~/.claude/projects/<slug>/memory
     ```
   - Memory is followed through the link, and keyed by the resolved path (0984).

7. **Repair the worktrees.** `git -C ~/.idh worktree repair <each worktree path>`.
   - Give each path as it is now: a path under `~/.claude/.claude/worktrees/` becomes `~/.idh/.claude/worktrees/`.
   - `git worktree list` must show nothing prunable.

8. **Re-key `~/.claude.json`.** Only the `projects` keys change, and only for paths that moved with the checkout. The snippet prints the mapping. Read it, then rerun with `APPLY=1` to write:
   ```bash
   python3 - ${APPLY:+--apply} <<'EOF'
   import json, os, sys
   home = os.environ["HOME"]; old, new = f"{home}/.claude", f"{home}/.idh"
   moved = {".claude", ".worktrees", "worktrees"}  # checkout subtrees that hold session cwds
   p = f"{home}/.claude.json"; d = json.load(open(p)); keys = d["projects"]
   m = {k: new + k[len(old):] for k in keys
        if k == old or (k.startswith(old + "/") and k[len(old) + 1:].split("/")[0] in moved)}
   assert not set(m.values()) & set(keys), "a new key already exists: merge by hand"
   for k, v in m.items(): print(k, "->", v)
   if "--apply" in sys.argv:
       d["projects"] = {m.get(k, k): v for k, v in keys.items()}
       tmp = p + ".tmp"; open(tmp, "w").write(json.dumps(d, indent=2) + "\n")
       os.chmod(tmp, 0o600); os.replace(tmp, p)
   EOF
   ```

9. **Manifest and checks.**
   - Commit the rewritten `adapters/projections.json`, prepared on a branch before the window. It replaces the whole-root `~/.claude` entry with one entry per link from steps 5 and 6.
   - The unrewritten manifest must refuse: `validate-projections.py claude` names `~/.claude` as FOREIGN. That refusal is the expected control.
   - Then `idh check`, and `python3 ~/.idh/scripts/validate-projections.py claude|codex|pi`, pass before the first launch.
   - Positive control: a fresh Claude, Codex and Pi session each load hooks, skills, instructions and memory.
   - Negative control: break one link, and the launch refuses, naming it.

10. **Resume the timers** that were active in step 3 (`systemctl --user start …`), then finish 0986's remaining criteria:
    - the `ln -sfn` repair texts in `scripts/shell-init.sh`, `scripts/bashrc-loader.sh` and the three hooks of `settings.shared.json` and the live `settings.json`;
    - the dual permission aliases;
    - Codex `hooks.json` with its `/hooks` re-trust and a fresh `codex exec` probe;
    - the README lines;
    - padme, or its recorded deferral.

## Rollback

Stop the three timers, then run:

```bash
mv ~/.idh ~/.idh.failed && mv ~/.claude ~/.claude.failed
tar -C ~ -xpf "$snap"
```

Then resume the timers, and run `idh check` from `~/.claude`. Delete the
`.failed` copies once the restored layout is verified. Anything written after
the snapshot is lost, which is why the window must be quiet.

## Warnings carried from the abandoned cutover script (PR #1067 review)

- **Slug look-alikes.** Slugs map `/`, `.` and `-` alike. A prefix rule such as "every slug starting with `-home-<user>--claude`" would also rename the store of `~/.claude-backup` (`-home-<user>--claude-backup`). Rename exact names only.
- **`projects/` is not native but mixed.** A rule of the form "re-key every `~/.claude.json` key under the checkout except native entries" also rewrites keys under `~/.claude/projects/...`. The snippet in step 8 therefore re-keys only an explicit set of moved subtrees.
- **`XDG_STATE_HOME` and `XDG_CONFIG_HOME`.** Any helper run in the window or in a rehearsal must derive its paths from `HOME`. A shell that exports these variables otherwise sends state to the live directories, even under a disposable HOME.
- **`git status` after the memory rename shows three entries, not two**: the deletion under the old slug, the untracked directory under the new slug, and the modified manifest. Commit them together.
- **A rollback must refuse before it changes anything.** If you script any part of this, run the checks before the first mutation, including stopping the timers.
