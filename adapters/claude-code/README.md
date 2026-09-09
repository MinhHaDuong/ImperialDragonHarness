# Claude Code adapter

The hook wiring of the Imperial Dragon Harness, packaged as a Claude Code
skills-directory plugin. Ticket 0887; the instruction that argues for it, with
the measurements, is `tickets/0887-*.erg`.

## It ships inert

Nothing here loads until `scripts/adapter-claude-code-activate.sh` creates the
symlink `skills/claude-code -> ../adapters/claude-code`. That is deliberate.
On the reference machine the harness repository *is* `~/.claude`, so a plugin
directory reachable under `skills/` is auto-discovered on the next session —
while the live `settings.json` still carries its own copy of the same hooks.
Both firing means every guard runs twice. The symlink is the switch, and the
switch refuses to close while the live file would double-fire.

## Why a plugin at all

Measured on Claude Code 2.1.266 (`scripts/probe-plugin-hook-loading.sh`):

- a plugin under `$HOME/.claude/skills/<name>/` loads with no marketplace, no
  install step, no `--plugin-dir` flag and no trust dialog;
- it loads the same way through a symlink, which is what frees this directory
  from having to live under `skills/`;
- project scope (`<repo>/.claude/skills/`) does *not* load under `claude -p`.

Hooks fail **open** — absent, the guards silently do not run — so they belong
in a layer git owns and the CLI never writes. Permissions fail **closed** and a
plugin cannot carry them anyway; they stay in `settings.shared.json`, which
ticket 0886 reconciles with the live file.

## Layout

    .claude-plugin/plugin.json   manifest
    hooks/hooks.json             DERIVED — do not hand-edit
    bin/idh-hook                 launcher: resolves the harness root, runs a scripts/ hook

`hooks.json` is generated from `settings.shared.json` by
`scripts/gen-claude-code-adapter-hooks.py`; `make adapter-hooks` regenerates it
and `make check` fails when it is stale. While both files carry the hooks, a
hook added to one and not the other is precisely the silent gap this adapter
exists to close, so neither is allowed to drift from the other.

`bin/idh-hook` exists because `${CLAUDE_PLUGIN_ROOT}` holds the path the plugin
was *discovered* at, not its resolved location: a symlinked plugin gets the
symlink's path, so a fixed number of `..` is only correct while link and target
sit at the same depth. On the guard layer a wrong resolution fails open in
silence. The launcher resolves its own real location instead, and a missing
target exits 1 — loud, and never 2, which is Claude Code's "deny the call".

## Cut-over, and back

    scripts/adapter-claude-code-activate.sh --status
    scripts/adapter-claude-code-activate.sh            # after clearing the live hooks
    scripts/adapter-claude-code-activate.sh --revert

Reverting is removing one symlink. Confirm a guard actually fires in a new
session; reading a configuration file is not evidence that it does.
