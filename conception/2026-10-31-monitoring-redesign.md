# Monitoring redesign: keep the transcripts, index the spans, derive the facts

Status: design memo, proposed 2026-10-31 for the author's review and a review
panel. It binds nothing until the author accepts it.

Asked 2026-10-31, after a harness-doctor consultation found that online
attribution capture is the main source of landing friction: rethink what is
recorded, when, how and where; keep every session transcript durably,
headless seats included; record the execution flow with timings and costs of
subagent and test calls, enough to draw timeline bars; keep pointers to the
transcript spans so a detail can be rebuilt quickly.

Measurements below were taken on padme on 2026-10-31 unless stated; doudou was
unreachable (`ssh: No route to host`), so its side is unmeasured.

## 1. Thesis

Record online only what cannot be reconstructed later; derive everything else
offline from durable transcripts.

The facts lost if not written at the moment they happen are **anchors**: the
link between a launcher and what it launched when the runtime does not record
it (a headless seat started by a script), and the session a commit came from. Timings, tokens, costs, exit codes, who
committed what, which gate ran on which head: all are in the transcripts
already, or in git. What is missing today is retention, coverage of every
runtime, and one index so that each analysis stops re-reading gigabytes.

## 2. Current situation

### 2.1 What is recorded, where, for how long

| Source | Where | Retention | Content useful for monitoring |
|---|---|---|---|
| Claude Code sessions and Task subagents | `~/.claude/projects/<cwd>/<session>.jsonl`, subagents in `<session>/subagents/agent-*.jsonl`; 5.5 GB, 282 project dirs, 7,735 subagent files | `cleanupPeriodDays: 180` (user and shared settings, the shared file first seen in commit 6193cb37 of 2026-07-22): deleted after 180 days. The oldest transcript is of 2026-06-10, later than the 180-day horizon (2026-05-04): an earlier, shorter period, likely the 30-day default, deleted the rest | timestamp on every message, tool call and tool result; token usage per assistant message; no dollar cost |
| Claude headless seats (`claude -p --restricted`) | same tree as interactive sessions | as above, assuming `--restricted` does not change the cleanup period (unverified, § 2.3) | as above |
| Codex (`codex exec`, interactive) | `~/.codex/sessions/YYYY/...`; 3.1 GB | oldest rollout 2026-09-08; no cleanup observed, too young to tell | event stream with token counts |
| Pi | `~/.pi/agent/sessions`; 12 MB | kept | per-call usage |
| vibe seats | disposable `VIBE_HOME` written per seat by `gaze_seat.py` | **lost** at seat end | none kept |
| aider seats | scratch cwd, `--no-restore-chat-history` | **lost** | none kept |
| `manuscript_review.py` readers | `claude -p ... --no-session-persistence` | **lost** | none kept |
| OpenRouter and Padmé LLM calls made by scripts | not recorded by the harness | — | billed cost per API key only, aggregated by `health_checkup.py` |
| Raw command output | the `rtk` PreToolUse hook compacts Bash output before it enters the transcript; `~/.local/share/rtk/tee/` keeps 124 KB of unfiltered output | short | the transcript holds the compacted form, not the raw output |
| Seat outcomes | `seat_clock.py` writes `<out>.status` (`reported in <s>s`) in the panel directory | as long as the panel dir lives | wall time per seat, no parent link |
| Review records | git notes `refs/notes/review` (88 notes), `memory/evidence/attribution/` (206 records) | durable | typed by hand online: the friction |
| Health pulse | `health/journal.jsonl` (49.6 KB) | durable | per-visit aggregates |

Session hooks exist in all three adapters (`adapters/claude-code/hooks/hooks.json`:
SessionStart, SessionEnd, PreToolUse; `adapters/codex/hooks.json`:
SessionStart, PreToolUse; `adapters/pi/extensions/idh-guard.ts`:
`session_start`, `tool_call`). None of them writes a monitoring record today.

