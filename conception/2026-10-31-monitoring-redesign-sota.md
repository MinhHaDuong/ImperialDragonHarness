# SOTA: agent execution-flow recording (as of 2026-10-31)
Marks: [V] read in primary doc this session; [S] secondary/blog; [U] unverified.

## 1. Claude Code
- OTel is off until `CLAUDE_CODE_ENABLE_TELEMETRY=1`; `OTEL_METRICS_EXPORTER`/`OTEL_LOGS_EXPORTER` (otlp|prometheus|console|none), `OTEL_EXPORTER_OTLP_PROTOCOL/ENDPOINT`. https://code.claude.com/docs/en/monitoring-usage [V]
- Log events: `claude_code.api_request` (model, cost_usd, cost_usd_micros, duration_ms, in/out/cache tokens, request_id, query_source, effort), `tool_result` (tool_name, tool_use_id, success, duration_ms), `tool_decision`, `user_prompt`. Ids: `session.id`, `prompt.id`, `tool_use_id`, `message.uuid` (matches the transcript entry). [V]
- Subagent parentage: `agent_id`, `parent_agent_id`, `agent.name` on events (v2.1.310+). Traces are beta: need `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` + `OTEL_TRACES_EXPORTER=otlp`. Hierarchy `interaction > llm_request | tool > tool.execution`; subagent spans nest under the parent's `claude_code.tool` span. [V]
- `claude -p` honours the same env vars; it also reads inbound `TRACEPARENT`, so a headless seat becomes a child of the caller's trace. Interactive sessions ignore inbound TRACEPARENT. Bash subprocesses inherit `TRACEPARENT`. Events carry trace_id/span_id even with no traces exporter. [V]
- Prompts/tool details are redacted by default (`OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_RAW_API_BODIES` opt in). Telemetry export vars in a project `env` block are ignored (user/managed only). [V: settings page]
- Transcripts: `~/.claude/projects/<project>/<session>.jsonl`; subagents in `<session>/subagents/agent-<id>.jsonl` (same format); large tool outputs in `<session>/tool-results/`. Plaintext, may hold secrets. [V] https://code.claude.com/docs/en/claude-directory
- `cleanupPeriodDays`: default 30, min 1, 0 is a validation error; deletes by age, subagent transcripts go with the parent; sweep skipped under `claude -p --bare`; paused if retention can't be determined. `--no-session-persistence` / `CLAUDE_CODE_SKIP_PROMPT_HISTORY` skip writing. `history.jsonl`, `stats-cache.json` are kept. [V]
- Hooks: `SubagentStart` {agent_id, agent_type}; `SubagentStop` {agent_id, agent_type, agent_transcript_path, last_assistant_message}; `SessionEnd` has a `reason` (matchers clear/resume/logout/prompt_input_exit/other) and a 1.5 s default budget. Common input: session_id, transcript_path, cwd, tool_use_id (tool events). Docs show no parent/launcher tool_use_id on SubagentStart; link via PostToolUse on `Agent`. Transcript is written async and may lag. [V; SessionEnd fields not read]
- Not found: the internal JSONL line schema (parentUuid, isSidechain etc.) as a documented contract. [U]
- Implication: the cheapest durable record is a SubagentStop hook that appends {session_id, agent_id, agent_type, agent_transcript_path, ts} to our own launch log, plus copying/archiving transcripts before the 30-day sweep (raise cleanupPeriodDays or archive). OTel events with `OTEL_LOGS_EXPORTER=otlp` to a local file/collector give cost+duration per call without parsing transcripts.

## 2. Codex CLI
- `[otel]` in config.toml: `exporter` none|otlp-http|otlp-grpc, `log_user_prompt` (default false), `environment`. With `none` events are recorded but not sent. https://learn.chatgpt.com/docs/config-file/config-advanced (redirect from developers.openai.com) [V]
- Events: `codex.conversation_starts`, `api_request`, `sse_event` (token counts on `response.completed`), `user_prompt`, `tool_decision`, `tool_result` (duration, success), plus metric `turn.token_usage`. [V]
- Rollouts: `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<id>.jsonl`; line = {timestamp,type,payload}; types session_meta (first line; cwd, id, cli_version, originator), turn_context, response_item, event_msg. `token_count` is cumulative `info.total_token_usage` (differ successive values; info null on rate-limit-only). Tools matched by call_id. Newer builds may write `.jsonl.zst`. https://docs.rs/crate/agent-top-core/latest/source/src/harness/codex.rs ; https://codex.danielvaughan.com/2026/06/05/codex-cli-session-forensics-jsonl-post-mortems-codex-trace-cass-ccusage/ [S, format varies by version]
- TokenUsage fields (input, cached_input, cache_write_input, output, reasoning_output, total): github.com/openai/codex codex-rs/protocol/src/protocol.rs [V]. SessionMeta/subagent-source variants: not read [U].
- Implication: Codex gives no cost in USD; derive from tokens x price table. Pin a per-version parser and test on fixtures.

## 3. Pi
- Session JSONL at `~/.pi/agent/sessions/--<path>--/<ts>_<id>.jsonl`; header line {type:"session", version(3), id, timestamp, cwd, parentSession?}; entries have id/parentId (tree); types message, model_change, usage, compaction, branch_summary, custom, ... Assistant messages carry `usage.cost{input,output,cacheRead,cacheWrite,total}`; entry timestamps ISO, in-message timestamps Unix ms. Repo is now earendil-works/pi (badlogic/pi-mono path 404s). https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md [V]
- Implication: Pi is the only runtime with cost in the transcript; `parentSession` gives fork lineage but no subagent concept found [U].

