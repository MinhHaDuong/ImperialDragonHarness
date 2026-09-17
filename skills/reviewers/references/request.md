# `/reviewers request <pr> [branch]`

For each roster seat, run the 0217 seat-runner over the merge request's
diff (the branch is resolved from the PR, or passed explicitly):

- **cli-agent / local-model**: the seat-runner launches the agnostic CLI
  reviewer inside an OS sandbox over an OpenAI-compatible endpoint
  (OpenRouter or local llama-server), writing per-seat findings.
- **forge-bot**: requested via the forge's reviewer-request API, using the
  seat's `login` from the roster (on GitHub: <!-- harness-extension-point -->
  `gh api --method POST repos/{owner}/{repo}/pulls/<pr>/requested_reviewers
  -f 'reviewers[]=<login>'`).
  **On-demand only** (ticket 0206): the seat fires when this subcommand is
  invoked on a specific merge request — no repo-wide auto-request, so
  trivial PRs stay unreviewed. Its findings surface as review comments on
  the merge request itself (not as `harvest` findings files); the gate
  dispositions them like any panel comment.

**Per-seat fail-open**: a seat that errors or hangs WARNs and the others
proceed — one seat never blocks the verdict (0205). Empty roster → no-op,
exits 0. Fail-open is not fail-silent: every seat that did not review is
recorded in a `<seat>.status` sidecar and named by `harvest` in the report
(see **Panel integrity** in `references/harvest.md`). No secrets in config.

**Seat credentials** (tickets 0393, 0947). A seat's `credential-env: NAME` is an
uppercase credential-shaped shell name: it must contain an underscore-delimited
`API_KEY`, `KEY`, `TOKEN`, `PASSWORD`, or `SECRET` component. It is read from
the environment only when the caller explicitly exported it. Normally `NAME`
is absent because the harness startup path does not make credentials resident
in the ambient environment (0945). `request` then resolves it from the fixed keystore
(`~/.config/keys/*.env`): the single bounded regular file
defining `NAME` is sourced under `set -a` in an `env -i` subshell, only that one
scalar, single-line variable is extracted, and it is exported solely inside the subshell that execs
the seat-runner. The author's key files are never edited — they hold bare
assignments with no `export`, and enabling allexport at source time is what
makes such an assignment reach a child process. A value never touches argv, a
log line, or a sidecar; warnings name variables and provider files only. A seat
whose credential resolves nowhere is skipped, WARNed, and reported by `harvest`
— it is not quietly dropped from the panel.

The three keystore consumers intentionally remain local implementations rather
than sharing a Bash library: one port is Python and their error/value contracts
differ. What is shared is the security checklist a future copier must reapply:
fixed or positional provider path, regular-file and 256 KiB bounds before
reading, controlled utility lookup, cleared child environment, credential-name
allowlist, scalar/single-line value, and CRLF normalization. `BASH_ENV` is not
claimed as a script-local mitigation: Bash evaluates it before the script's
first line, so a hostile calling environment is already executing code before
this resolver can unset anything.

**Per-seat latency** (ticket 0353): each `cli-agent`/`local-model` seat is timed
and its wall-clock seconds written to a `<seat>.latency` sidecar beside the
findings, whatever the outcome (a slow-then-failed seat is still evidence).
`scorecard` folds that figure into the seat's trial line. `forge-bot` seats run
async server-side and get **no** sidecar — there is nothing local to time.