### 2.2 How it is analysed

Sixteen scripts match `trace-*.py`, `trace_*.py`, `gate_traces.py`,
`mammoth-audit.py` and `health_checkup.py`; about eight of them read the
transcripts directly, each with its own reader: 5,198 lines in the `trace*`, `gate_traces` and
`mammoth` files alone. Each walk re-reads the corpus (mammoth: about 45 s on
4.7 GB). Only Claude Code's layout is read by most of them; Codex and Pi
traces are invisible to the surveys.

### 2.3 Observed gaps and open questions

- **August hole.** No Claude Code transcript on padme has an mtime between
  2026-07-30 and 2026-08-31, while the harness has 215 commits in August.
  Cause not established; the likely discriminator is doudou (work done there
  stays there). One experiment settles it: list doudou's transcripts by month.
- **Per-host stores.** Transcripts stay on the host that ran the session; no
  central copy exists.
- **Headless cleanup period.** `--restricted` ignores the settings files and
  the documented default is 30 days (§ 3); if a seat applied that default at
  start, it could delete every transcript older than a month. The surviving
  June files argue against it; one experiment settles it, first in P0 (a seat under a scratch `CLAUDE_CONFIG_DIR` holding a 40-day-old
  file).
- **Online attribution friction.** Since 2026-10-29, 15 of the 22 sessions
  that executed `attribution_record.py` met at least one refusal; the main one
  (30 of 47 refusal responses) is the missing `writer:` line in interactive
  sessions (ticket 1380). This is the symptom that opened the question.

### 2.4 Volume (measured, padme)

- October 2026, by mtime: 3.53 GB of Claude Code JSONL, 2.28 GB of Codex.
- zstd on a 163 MB sample (300 Claude files of 2026-10-20): 10.1 MB at
  level 19 (16×), 15.8 MB at level 3 (10×).
- Derived, not measured: at October's rate, an archive grows by about
  5.8 GB / 10–16 ≈ 0.4–0.6 GB per month compressed. `/home` has 163 GB free
  (83 % used).

## 3. State of the art

Full survey with sources and verification marks:
[2026-10-31-monitoring-redesign-sota.md](2026-10-31-monitoring-redesign-sota.md)
([V] read in a primary doc, [S] secondary, [U] unverified). What changes the
design:

- **Claude Code exports OTel natively** [V]: with `CLAUDE_CODE_ENABLE_TELEMETRY=1`,
  log events `claude_code.api_request` (model, `cost_usd`, `duration_ms`,
  tokens) and `tool_result` (`tool_use_id`, `duration_ms`, success), keyed by
  `session.id`, `prompt.id` and `message.uuid` (which matches the transcript).
  Events carry `agent_id` and `parent_agent_id`; beta traces nest subagents
  under the parent's tool span. `claude -p` reads an inbound `TRACEPARENT`,
  and Bash subprocesses inherit it: a headless Claude seat can become a child
  of its caller's trace. Conditions: telemetry is off by default, traces need
  the beta flag `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`, the agent fields need
  v2.1.310 or later, and export vars are honoured only in user or managed
  settings. Prompts and tool details are redacted by
  default.
- **Codex exports OTel** through `[otel]` in `config.toml` (events with
  durations and token counts, no USD) [V]. Its rollout files carry cumulative
  `token_count`, so per-turn usage is a difference; newer builds may write
  `.jsonl.zst`; the rollout format varies by version [S].
- **Pi writes cost in the transcript** (`usage.cost.total`), entries form a
  tree, the header names a `parentSession` [V]. No OTel export found.
- **Claude Code retention defaults to 30 days** [V]; large tool outputs spill
  to `<session>/tool-results/` [V], which the archive must include.
  `SubagentStop` hooks receive `agent_transcript_path` [V].
- **OTel GenAI agent conventions were "Development" as of 2026-06** (secondary
  source, not rechecked for October) [S]: do not adopt
  `gen_ai.*` as our schema; keep plain trace/span/parent ids and map on export.