## 4. OTel GenAI / OpenInference / OpenLLMetry
- GenAI semconv moved to github.com/open-telemetry/semantic-conventions-genai (Apache-2.0); old opentelemetry.io page is a stub. https://github.com/open-telemetry/semantic-conventions-genai [V]
- Agent spans (`invoke_agent`, `execute_tool`, `gen_ai.usage.*`) are Status: Development; opt-in via `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`; move in v1.42.0 on 2026-06-12. https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans [S via search snippets; page itself is a pointer]
- Claude Code's native spans use its own `claude_code.*` names, not gen_ai.* [V], so a mapper is needed for GenAI-aware backends.
- OpenInference (Arize): `openinference.span.kind` in LLM/CHAIN/AGENT/TOOL... (11 kinds). https://arize.com/docs/ax/concepts/otel-openinference/span-kinds [S]. OpenLLMetry: Apache-2.0, Traceloop (reported joining ServiceNow Mar 2026, [U]).
- Implication: do not adopt gen_ai.* as storage schema; it is unstable. Use plain OTel-style span fields (trace_id, span_id, parent_span_id) and map on export.

## 5. Backends
- Langfuse: needs web+worker+Postgres+ClickHouse+Redis+S3; compose is "local/testing, no HA/backups"; OSS core with licence-key enterprise add-ons (MIT per [S]). https://langfuse.com/self-hosting [V]. Heavy for one user.
- Arize Phoenix: Elastic License 2.0 (not OSI open source), single container, Docker/Helm; SQLite/Postgres storage [S]. https://github.com/Arize-ai/phoenix [V licence]. Has a Claude Code plugin emitting OpenInference spans incl. subagents. https://arize.com/docs/phoenix/integrations/coding-agents/claude-code [S]
- Jaeger v2: OTel-collector based, native OTLP 4317/4318, Badger embedded storage (set `--badger.ephemeral=false`, no default TTL); v1 EOL 2025-12-31. [S] Tempo: object-storage oriented, no full index, k8s-leaning [S].
- Logfire self-host: enterprise contract, private images, needs k8s+Postgres: unfit. Helicone: Apache-2.0 core, gateway possibly GPL-3.0, acquired by Mintlify Mar 2026 and in maintenance: poor fit [S, conflicting].
- Implication: for a single workstation, files + DuckDB first; if a waterfall UI is wanted, Jaeger v2 all-in-one with Badger is the lightest OTLP target. Skip Langfuse/Logfire.

## 6. Timeline formats
- Chrome Trace Event JSON (Perfetto/ui.perfetto.dev/chrome://tracing): array of {name,cat,ph,ts(us),dur,pid,tid,args}; `X` complete events, `B`/`E` pairs, `M` metadata names processes/threads, flow `s/t/f` arrows. Duration events on a thread must nest; overlapping siblings need async events or separate tids. https://perfetto.dev/docs/getting-started/other-formats [V; required-field list for X not stated there, `dur` is standard in the Chrome spec]
- Minimal Gantt row: span_id, parent_id, name, kind, start_ts, end_ts, runtime/model, status. Map session->pid, agent->tid (one lane per concurrent subagent), tool call -> X event; put cost/tokens/transcript pointer (file+line) in args.
- Implication: emit trace.json from the span index on demand; no server needed.

## 7. Archival
- zstd seekable format (contrib): independent frames + jump table, readable by plain zstd; frames >=1 KB, smaller frames cost ratio. https://github.com/facebook/zstd/tree/dev/contrib/seekable_format [V]. Codex itself may emit .jsonl.zst [S].
- DuckDB `read_json/read_ndjson` with globs and `filename` can index JSONL in place; exact options not verified (docs redirected) [U]; DuckDB cannot read seekable zstd frames by offset, so pointers should be (file, line) over uncompressed or whole-file decompress after cold storage.
- Claude transcripts are plaintext and contain secrets from tool output [V]; archive with 0600/encrypted store and scrub at export, not at write. Retention: archive before the 30-day sweep.
- Implication: hot = raw JSONL, cold = per-session .zst, index = SQLite/Parquet of spans with pointers.

## 8. Derive, don't record
- Trailers (`Co-authored-by`, Block's aittributor hook, QAC trailers) are cheap but weak evidence; one NeurIPS 2026 audit found 1 of 39 commits touching an agent-notes file carried the trailer. https://neurips.cc/virtual/2026/166237 ; https://dev.to/piiiico/co-authored-by-is-not-enough-1nee [S]
- Critics argue provenance must be captured at generation time, not labelled at commit time [S].
- in-toto/SLSA mapping for agent actions: nothing found [U].
- Implication: derive commit attribution offline by joining commit time/worktree/branch/cwd against span index (Bash tool_result containing `git commit`, with `TRACEPARENT`/session_id), and write the join result as git notes if needed. Keep a cheap trailer (session id) as the anchor to make the join exact.

## Unverified / to check
Claude JSONL line schema; Codex SessionMeta subagent fields; DuckDB read_json options; Phoenix storage details; Tempo/Jaeger specifics (single secondary source); Traceloop acquisition; Helicone gateway licence.
