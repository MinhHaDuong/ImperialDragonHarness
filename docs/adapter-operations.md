# Adapter operations runbook

Operator commands for the IDH pilot surface on Claude Code, Codex and Pi
(tickets 0802, 0803, 0809, 0810). Mistral Vibe is a probed fourth target
with no porting slice yet; nothing here claims Vibe behavior.

The pilot creates exactly four things on a machine, in two planes:

| Plane | Paths | Managed by |
|---|---|---|
| skills | `~/.agents/skills/{perch,healthcheck}` (+ a Claude Code projection when the repo is not `~/.claude`) | `bin/idh` |
| wirings | `~/.codex/hooks.json`, `~/.pi/agent/extensions/idh-guard.ts` | `adapters/install-wirings.sh` |

Both managers share one doctrine: a target that already resolves to the
canonical file is success ("already discoverable"); anything else at the
target is refused — never overwritten, never deleted. Interrupted installs
are recovered by re-running the same command; installs are idempotent.

## Probe versions

```bash
claude --version && codex --version && pi --version && vibe --version
./bin/idh check harness claude   # also: codex, pi
```

Support is a floor plus a probe, never an allowlist. An unreadable version
refuses rather than passes.

## Install (fresh machine)

```bash
cd ~/.claude            # the harness checkout
./bin/idh install skill perch healthcheck
./adapters/install-wirings.sh install
```

Preflight the guard itself before trusting the wiring (a missing or
broken script fails open, so verify it fires):

```bash
cd /some/dirty-repo
echo '{"tool_input":{"command":"git reset --hard"},"cwd":"'$PWD'"}'   | bash ~/.claude/scripts/guard-destructive-bash.sh; echo "exit=$?"
# expect: the BLOCKED message and exit=2
```

Then, once, inside Codex: run `/hooks`, review and **trust** the guard
hook. Codex skips non-managed hooks until their exact definition is
trusted; an untrusted guard silently does not run, so trust is part of the
enforcing boundary, not a formality.

## Verify

```bash
./bin/idh status skill perch --to codex
./adapters/install-wirings.sh status
```

## Uninstall (exact removal)

```bash
./adapters/install-wirings.sh uninstall
./bin/idh uninstall skill perch healthcheck
```

Removal takes back exactly what install created and prunes only the
directories it emptied. Unmanaged files — an existing `~/.codex/hooks.json`
of your own, anything else living in `~/.agents/skills` — survive
untouched; the exit code reports any refusal.

## Move the checkout

```bash
# from the NEW checkout:
./bin/idh relocate skill perch healthcheck --from /old/absolute/path
./adapters/install-wirings.sh uninstall   # refuses the now-foreign links
rm ~/.codex/hooks.json ~/.pi/agent/extensions/idh-guard.ts   # only the two
# foreign links, after the refusal confirmed they are ours
./adapters/install-wirings.sh install
```

Skills links are retargeted atomically by `relocate`; wiring links are
dangling after a move and are refused (never silently retargeted), so the
honest sequence is uninstall-refuse, remove the two known links, reinstall.
The `~/.claude` → `~/.idh` relocation (ticket 0978) additionally owns
repointing the config-plane guard paths in `settings.shared.json` and
`codex/hooks.json` (`$HOME/.claude/scripts/...`).

## Interrupted run / recovery

Any interruption leaves a partial surface at worst — every command is
idempotent, refuses instead of overwriting, and reports per target. Recover
by re-running install. A dangling or foreign symlink is reported as such;
nothing retargets it behind your back.

## Limits, stated rather than papered over

- Codex skips untrusted hooks (hash-recorded trust via `/hooks`) and some
  specialized tool paths opt out of the hook path: the guard is a
  guardrail, not a complete boundary.
- Codex hook trust authenticates the **hook definition**, not the script it
  invokes: a changed `guard-destructive-bash.sh` does not untrust the hook.
  The script's integrity is the harness checkout's business (git + CI).
  Trust is recorded as `[hooks.state."<hooks.json>:pre_tool_use:0:0"]
  trusted_hash` in `~/.codex/config.toml` — never through the symlink into
  the repo file (measured 2026-09-28). **A stale hash (status Modified) is
  silently skipped in `codex exec`** — observed live: the guard did not fire
  until the trust was re-recorded. After a recorded trust, `codex exec`
  without any bypass flag blocks a dirty reset (verified on the fixture).
  Re-trust after touching `hooks.json`, and preflight the guard before
  relying on it.
- **Hook timeout is fail-open** (measured 2026-09-28: a hook sleeping past
  its timeout does not block the command). The wiring budget is 8s; the
  guard's per-`git` subprocess timeout is 4s, so one slow repo check fits
  and a pathological multi-target line can still exceed the budget and
  let the command through. The guard has no internal global deadline —
  a residual risk recorded here rather than fixed in this slice.
- The guard is fail-open on: an unparseable payload, missing `python3`,
  and commands nested in `bash -c`/`eval`. A seatbelt for the common
  linear shape, not a sandbox.
- The Pi adapter carries the guard's fail-open doctrine: if the guard
  script or python3 is missing, Pi's bash calls are allowed, not bricked.
- No full-harness parity is claimed: skills are read-in-place Markdown,
  one enforcing guard is wired, everything else (hooks, permissions,
  settings, rules) remains Claude-native.
- Mistral Vibe: version probe and skills-root compatibility only.