- **Backends.** Langfuse needs Postgres, ClickHouse, Redis and S3 (heavy for one
  user); Phoenix is Elastic-licensed; Logfire self-host is enterprise-only;
  Jaeger v2 all-in-one with Badger is the lightest OTLP waterfall [S].
  Files plus SQLite/DuckDB fit a single workstation.
- **Timeline format.** Chrome Trace Event JSON opens in Perfetto with no
  server; duration events on one `tid` must nest, so concurrent subagents
  need one lane each [V].
- **Provenance by trailer is weak evidence**: in one study, 1 of 39 commits
  touching an agent-notes file carried the trailer [S]. Its critics argue for
  capture at generation time rather than labels at commit time. This design
  takes that position for the anchors (launch records and a session-id
  trailer are written when the act happens) and derives the rest by joining
  them with the transcripts. No in-toto/SLSA mapping for agent actions was
  found [U].

## 4. Design

### 4.1 Three layers

**L0 — Raw transcripts, kept durably (the record).**
A nightly job copies every transcript of the three runtimes untouched for a
day, with Claude Code's `tool-results/` spill directories, into an archive.
A resumed session grows its file: the job re-copies any source whose size
changed, and since transcripts only append, the new copy keeps every earlier
offset valid. The archive lives at
`~/archive/transcripts/<host>/<runtime>/<original relative path>.zst`,
compressed per file in the zstd seekable format.
doudou pushes to padme over the existing tailnet; padme is the archive host.
The archive is never pruned by a runtime; `cleanupPeriodDays` stays as is (it
now only frees the live tree). Files of projects with uncleared material are
encrypted at rest (age, the key outside the archive), as AGENTS.md requires.
Nothing is committed to git.

Coverage holes closed at the door: vibe and aider seats get a persistent
per-seat home under the archive's spool; `manuscript_review.py` drops
`--no-session-persistence`; script calls to OpenRouter and the Padmé LLM log
one line each (model, tokens, cost, duration, caller) to a spool file.

**L1 — Launch links and the span index (derived, rebuilt at will).**
Online, the only new writes are anchors: one-line launch records, and a
`Session: <runtime>/<session id>` trailer that a commit hook adds so the join
between a commit and its session is exact rather than inferred from time and
cwd. A launch record has this shape:

```
{"ts_start", "ts_end", "host", "parent_runtime", "parent_session",
 "child_runtime", "child_session", "launcher", "cwd", "unit", "exit"}
```

Launch records are kept for every runtime, Claude Code included. OTel's
`parent_agent_id` and `TRACEPARENT` (§ 3) would make them redundant for Claude
only if the OTel output were archived too; P1's probe decides whether that is
worth a collector, as a bonus, never as the only link.

`launcher` is the script (`seat_clock run`, `gaze_seat.py`,
`manuscript_review.py`, raid launchers); `unit` is the ticket or PR when the
launcher knows it; `child_session` is pinned at launch where the CLI allows it
(`claude -p --session-id`) or read from the child's first output. Session
start/end hooks in the three adapters write the same shape for top-level
sessions (host, cwd, branch, session id), and a Claude Code `SubagentStop`
hook writes `agent_id` with the documented `agent_transcript_path` [V], so
subagent parentage does not rest on the transcript's undocumented line schema. These are appends to one spool
file per host, never validated online, never able to refuse anything.

Offline, one shared event reader per runtime turns transcripts into a common
event stream; an incremental indexer reads that stream from L0 plus the spool
and writes one span table (SQLite or DuckDB; Parquet if DuckDB):

```
span_id, parent_id, session, host, runtime, kind (session|subagent|seat|tool|test|gate|llm_call),
name, start, end, model, tokens_in, tokens_out, tokens_cache, usd_shadow, exit,
cmd, result_head, skill, file, offset, line, tool_use_id
```

