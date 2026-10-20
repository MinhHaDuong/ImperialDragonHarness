# Cold coaching replay

Run the helper from the harness root, from any project directory (formerly
the `/coaching` skill; now a script, demoted under ticket 1140):

```bash
IDH_ROOT="${IDH_ROOT:-$HOME/.agents}"
"$IDH_ROOT/scripts/coaching/replay.sh" MODEL
```

Replace `MODEL` with the
candidate model ID. Optional flags are `--endpoint URL`, `--board FILE`,
`--repo DIR`, `--credential-env NAME`, and `--name LABEL`. The helper runs the
frozen board of merged PRs.
`--repo` selects the checkout supplied to the seat runner and defaults to this
repository. `--board` defaults to `benchmark-board.yml`. The endpoint option
defaults to the contained runner's local endpoint. For authenticated endpoints,
name a credential environment variable; the helper accepts an inherited value
or resolves it from the trusted user keystore. The credential is passed only to
the runner process. It never appears in arguments or output.

Each board PR is reconstructed from its recorded base and head by the contained
seat runner. Findings match board anchors by **basename and line**; a bare
basename or `:*` matches any line. The panel match takes precedence over a
defect match. The result preserves the legacy field names: `duplicate` matches
the panel, `unique-verified` matches a recorded panel-missed defect, and
`unique-hallucinated` matches neither. The last label means *unconfirmed by this
board*; it does not prove that a finding is false.

The single output row includes findings, overlap percentage, total latency,
nearest-rank p50/p95 latency, and token-price cost. Set
`REVIEWERS_PRICE_IN_PER_M` and `REVIEWERS_PRICE_OUT_PER_M` in USD per million
tokens for a cost estimate. With no prices or token counts, cost is `n/a`.
`SUMMARY|findings=0` is a valid clean replay. Missing output, a missing or
inconsistent summary, an incomplete board, or a failed runner exits nonzero
with a diagnostic on stderr and no result row.

The helper writes only temporary findings and removes them on exit. It never
edits the board, tickets, or logs.

The replay invokes the contained `seat-runner.sh` once per board PR and prints a
result only after every PR has completed with a valid summary; treat any nonzero
exit as an incomplete replay. It reads the board and already merged repository
revisions. It does not log trial tickets, change a reviewer roster, or make a
promotion decision.
