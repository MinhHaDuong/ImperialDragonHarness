---
name: reviewers
description: "Reviewer-management helper skill — request, harvest, normalize, scorecard"
disable-model-invocation: false
user-invocable: true
argument-hint: "<subcommand> [args]"
---

Manage the external reviewer panel for `/verify`. Delegates to
`skills/reviewers/reviewers.sh` for all I/O.

## Subcommands

### `/reviewers list`

Show panel members, their kind (forge-bot / cli-agent / local-model),
advisory/required status, and trial progress (merge requests observed /
projects covered).

Reads `skills/reviewers/panel.yml`. If the roster is empty, prints
"no reviewers configured" and exits 0.

### `/reviewers request <pr>`

Fire all configured external reviewers for a merge request. For each
reviewer kind, call the appropriate mechanism:

- **forge-bot**: request review via the forge's review-request API
  <!-- harness-extension-point -->
- **cli-agent**: invoke the adapter with the merge request diff
  <!-- harness-extension-point -->
- **local-model**: send the diff to the local inference endpoint
  <!-- harness-extension-point -->

Currently stubs until 0206/0207 land real reviewer adapters. Prints
"no reviewers configured" with an empty roster and exits 0.

No secrets in config — credentials via BASH_ENV path.

### `/reviewers harvest <pr>`

Collect all external findings, normalize to the 0205 contract shape:

```
verifiable: <file>:<line> — <rationale>
consider: <file>:<line> — <rationale>
```

Emit one findings file for the gate. With no findings (empty panel or
no comments returned), produce empty normalized output and exit 0.

### `/reviewers scorecard <pr> <verdict-summary>`

Append the per-merge-request trial line to the owning ticket's log
using `erg note`. Log verbs: `created`, `note`, `closed` only.

Example log line appended:

```
2026-06-04T12:00Z agent note MR #42 verdict: PASS — 0 blocking, 2 advisory
```

## Configuration

`skills/reviewers/panel.yml` is the single roster file. Structure:

```yaml
reviewers:
  - name: <identifier>
    kind: forge-bot | cli-agent | local-model
    disposition: advisory | required
    trial-ticket: <ticket-ref>
```

No secrets in config — credentials load via BASH_ENV.

## Dispatcher

All subcommands route through `skills/reviewers/reviewers.sh` (pure
I/O helper, case-switch dispatch). No plugin architecture — plain
case switch per subcommand.
