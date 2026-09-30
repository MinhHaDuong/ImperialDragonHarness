# Move the harness to `~/.idh`

Run this once from a plain terminal when Claude, Codex and Pi are closed. The
checkout is currently `~/.claude`; `~/.idh` points to it. After the move,
`~/.claude` remains Claude Code's native state directory with links to the
harness entries it reads. Use the reviewed `t0986-step1` branch for the path
changes. The memory and permission behavior was probed on Claude Code 2.1.285;
repeat those probes if the installed version changes.

1. Confirm `main` is clean, `t0986-step1` includes it, no worktree is in use,
   and no timer service is running. Record which of `claude-refresh.timer`,
   `idh-mammoth-audit.timer`, and `claude-telemetry-prune.timer` are active.
   Stop those timers. Check free space, then take and list a private snapshot:

   ```bash
   umask 077
   snap="$HOME/idh-cutover-$(date +%Y%m%dT%H%M).tar"
   tar -C "$HOME" --one-file-system -cpf "$snap" .claude .claude.json .idh
   tar -tf "$snap" >/dev/null
   ```

2. Fast-forward `main` to the reviewed preparation branch and run `idh check`
   while the old layout is still intact. Then move the checkout:

   ```bash
   git -C "$HOME/.claude" merge --ff-only t0986-step1
   rm "$HOME/.idh"
   mv "$HOME/.claude" "$HOME/.idh"
   mkdir "$HOME/.claude"
   chmod --reference="$HOME/.idh" "$HOME/.claude"
   ```

3. Move Claude Code's native state back into `~/.claude`. Compare every
   top-level entry with `git -C ~/.idh ls-files`; classify unfamiliar entries
   before moving them. Keep the checkout, `.git`, `.env`, and its worktrees in
   `~/.idh`. Move `projects/` back to `~/.claude/projects/`. Link `CLAUDE.md`,
   `RTK.md`, `rules`, `agents`, `commands`, and `tickets` from
   `~/.claude` to `~/.idh`; `idh install` links individual skills. For each
   tracked `projects/<slug>/memory`, move its
   directory into `~/.idh/projects/<slug>/memory` and link it back from the
   native `projects/` directory. Rename only the exact harness slug from
   `-home-<user>--claude` to `-home-<user>--idh`, including its worktree slugs.

4. Repair Git worktrees and set `core.hooksPath` to `~/.idh/hooks`. Re-key only
   `~/.claude.json` project paths for the checkout and moved worktree directories;
   leave native `~/.claude/projects/` keys alone. Apply the tracked hook and
   permission changes to the live `~/.claude/settings.json`, keeping its other
   settings. Refresh the shell loader with `idh install`. Re-trust the changed
   Codex hook definition through `/hooks`.

5. Run `idh check`, `make check`, and one fresh launch for each runtime. Confirm
   Claude instructions and memory load and that the Codex dirty-reset guard
   blocks. Restore and recheck one temporarily broken projection link to prove
   a missing link refuses a launch. Resume only the timers that were active.
   Update the second host in its own quiet window.

If the move cannot be completed, stop the timers and restore the snapshot from
a plain terminal. Keep the snapshot until the live checks pass; it contains
credentials. The abandoned scripted attempt's useful findings are in ticket
0985: rename exact slugs, avoid re-keying native project paths, and keep
`XDG_STATE_HOME` and `XDG_CONFIG_HOME` out of disposable HOME probes.
