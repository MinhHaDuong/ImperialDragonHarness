# `/reviewers scorecard <pr> <seat> <verdict-summary>`

Append a fixed-schema trial line to the seat's trial ticket via `erg log`
(verbs: `created`, `note`, `closed` only), so 0205's integration review is
evidence-based:

```
MR #42 seat=local-qwen verdict: PASS — 0 verifiable, 2 consider latency=48.7s
```

When `request` left a `.latency` sidecar for the seat (a `cli-agent`/
`local-model` seat — see **Per-seat latency** in `references/request.md`), its
wall-clock seconds fold into the line as a
trailing `latency=<s>s` field (ticket 0353). Absent a sidecar the line is
byte-identical to the pre-latency schema — the field is appended at the end, so
every existing parser is unaffected.
