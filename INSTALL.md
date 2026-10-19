# Installation

The reference checkout is `~/.agents`; adapters connect each runtime to the
same skills, rules and tools.

Clone into an absent destination:

```bash
git clone https://github.com/MinhHaDuong/ImperialDragonHarness.git ~/.agents
cd ~/.agents
```

If `~/.agents` already exists, inspect it first. Other checkout locations are
supported: entry points resolve the checkout from their real location or an
explicit root argument.

Follow the [installation guide](docs/idh-install-strategy.md) to register
resources with each runtime. `./bin/idh install` creates manifest links and
edits the shell loader, preserving unrelated profile content and refusing
same-name conflicts. Claude hooks come from the adapter plugin; Codex hooks
merge into its settings. Review these host-wide actions before running it:
there is no dry run or runtime selector, and shell integration is not opt-in.
Scheduling is left to the host.

The [operations runbook](docs/adapter-operations.md) covers verification,
removal and recovery. The [adapter reference](adapters/README.md) records
loaded-skill paths and measured runtime behavior.

For an existing installation:

- `./bin/idh check [RUNTIME]` reports broken manifest entries.
- `./bin/idh status` reports installation and repository state.
- `./bin/idh sync` fast-forwards or names the changes preventing it.

## Runtime support

The reference clone lives at `~/.agents`. The installation strategy uses
native registration to coexist with runtime-owned configuration.
Portability is measured, not presumed: `adapters/` currently has pilot
evidence for two skills (`perch`, `yawn`) and one guard across Claude
Code, Codex and Pi. Mistral Vibe has a version and skill-path probe but no
behavioral port yet. See `adapters/pilot-support.json` and
`docs/adapter-operations.md` for the current evidence.
