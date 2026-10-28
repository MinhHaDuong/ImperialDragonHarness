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

Follow the [installation guide](conception/idh-install-strategy.md) to register
resources with each runtime. `./bin/idh install` creates manifest links and
links every `bin/*` command into `~/.local/bin` (a name already taken is
refused and named; see `bin/README`), edits the shell loader, preserving
unrelated profile content and refusing same-name conflicts. Claude hooks come from the adapter plugin; Codex hooks
merge into its settings. Review these host-wide actions before running it:
there is no dry run or runtime selector, and shell integration is not opt-in.
Scheduling is left to the host.

The [operations runbook](conception/adapter-operations.md) covers verification,
removal and recovery. The [adapter reference](adapters/README.md) records
loaded-skill paths and measured runtime behavior.

For an existing installation:

- `./bin/idh check [RUNTIME]` reports broken manifest entries.
- `./bin/idh status` reports installation and repository state.
- `./bin/idh sync` fast-forwards or names the changes preventing it.

## Dependencies

Required:

- Linux with GNU coreutils and `flock` (§ Platform contract below).
- `git` and `make`; `bash` for the hooks and scripts.
- Python 3.11 or later (`pyproject.toml`), with [uv](https://docs.astral.sh/uv/):
  `make` runs Python through `uv run --frozen` against the locked `.venv`,
  unless a virtual environment is already active or `uv` is absent.
- At least one agent runtime: Claude Code, Codex or Pi. Each has a minimum
  version, checked by `./bin/idh check harness <name>`; the floors live in
  `adapters/pilot-support.json`, not here.

Optional, by feature:

| Tool | Needed for | Without it |
|---|---|---|
| `gh`, authenticated | the GitHub forge backend of `scripts/forge.py` | review and gate state go to git notes (the `none` backend); but on a repository with an `origin` remote, landing a merge waits for the forge and is refused |
| `age` and `age-keygen`, and an `origin` remote | journal entries not cleared for the repository's public audience, stored as age ciphertext (`scripts/memory-capture.sh`); the per-project key, `~/.config/keys/memory/<sha256(normalized origin URL)[:16]>.age`, is created on the first private capture | such captures are refused and reported as pending, never written in plaintext |
| `systemd-run --user` (systemd 254 or later) | arming a wake for a Codex session (`scripts/runtime.py wake arm`) | `wake arm` answers NOOP (`wake send` still works); a present but unusable user service manager makes `arm` fail with exit 2 |
| `act` and `podman` | running CI locally (`scripts/local-ci.sh`) | CI runs only on the forge |
| `rtk` | the token-saving command proxy ([RTK.md](RTK.md)) | commands run unproxied |
| Zotero desktop, running | the `zotero` skill (local API on 127.0.0.1:23119) | bibliography work is unavailable |

`tickets/erg`, the ticket tool, is committed as a Linux x86-64 binary.

## Platform contract

The harness targets Linux (systemd, `/proc`, GNU coreutils, `fcntl.flock`,
XDG paths); macOS and Windows are unsupported, and WSL2 is unverified.
Evidence: every CI job runs on `ubuntu-latest`, `ci-local/` runs podman, and
`tickets/erg` is a Linux x86-64 binary. Assumptions already committed:

- `/proc`: `scripts/worktree-gc.sh` snapshots live process cwds from
  `/proc/[0-9]*/cwd`, and some tests read `/proc` too.
- GNU-only flags: `readlink -f` (for example `scripts/bashrc-loader.sh`)
  and `sha256sum` (`scripts/memory-capture.sh`), plus `stat -c` in
  `tests/test_memory_capture.sh`, are used without a fallback.
- Hardcoded mounts: `scripts/tmp_report.py` reads disk headroom for `/tmp`
  and `/home` only.
- Inferred quota: `scripts/session_scratch.py` assumes systemd's default
  tmpfs `/tmp` and caps each user at 80% of it; the cap is inferred, never
  measured.

## Runtime support

The reference clone lives at `~/.agents`. The installation strategy uses
native registration to coexist with runtime-owned configuration.
Portability is measured, not presumed: `adapters/` currently has pilot
evidence for two skills (`perch`, `yawn`) and one guard across Claude
Code, Codex and Pi. Mistral Vibe has a version and skill-path probe but no
behavioral port yet. See `adapters/pilot-support.json` and
`conception/adapter-operations.md` for the current evidence.
