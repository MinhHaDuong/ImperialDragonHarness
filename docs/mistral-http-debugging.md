# Native Mistral HTTP diagnostics

The arena runner now preloads `mistral-http-trace.cjs` into future native ML4 Pi
processes with NODE_OPTIONS. Existing processes are unaffected. Each attempt
gets private `attempts/N/http-trace` files: exact JSON request body, response
status and selected correlation headers, and the raw SSE response bytes.
Request headers are never persisted. Directory mode is 0700, files 0600.
Full prompts/tool results stay in the arena; do not commit trace directories.

The detector hashes the previous tool calls and contiguous tool results,
excluding call IDs. Five identical consecutive pairs create a `.loop.json`
marker; execution continues unchanged. Network errors get only their class.
Captures use a pull-through stream preserving backpressure and cancellation.
They can be compared with the corresponding Pi session JSONL to distinguish
upstream tool-call repetition from reconstruction or tool execution errors.

Replay one captured request without Pi (using MISTRAL_API_KEY in the environment):

```sh
python3 scripts/mistral-http-replay.py path/to/request.json --output /tmp/private-replay
```

Replay preserves the original messages/tools/parameters and saves the raw stream.
It does not execute tool calls. Responses remain stochastic: one replay is a
counterexample or reproduction, not proof that behavior is deterministic.

Verification: `node tests/test-mistral-http-trace.cjs`. Checks exact stream bytes,
one upstream call per request, observe-only loop detection, credential-header
exclusion and private file modes. Live Pi smoke evidence stays in
`~/arena/mistral-http-instrumentation-smoke/`.

With `MISTRAL_LOOP_BREAKER=5`, the fifth identical pair triggers a private
`.breaker.json` marker and rejects the next HTTP request. The session remains
latched, preventing subsequent requests. Diagnostic retries use arm `mb`, native
ML4/off, with the changed protocol explicitly recorded. Old completed looped
runs are annotated via `diagnostic.json` without rewriting original records:
they remain in real cumulative cost/time, but cannot be selected as ideal success.
An external watcher polls existing uninstrumented sessions every five seconds,
compares tool commands and results, and terminates only the matching Pi process
group when five identical consecutive pairs are confirmed.
