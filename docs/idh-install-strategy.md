# Portable installation

The reference clone lives at `~/.agents`. Use an absent destination when
cloning; inspect an existing skills directory or checkout first.

```bash
git clone https://github.com/MinhHaDuong/ImperialDragonHarness.git ~/.agents
cd ~/.agents
```

The checkout may live elsewhere. Helpers derive its root from the real
location of the loaded skill, script or installed adapter, or accept an
explicit root. Runtime-owned paths remain adapter destinations. Ticket 0999
tracks integration: registration 1003 landed in #1091; legacy helper handoff
1002 is WONTDO and unused provenance.py is retired under 0934, preserving data.
Memory ownership/sync remain 0988's separate v8 work; installation
does not certify a working dream storage contract.

## Register resources

Register resources reviewed for the selected runtime. Preserve existing
profiles and resolve same-name resource conflicts explicitly.

| Runtime | Target registration |
|---|---|
| Claude Code | Native plugin for reviewed skills and hooks; settings remain in the user's profile. |
| Codex | Local plugin registered through a personal marketplace. |
| Pi | Local package with an explicit resource list. |
| Mistral Vibe Code | Add the checkout's `skills/` path to `skill_paths` after reviewing compatibility. |

These are installation targets. The measured pilot covers two skills and
one guard across Claude Code, Codex and Pi; Vibe has a discovery probe.
See `adapters/pilot-support.json` for evidence.

At the reference location, Codex and Pi already scan `~/.agents/skills`.
Cloning there exposes the entire skill catalog to discovery immediately;
discovery alone does not certify each skill's runtime compatibility.
Installation must recognize canonical directories in place and avoid links
from a directory to itself.

## Current installer

`./bin/idh install skill <name> --to <runtime>` is the pilot skill installer.
It checks conflicts and versions before linking reviewed skills.

The bare `./bin/idh install` is all-runtime host setup. It creates
manifest links and edits `~/.bashrc`; it has no dry run or
runtime selector. It merges required hooks into existing Claude/Codex
configuration and links individual rules, skills, instructions, launchers and
the Pi extension without replacing profile directories or requiring a
repository pointer. Unrelated content survives; same-name resource conflicts
are refused and must be resolved explicitly, never deleted blindly.
At `~/.agents`, canonical skills are recognized in place, not self-linked.
Run `./bin/idh install` only after reviewing these host-wide actions.
After moving a checkout, run its `./bin/idh install` again: unchanged
receipt-owned links are refreshed and foreign replacements are refused.
`./bin/idh check` and `./bin/idh status` are read-only diagnostics.

## Remaining work

1. Prove project-local v8 capture and integration (0988) after the pilot;
   do not revive the closed legacy helper contract (1002).
2. Preflight selected-runtime registration and list exact actions and conflicts.
3. Package reviewed resources through native runtime mechanisms.
4. Keep shell integration opt-in; leave scheduling to the host.
5. Maintain arbitrary-location, relocation and runtime smoke evidence;
   registration fixtures do not certify every discovered skill's behavior.

[ROADMAP](../ROADMAP.md) tracks priorities; [adapter operations](adapter-operations.md)
covers the pilot. The old cutover is archived in
[idh-cutover-checklist.md](idh-cutover-checklist.md).
