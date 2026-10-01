---
name: reviewers
description: "Reviewer-panel management for /gaze — list, request, harvest, scorecard, scores, audition, and help reviewer seats."
disable-model-invocation: false
user-invocable: true
argument-hint: "<subcommand> [args]"
---

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Describe the external reviewer needs for `/gaze`, then let the active runtime
find available independent reviewers and route requests. Possible resources
include llama.cpp on Padmé, OpenRouter, other local agents, and agents on another
host. No fixed roster, provider, or transport is mandatory. Record who actually
reviewed, what material they received, their findings, and missing perspectives.

The subcommands below manage the bundled seat-runner helper when the runtime
chooses it. Its configured seats are sandboxed CI-style reviewer jobs; containment
comes from that helper's sandbox. These helpers are optional routes, not the
runtime's complete catalogue of available reviewers. Other routes must preserve
the same finding evidence and panel-integrity information for the gate.

## Subcommands

A run uses exactly one. **Read that subcommand's reference file before acting**
— each is self-contained, and the contract details that make a subcommand
correct (credential resolution, fail-open vs fail-loud, card schemas) live
there, not here.

| subcommand | what it does | detail |
|---|---|---|
| `list` | show the roster | below |
| `request <pr> [branch]` | run every seat over a merge request's diff | `references/request.md` |
| `harvest <pr>` | normalize seat findings, report panel integrity | `references/harvest.md` |
| `scorecard <pr> <seat> <verdict-summary>` | append a trial line to a seat's ticket | `references/scorecard.md` |
| `scores [seat-or-candidate]` | read back trial cards as one comparison table | `references/scores.md` |
| `audition <model> [--endpoint URL]` | replay a candidate over the frozen benchmark board | `references/audition.md` |
| `help` | print usage | below |

`list` and `help` are documented here rather than in a file of their own: at
three lines each, the pointer would cost more than the text.

### `/reviewers list`

Show panel members, their kind (forge-bot / cli-agent / local-model),
advisory/required status, and trial ticket. Empty roster → prints
`no reviewers configured`, exits 0.

### `/reviewers help`

Print the usage block to stdout and exit 0. The no-argument and unknown-verb
paths keep printing usage to stderr and exiting 1.

## Configuration

`skills/reviewers/panel.yml` is the bundled helper's roster file (schema in its
header). No secrets in config — a seat names its credential *variable*, and
the value is resolved at run time (see **Seat credentials** in
`references/request.md`).

The credential keystore is fixed at `~/.config/keys`: it is sourced as trusted
shell code, so no environment variable may redirect it. `REVIEWERS_PANEL`, `REVIEWERS_FINDINGS_DIR`,
`REVIEWERS_REPO`, `SEAT_RUNNER`, and `ERG` override the roster, the findings
directory, the repo under review, the seat mechanism, and the ticket binary.

For an on-demand Padmé-only trial, run
`skills/reviewers/padme-reviewers.sh request <pr> [branch]`. It opens an SSH
forward to the existing llama-server, uses `panel-padme.yml` and the bounded
direct client inside the same read-only seat sandbox, then closes the forward.
Run `skills/reviewers/padme-reviewers.sh harvest <pr>` to read that trial's
findings. Its sidecars live under `${TMPDIR:-/tmp}/reviewers-padme` by default,
away from the regular panel's sidecars. The regular roster and its paid seats
are not invoked by this path. The local client fails loud for diffs above
32,768 bytes so the bounded trial never silently truncates a large PR.

`skills/reviewers/benchmark-board.yml` is the frozen audition board: ~10
already-merged multi-file code PRs of this repo, each with `base`/`head` commit
SHAs (immutable, so the diff is reconstructable forever) and ground-truth
`panel`/`defects` anchors recovered from the PR's gate verdict. It is a data
artifact — `audition` reads it, never edits it. Schema in its header.

## Dependencies

- `"$IDH_ROOT/scripts/seat-runner.sh"` (ticket 0217) — the
  sandboxed seat execution mechanism `request` invokes. Override with
  `SEAT_RUNNER` for testing.
- `tickets/erg` — `scorecard` appends the trial log line.
