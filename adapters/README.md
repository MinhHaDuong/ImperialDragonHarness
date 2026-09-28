# adapters/

Native glue for harnesses other than the one this repository is checked out
into. Two unrelated things live here today:

- `claude-code/` — the harness's hook wiring as a Claude Code plugin (ticket
  0887). Its own README is next to it.
- `perch.py` and `bin/idh` — the multi-harness skill installer, generalized
  from the perch pilot (tickets 0802 and 0949).

## The perch pilot

One question, one skill: what do Claude Code, Codex and Pi actually require
around a shared skill body? `skills/perch/SKILL.md` is the smallest useful
answer — portable Markdown, read-only, no tools. It is hand-ported, not
generated: there is no skill IR here, no workflow DSL and no second copy of
the prose.

    bin/idh status skill perch             # where each harness looks
    bin/idh status skill perch roar --to codex
    bin/idh install skill perch            # all three harnesses
    bin/idh uninstall skill perch --to codex
    bin/idh relocate skill perch --from /old/checkout
    bin/idh check harness pi

The object argument names a directory under `skills/` whose `SKILL.md` has
matching `name` and a nonempty `description`. `status skill` lists every
canonical skill; `--to` narrows a command to one harness. Installation checks
all requested skills and harness versions before it creates any links. This
installer makes a skill discoverable; a skill's workflow still needs its own
portability review before installation. In particular, `roar` is used as the
second-object test but is not yet installed by this change.

### Where the skill goes

