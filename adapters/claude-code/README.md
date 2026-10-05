# Claude Code adapter

The hook wiring of the Imperial Dragon Harness, packaged as a Claude Code
skills-directory plugin. Ticket 0887; the instruction that argues for it, with
the measurements, is `tickets/closed/0887-*.erg`.

## The switch

Nothing loads until the symlink `~/.claude/skills/claude-code ->
<checkout>/adapters/claude-code` exists. It is created by
`scripts/adapter-claude-code-activate.sh`, which refuses to close the switch
while the live settings still carry a hooks block, or by `bin/idh install`,
which removes those stale hooks in the same pass. If the settings step then
refuses (unreadable live file, unrepairable state), the removal runbook is
`idh check`: it names the double-fire until the stale hooks are gone. Since the activation (2026-10-05) this plugin is the single hook
source — `settings.shared.json` carries no `hooks` key at all, ratcheted by
`tests/test_claude_code_adapter.py`.

## Why a plugin at all

Measured on Claude Code 2.1.266 and re-measured on 2.1.289
(`scripts/probe-plugin-hook-loading.sh`):

- a plugin under `$HOME/.claude/skills/<name>/` loads with no marketplace, no
  install step, no `--plugin-dir` flag and no trust dialog;
- it loads the same way through a symlink, which is what frees this directory
  from having to live under `skills/`;
- project scope (`<repo>/.claude/skills/`) does *not* load under `claude -p`;
- a personal-scope plugin reached through a *broken* symlink does not load —
  case D, the negative control that makes the link a real switch (2.1.289).

Hooks fail **open** — absent, the guards silently do not run — so they belong
in a layer git owns and the CLI never writes. Permissions fail **closed** and a
plugin cannot carry them anyway; they stay in `settings.shared.json` alongside
`env` and `statusLine`, the surfaces the plugin cannot carry.

## Layout

    .claude-plugin/plugin.json   manifest
    hooks/hooks.json             the single hook source — maintained here
    bin/idh-hook                 launcher: resolves the harness root, runs a scripts/ hook

`hooks.json` was generated from `settings.shared.json` while both files carried
the hooks (the drift check `make check-adapter-hooks` held them together); at
activation the settings dropped their `hooks` key and the generator was
retired. Hooks are maintained here now — and nowhere else, which is the point:
one source, no drift possible.

`bin/idh-hook` exists because `${CLAUDE_PLUGIN_ROOT}` holds the path the plugin
was *discovered* at, not its resolved location: a symlinked plugin gets the
symlink's path, so a fixed number of `..` is only correct while link and target
sit at the same depth. On the guard layer a wrong resolution fails open in
silence. The launcher resolves its own real location instead, and a missing
target exits 1 — loud, and never 2, which is Claude Code's "deny the call".

## Activation and rollback

    scripts/adapter-claude-code-activate.sh --status
    scripts/adapter-claude-code-activate.sh            # after clearing the live hooks
    scripts/adapter-claude-code-activate.sh --revert

Activating refuses while the live settings carry a hooks block — both sources
would fire every guard twice. Reverting removes the symlink and, because the
canonical settings carry no hooks, says loudly that no guard will fire until a
hooks block is restored to the live settings; the block lives in git history,
in the commit that removed it. Confirm a guard actually fires in a new session
after activating; reading a configuration file is not evidence that it does.
