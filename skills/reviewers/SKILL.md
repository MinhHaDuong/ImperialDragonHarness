---
name: reviewers
description: "Reviewer-panel management for /gaze — list, request, harvest, scorecard, scores, audition, and help reviewer seats."
disable-model-invocation: false
user-invocable: true
argument-hint: "<subcommand> [args]"
---

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Manage the external reviewer panel for `/gaze`. Each seat is a sandboxed
CI-style reviewer job (ticket 0205, "review is CI"): `request` runs the
0217 seat-runner once per roster seat — one OS-sandboxed container per
seat — and `harvest` normalizes every seat's findings to the gate's
contract shape. Containment comes from the seat-runner's sandbox, not from
this skill. All I/O routes through `skills/reviewers/reviewers.sh`.

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

`skills/reviewers/panel.yml` is the single roster file (schema in its
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