`$HOME/.agents/skills` is not a name this installer invents. It is the user-level
[Agent Skills](https://agentskills.io/specification) root that **Codex** and
**Pi** each document and each scan, and both follow a symlinked skill
directory — so `install skill perch` points it at `skills/perch` in this repository and
the body stays canonical and live. Editing the prose needs no build step and
no reinstall.

**Claude Code does not read that directory.** It scans `$HOME/.claude/skills`
only. On the reference machine the harness repository *is* `$HOME/.claude`, so
the canonical directory already is the one Claude Code discovers: `install
claude` reports it and creates nothing. Where the repository lives elsewhere,
it creates the link. Either way there is no second perch and nothing under
`skills/` changes, which is what makes removing the experiment a no-op for
Claude.

| | skills root | invocation |
|---|---|---|
| Claude Code | `$HOME/.claude/skills` | `/perch` |
| Codex | `$HOME/.agents/skills` | `$perch` |
| Pi | `$HOME/.agents/skills` | `/skill:perch` |

Run from a git worktree, `bin/idh status skill perch --to claude` reports `other-checkout`: the
canonical source is then the worktree's copy while the skills root still holds
the primary checkout's. Install refuses — pointing a live skills root at a
throwaway worktree is not an improvement — and says so in those words.

### Version support is a floor, not a list

`bin/idh check harness <name>` probes `<cli> --version` and compares it against
`minimum_version` in `pilot-support.json`. Above the floor is supported with no
edit to this repository; below it, unparseable, or a CLI that will not run at
all is **refused**, never silently accepted. The predecessor of this pilot
enumerated exact supported versions and had revoked support for two of its
three harnesses within nine days.

### The evidence inventory

`pilot-support.json` records what was actually proved, against
`pilot-support.schema.json`. Later slices append to the same arrays; ticket
0810 validates them. Four kinds of evidence, and the distinction is the point:

- `static-test` — a unit test in `tests/test_perch_pilot.py`.
- `local-probe` — the real CLI answered, offline and with **no model call**,
  under a negative control (clean profile: absent) and a positive one
  (installed: present). `tests/test_perch_discovery.py`; it skips when the CLI
  is not installed, so CI depends on no paid model and no mutable service.
- `documentation` — an upstream citation, for what only upstream can settle.
- `manual-smoke` — a live invocation, which costs a paid call on a
  third-party account. These sit at `result: "pending"` until the author runs
  them; no automated gate may claim them.

### Taking it back out

`bin/idh uninstall skill <name> --to <harness>` removes the managed link, then every
directory the removal left empty, up to and including the neutral home. A
neutral home holding anything else survives untouched, and the canonical skill
is never deleted. One caveat stated rather than papered over: nothing on disk
records which of those empty directories `install` created, so an empty one you
made by hand goes with them. Nothing under `skills/` is touched at any point,
so the pre-experiment Claude state is restored by construction.

`uninstall skill perch --to codex` and its Pi equivalent reach the same link — one neutral home,
one perch — so each names both harnesses in what it reports. A link left
dangling by moving the checkout is reported as `dangling` and removed on
request, rather than sitting there as an entry nothing can clean up.

### Moving the canonical checkout

After moving the repository, run `bin/idh relocate skill <names> --from
<old-absolute-checkout-path>` **from the permanent new checkout**. It checks
every requested target before writing, then atomically retargets only symlinks
whose text exactly names `<old>/skills/<name>`. A link from another checkout or
an unmanaged directory is refused. Codex and Pi share one target; the command
updates it once. Missing or already current links need no retargeting. Run
`bin/idh install skill <names>` afterward to create any missing Claude Code
projections. For the planned `~/.claude` → `~/.idh` move, the old Claude Code
directories will disappear with the checkout, while the neutral links remain
and need retargeting. No skill depends on `bin/idh` being on `PATH` at runtime:
helper commands resolve from the loaded skill file.

## The loaded-skill path seam (ticket 0803)

A script-backed skill needs one fact the body cannot know at authoring time:
where the harness is installed. The seam is the smallest contract that
resolves it, and it adds **no configuration field at all** — the runtime
already supplies the missing fact.

The contract, measured 2026-09-28 on all three pilot runtimes:

1. The runtime supplies the **absolute projected path** of the SKILL.md it
   loaded — Claude Code in its skill injection, Pi in the
   `<available_skills><location>` block of its preamble, Codex in its
   context skill list (Codex names the path but not the body, so the model
   reads the file itself: one extra tool call, same fact).
2. The body substitutes that path and derives the installation root with
   `cd -P` — through the projected symlink, two levels up:

   ```bash
   IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"
   ```

3. Bundled scripts live under `$IDH_ROOT/scripts/` and are read in place.
   No build step, no second copy, no `IDH_HOME` — zero of the three runtimes
   needed it, so per the 0803 gate it does not exist.

`healthcheck` is the proof slice: `bin/idh install skill healthcheck` makes
it discoverable everywhere, and its `project-state.py` probe runs through
Claude Code, Codex and Pi against the live repository. The deterministic
half is `tests/test_skill_seam.py`: the derivation is pinned against
space-containing roots, quote-containing roots, nested symlinks and
dangling projections (empty root plus stderr, never a plausible wrong
root), and a ratchet holds every seam-bearing body to the same
runtime-supplied-path derivation — one line for most skills, two for
`roar`, which needs its own skill directory first.

Adversarial-root findings worth knowing before you "simplify" the line:
the idiom's nested quoting survives a double quote in the installation
root (observed, pinned), and a dangling projection fails visibly at the
first downstream use rather than resolving to a wrong root. Both behaviors
are tests, not comments.

## The dirty-reset guard through three runtimes (ticket 0809)

One canonical decision — `scripts/guard-destructive-bash.sh` blocks
`git reset --hard` over uncommitted changes to tracked files, exit 2 with
the reason on stderr — carried by three thin wirings. The guard owns the
decision; adapters only normalize input and carry it. Portability did not
turn enforcement into advice:

- **Claude Code**: the existing `PreToolUse(Bash)` hook in
  `settings.shared.json`, unchanged.
- **Codex**: `codex/hooks.json` — Codex's PreToolUse payload carries
  `tool_input.command` and its block contract accepts exit 2 with the
  reason on stderr, so the same script runs byte-identical. Install:
  symlink to `~/.codex/hooks.json`, then review and trust once via
  `/hooks`. **Trust is part of the boundary**: Codex skips non-managed
  hooks until their exact definition is trusted (hash-recorded), so an
  untrusted guard silently does not run — Git-mutating Codex use without
  a trusted guard is outside the enforcing profile. Headless one-offs
  pass `--dangerously-bypass-hook-trust` explicitly.
- **Pi**: `pi/extensions/idh-guard.ts` — a `tool_call` handler that maps
  the bash event to the guard's payload and translates exit codes into
  Pi's `{ block, reason }`. It catches its own errors so the guard's
  fail-open doctrine is carried, not Pi's handler fail-safe (which would
  block on any breakage). Install: symlink into
  `~/.pi/agent/extensions/`.

**Refusal rule (binding for 0810's profiles):** a Git-mutating runtime
profile may not activate without its enforcing boundary — Claude: the
wired hook; Codex: the *trusted* hook; Pi: the installed extension.
Read-only use stays available; instructions and post-hoc warnings are
not enforcement. Codex's own docs say some specialized tool paths opt
out of the hook path: tool hooks are a guardrail, not a complete
boundary, and the inventory says so.

The wirings' guard paths live in the config plane (`settings.shared.json`,
`codex/hooks.json` use `$HOME/.claude/scripts/...`), where no
runtime-supplied path exists — unlike the skills seam, there is no loaded
body to derive a root from. The `~/.idh` relocation (0978) owns repointing
every one of them.

Weakening is tested, not warned about: `tests/test_guard_adapter_wiring.py`
rejects removal of the event mapping, the block result, the exit semantics
or the seam from the Pi adapter by a separate named check each, and pins
the Codex and Claude wirings to the canonical script.
