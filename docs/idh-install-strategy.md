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
owns implementation and verification of this contract.

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

## Existing installer

`./bin/idh install skill <name> --to <runtime>` is the pilot skill installer.
It checks conflicts and versions before linking reviewed skills.

The bare `./bin/idh install` is legacy all-runtime host setup. It creates
manifest links, edits `~/.bashrc` and enables a timer; it has no dry run or
runtime selector. The manifest still expects the Claude profile to resolve
to the repository and requires the legacy `~/.idh` pointer, so it is not yet
a general fresh-install recipe.
`./bin/idh check` and `./bin/idh status` are read-only diagnostics.

## Remaining work

1. Resolve checkout paths portably across all consumers.
2. Preflight selected-runtime registration and list exact actions and conflicts.
3. Package reviewed resources through native runtime mechanisms.
4. Keep shell integration and timers separate and opt-in.
5. Verify an arbitrary checkout location, relocation and runtime smoke tests.

[ROADMAP](../ROADMAP.md) tracks priorities; [adapter operations](adapter-operations.md)
covers the pilot. The old cutover is archived in
[idh-cutover-checklist.md](idh-cutover-checklist.md).
