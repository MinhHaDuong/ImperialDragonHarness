# Adapter operations runbook

Run from the harness checkout and retain its absolute path for commands
that change directory:

```bash
IDH_ROOT="$(pwd -P)"
```

## Install and verify

```bash
"$IDH_ROOT/bin/idh" install
"$IDH_ROOT/bin/idh" check
"$IDH_ROOT/bin/idh" status
```

Host installation registers individual rules, skills, instructions and
launchers, links the Claude adapter plugin (the single Claude hook source,
0887), merges the Codex hooks into its configuration, and links
the Pi guard extension. Runtime profiles remain independently owned.
It also edits the shell loader: review these host-wide actions before
running it. Scheduling is left to the host. There is no dry run or runtime selector.
Same-name resource conflicts are refused; unrelated content is preserved.

The measured runtime pilot covers perch, healthcheck and the dirty-reset
guard. Installing or discovering the whole catalog does not certify every
skill's workflow. The legacy helper handoff 1002 is WONTDO. Project-local v8
memory is tracked by 0911/0917, the pilot 0920, and integration 0988 after the
pilot.

Before interactive launches, the shell wrappers validate the selected
runtime's registrations. Broken required resources refuse the launch and
recommend `idh install`. `IDH_SKIP_VALIDATE=1` is an explicit, logged bypass.

## Guard smoke and trust

Use a disposable repository with a committed file, then edit that file.
Keep the absolute checkout path when changing into it:

```bash
cd /some/disposable-dirty-repo
echo '{"tool_input":{"command":"git reset --hard"},"cwd":"'$PWD'"}' |
  bash "$IDH_ROOT/scripts/guard-destructive-bash.sh"
echo "exit=$?"  # expect BLOCKED and exit=2; a clean control exits=0
```

Inside Codex, run `/hooks`, review and trust the installed definition.
Untrusted or modified definitions are silently skipped in headless use.
Re-trust whenever the definition changes, then probe the dirty control again.
Invocation-local trust bypass is smoke-test evidence only, not persistent
deployment. Claude/Codex/Pi guard controls recorded for PR1091 used temporary
profiles and did not deploy into the user's live profiles.

## Move the checkout

From the permanent new checkout:

```bash
./bin/idh install
./bin/idh check
```

Explicit reinstallation atomically refreshes links whose text still matches
the installer receipt at
`${XDG_STATE_HOME:-$HOME/.local/state}/idh/links.json`.
Modified or foreign links are refused. If a refused link needs repair,
inspect its ownership and resolve that single conflict explicitly.
Do not remove a runtime configuration file to repair registration:
hook JSON is normally a regular user-owned file containing merged hooks.

The older skills-only `idh relocate skill <names> --from <old-path>` command
is for links made by that installer. It neither owns nor replaces runtime
settings. Re-run host install afterward and refresh Codex trust if needed.

## Remove registrations

`idh uninstall skill <names>` removes only the skill installer's managed
links, never canonical skills or unmanaged directories. There is no host
uninstall command.

For hook removal, run `bin/idh install`: it removes exactly the harness's
own hook commands from the live Claude settings (the plugin is the single
Claude hook source since 0887) and leaves operator hooks, events, metadata
and permissions alone — back up first if you want a manual record. For
Codex, back up the live JSON and edit only the exact harness hook blocks
identified by the checkout template. Remove installer-owned environment
or status-line entries only after confirming their exact values. Never
delete `~/.codex/hooks.json` merely because status says `ok`: that proves
registration is present, not exclusive ownership.

For individual resource symlinks (including the Pi extension), inspect the
link text and its receipt before removing the verified link. Leave regular
files, canonical resources and foreign replacements alone.
Remove or disable the loader block before intentionally removing required
registrations; otherwise its launch checks correctly refuse the runtime.

Other host integration is removed explicitly:

- Delete only the marked Imperial Dragon Harness loader block in `~/.bashrc`.
- Inspect installer backups before discarding them; they can contain private
  shell configuration.

## Audit and recovery

`./bin/mammoth-audit` reports candidates without removing skills.
The harness installs no scheduler; arrange recurring runs externally.
An interrupted install can leave partial registration; rerun install and
check from the current checkout. Only unchanged receipt-owned links are
refreshed, and runtime configuration changes are backed up.

## Limits

- The dirty-reset guard is a guardrail, not a Git-mutation sandbox. Unparseable
  payloads, missing Python, nested shell commands and hook timeouts can fail open.
- Codex trust covers the hook definition, not the invoked script's integrity.
  The checkout and CI own that integrity; a changed definition needs renewed trust.
- Pi preserves the guard's fail-open behavior if its script or Python is missing.
- Full runtime parity and native packaging remain separate work. Vibe has only
  a version/discovery probe, not an enforcing registration slice.
