# adapters/

Native glue for harnesses other than the one this repository is checked out
into. Two unrelated things live here today:

- `claude-code/` — the harness's hook wiring as a Claude Code plugin (ticket
  0887). Its own README is next to it.
- `perch.py` + `pilot-support.*` — the multi-harness skill pilot (ticket
  0802), described below.

## The perch pilot

One question, one skill: what do Claude Code, Codex and Pi actually require
around a shared skill body? `skills/perch/SKILL.md` is the smallest useful
answer — portable Markdown, read-only, no tools. It is hand-ported, not
generated: there is no skill IR here, no workflow DSL and no second copy of
the prose.

    adapters/perch.py status              # where each harness looks, and what is there
    adapters/perch.py install codex
    adapters/perch.py uninstall codex
    adapters/perch.py check-version pi

### Where the skill goes

`$HOME/.agents/skills` is not a name this pilot invents. It is the user-level
[Agent Skills](https://agentskills.io/specification) root that **Codex** and
**Pi** each document and each scan, and both follow a symlinked skill
directory — so `install` points it at `skills/perch` in this repository and
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

Run from a git worktree, `status claude` reports `other-checkout`: the
canonical source is then the worktree's copy while the skills root still holds
the primary checkout's. Install refuses — pointing a live skills root at a
throwaway worktree is not an improvement — and says so in those words.

### Version support is a floor, not a list

`check-version` probes `<cli> --version` and compares it against
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

`adapters/perch.py uninstall <harness>` removes the managed link, then every
directory the removal left empty, up to and including the neutral home. A
neutral home holding anything else survives untouched, and the canonical skill
is never deleted. One caveat stated rather than papered over: nothing on disk
records which of those empty directories `install` created, so an empty one you
made by hand goes with them. Nothing under `skills/` is touched at any point,
so the pre-experiment Claude state is restored by construction.

`uninstall codex` and `uninstall pi` reach the same link — one neutral home,
one perch — so each names both harnesses in what it reports. A link left
dangling by moving the checkout is reported as `dangling` and removed on
request, rather than sitting there as an entry nothing can clean up.