`cmd` (command text, truncated), `result_head` (first lines of the result)
and `skill` (skill invoked) carry what today's scripts read
(`scripts/gate_traces.py:299-320`, `scripts/mammoth-audit.py:95-103`); P3
starts by listing each consumer's needs and widening the table before any
migration. The last four columns point back into L0: `offset` is the byte
offset of the line in the uncompressed file, which the zstd seekable format's
jump table maps to its frame, so one frame is decompressed, not the whole
file; transcripts only append, so the offset stays valid across re-copies.
Encrypted files (uncleared projects) are decrypted whole: a minority, slow
on purpose. `usd_shadow` comes from a
price table under subscription auth (capacity, not invoiced money), as
trace-doctor already states.

**L2 — Facts derived on demand.**
Attribution (writer from the commits made in the session that owns the
branch; reviewers from the seats' launch records and notes), gate wall time,
cost per ticket, stale skills, merge path: queries over L1 and git, written
where they are needed (PR body, memory evidence) by the step that needs them,
never typed by hand. A query that cannot answer says "not derivable" and the
landing continues: no online refusal. A landing on the day of its session
runs the reader on that session's live transcript (one file, seconds); the
archive is for durability, not a prerequisite.

### 4.2 Timeline bars: is this enough?

Yes, with four conditions, all met by the design:

1. **Parentage.** Task subagents get it from the `SubagentStop` record (and,
   unverified, from the transcript's own fields); headless seats get it from
   the launch record. Without the launch record a seat floats free.
2. **Background commands.** Their end is the completion notification, not the
   tool result; the indexer pairs them.
3. **Clocks.** padme and doudou must run NTP; the indexer records the host so
   skew is visible.
4. **Rendering.** Export the spans as Chrome Trace Event JSON (complete events
   `ph: "X"`, `ts`, `dur`, `pid` = session, `tid` = lane) and open it in
   Perfetto UI as a local file: no service to run. A waterfall per raid, per
   ticket or per day is one query plus one export.

### 4.3 What this replaces

- Hand-typed attribution lines (`--record-writer`, the ordering rules that
  refuse) become derived; ticket 1380 is re-scoped to "derive the writer".
- The private transcript readers migrate to the index one by one;
  each migration deletes a parser.
- Seat `<out>.status` files stay (gaze reads them live); the launch record
  duplicates their timing for the index.

### 4.4 What it does not do

- No live dashboard or alerting: monitoring here is retrospective, which is
  what the doctors use.
- No OTel backend (Langfuse, Phoenix, Tempo). Whether to switch on native
  OTel export to a local file collector is decided by a probe in P1, on what
  it adds over the transcripts: native `cost_usd`, `parent_agent_id`,
  `TRACEPARENT` propagation, against one more service to keep alive and
  coverage limited to Claude Code and Codex.
- No change to what runtimes write; the harness reads their formats as they
  are and owns one parser per runtime.

## 5. Risks

| Risk | Odds | Mitigation |
|---|---|---|
| Runtime formats drift (three parsers to maintain) | high over a year | one parser per runtime, a fixture transcript per runtime as positive control, the indexer reports unparsed lines by count |
| Secrets in archived transcripts | certain that some exist | archive local and outside git, encrypted for uncleared projects, readable only by the user; no upload |
| Disk | low (≈ 0.5 GB/month measured rate) | monthly size line in the health checkup |
| doudou unreachable at archive time | medium | push from doudou when online; the index marks the host's last sync |
| Index becomes a second source of truth | medium | the index is disposable and rebuilt from L0; nothing writes facts only into it |
| A resumed session's later growth missed | low | the archive job re-copies on size change; the index marks a session whose live file is newer than its archive copy |
| Online launch records forgotten by a new launcher | medium | one helper (`launch_record.py`) used by every launcher; a seat without a record shows as an orphan span in the index, visible, not silent |

## 6. Phasing and migration cost

Prices are estimates: agent hours, USD at list price for the coder and review
seats, author time. Odds are the chance the phase meets its exit on the first
pass.

| Phase | Content | Exit | Agent | USD | Author | Odds |
|---|---|---|---|---|---|---|
| **P0 — Stop the loss** (now) | archive job (timer, zstd seekable, both hosts, re-copy on growth), close the vibe/aider/manuscript-review holes, run the two experiments of § 2.3 | every transcript untouched for a day exists in the archive at its current size; the August question answered | 4 h | 20–30 | 15 min (archive location, doudou access) | 85 % |
| **P1 — Launch links** | one-hour OTel probe (Claude Code and Codex to a local file collector, a `claude -p` seat under `TRACEPARENT`); then `launch_record.py` for the launches OTel does not link, wired into every headless launcher and the three adapters' start/end hooks (`SubagentStop` included); the `Session:` commit trailer | every seat of one gaze run appears with its parent; the OTel decision recorded | 4–5 h | 25–40 | 10 min | 80 % |
| **P2 — Shared reader, span index and timelines** | P2a: one event reader per runtime with a fixture each; P2b: incremental indexer, price table, Chrome-trace export | a raid of the week renders as a correct waterfall in Perfetto, spot-checked against its transcript | 8–12 h | 50–100 | 1 h (schema review) | 70 % |
| **P3 — Derive the facts, retire the parsers** | inventory each consumer's fields first; attribution writer and reviewers derived (re-scoped 1380), then migrate trace-doctor, gate_traces, mammoth, merge path, health checkup onto the index | 1380's exit met by derivation; each migrated script byte-compares its old output on a frozen window; net code deletion | 10–20 h over 4–6 hunts | 80–200 | 1–2 h | 60 % |

Total P0–P3: about 26–43 agent hours, 175–370 USD, 3–4 author hours.
P0 is independent and urgent (the 180-day window starts deleting the oldest
surviving transcript, of 2026-06-10, around 2026-12-07); P1 before P2 (orphan seats otherwise);
P3's children land one script at a time.

Per `rules/workflow.md` § Ticket discipline, this becomes a tracker with one
child per phase (P3 split per consumer), each `Blocked-by` its real
prerequisite.

## 7. Recommendation

Accept the thesis and start P0 at once; file the tracker with P1–P3 children,
the OTel probe opening P1. Re-scope 1380
now so that no one builds the writer line by hand in the meantime.

## 8. Review

Gaze panel on PR 2067, review rv-20261031-pr-2067-b6f9, head 81cde90:
FINDINGS, none blocking. Seats: facts re-measured by the orchestrator (Claude
Opus, same family as the author of the memo); state of the art by Claude
Sonnet (same family); design by GPT-6.1 Sol (OpenAI family, the independent
seat). Folded in this revision:

- The June cutoff was misattributed to the 180-day period; corrected (§ 2.1)
  and the urgency date moved to about 2026-12-07 (§ 6).
- A line number cannot address a frame of a compressed file (both seats,
  independently): pointers now carry the uncompressed byte offset, which the
  seekable jump table resolves; encrypted files are decrypted whole (§ 4.1).
- Resumed sessions re-copied on growth (§ 4.1, P0 re-priced); launch records
  kept for every runtime, OTel a bonus; same-day landings read the live
  transcript; the span table widened with `cmd`, `result_head` and `skill`,
  and P3 opens with a per-consumer field inventory; P2 split into a shared
  reader then the index.
- State of the art: the "1 of 39" figure restated with its scope; the
  critics' generation-time position stated and answered with the session-id
  trailer; TRACEPARENT conditions, Codex format variance and the date of the
  "Development" status made explicit; subagent parentage moved onto the
  documented `SubagentStop` hook.
- The script count corrected to sixteen matching, about eight reading
  transcripts; Codex's short history noted.

Not checked by the panel: the "15 of 22 sessions" refusal count (a transcript
scan from the harness-doctor consultation, not rerun) and doudou.
