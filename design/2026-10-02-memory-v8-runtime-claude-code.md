# Memory v8 runtime evidence — Claude Code (ticket 0924)

Evidence for [ticket 0924](../tickets/closed/0924-remaining-runtime-adapters.erg), raid-0909
Wave 3 (Vibe was smoked by
[0923](2026-10-02-memory-v8-runtime-smoke.md); this wave covers Claude Code,
Codex and Pi with one session each). Session: 2026-10-02, headless
(`claude -p --output-format stream-json --verbose`), one real task in a
disposable clone of this repository at commit 81a468a8; the clone lives under
`/tmp/mem0924/claude-code/` on the executing host and nothing was committed
from it. The task was the common instruction shared verbatim with the other
two runtimes: recall the two worktree-session guards from project memory,
search the journal for "gaze panel", write findings outside the repository,
and record one public capture through
[scripts/memory-capture.sh](../scripts/memory-capture.sh) with the slug
`memory-v8-smoke-claude-code`.

Method: each leg below states what was observed and which artifact the
observation came from. The transcripts quoted are the runtime's own event
streams, recorded by the runtime — an evidence channel independent of the
agent's own summary of what it did.

## Runtime and scope

Runtime: Claude Code 2.1.286 (`claude --version`), model
`claude-opus-5-5` (init event), permission mode auto, headless `-p` mode,
allowed tools `Read Grep Glob Write Bash`. Version and model are recorded
from the runtime's init event in the session stream, not from the model's
self-description.

## (1) Read-before-action

The repository clone carries no `CLAUDE.md`; the only instruction file is
`AGENTS.md`. Two independent channels establish that Claude Code loaded it
and read the index before acting:

- **Context-only recall probe.** A second headless invocation in the same
  clone (no `CLAUDE.md`, no file reads allowed to happen — the event stream
  records zero tool calls) answered, from loaded context only: "At task
  start, read `memory/MEMORY.md` when it exists. At roar, the repository
  says to commit significant facts […]" — the AGENTS.md Project-memory
  section verbatim in substance. Claude Code 2.1.286 loads `AGENTS.md`
  natively through its built-in `cc-plugin-agents-md` plugin (the init
  event lists the plugin; the base system prompt is not echoed by
  `stream-json`, which is why the behavioural probe was needed).
- **Access trace in the session's first tool call.** The task session's
  first action was
  `cat memory/MEMORY.md; ls memory memory/journal | head -50; grep -ril "gaze panel" memory/journal; ls scripts | grep -i -E "capture|memory|journal"`
  — index read, then theme and capture-script discovery, before any write.
  The theme `memory/topics/git-worktree-session-guards.md` and its
  reference note were read next.

Evidence channel: the runtime's `stream-json` event files
(`/tmp/mem0924/claude-code/events.jsonl` for the task session,
`noalias-events.jsonl` for the recall probe) plus the
`~/.claude/projects/-tmp-mem0924-claude-code-clone/` transcript. The
model's own final statement was not used as proof.

## (2) Journal search

The session ran `grep -ril "gaze panel" memory/journal` (its first tool
call) and found
`memory/journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md`
— the same hit Codex and Pi found independently. Ordinary shell tools
sufficed; no dream report or index entry was needed for recall, matching
the AGENTS.md contract (search with `rg` or `grep` when recall is needed).

Evidence channel: the grep command in the first tool call of the event
stream and its tool-result event.

## (3) Public capture

The session invoked the repository's capture script as-is, no wrapper, no
adapter:

```text
scripts/memory-capture.sh . public memory-v8-smoke-claude-code <<'EOF'
# Memory v8 smoke evidence — Claude Code (ticket 0924) …
```

The script's own output line — `memory-capture: memory/journal/2026/
2026-10-02-memory-v8-smoke-claude-code.md (public)` — is recorded in the
tool-result event. The entry exists in the clone, audience `public`,
clearly marked smoke evidence. Nothing was committed from the clone: its
`git status --short` shows exactly one untracked path, the capture entry.
The private `.age` leg stays deferred by author decision F2 (recorded on
0923); no ciphertext was written.

Evidence channel: the command and its tool-result in the event stream, and
the entry file in the disposable clone.

## (4) Native-profile independence

No native-profile sync was performed or needed: the session read the whole
common memory surface (index, theme, reference, journal) from the clone
alone; nothing was seeded into `~/.claude` for this to work, and no
Claude-Code-native memory store participated in the recall. Observed
side channel, recorded as an observable rather than hidden: the host's
live user-level `~/.claude/settings.json` SessionStart hook fired in the
clone (a "PROJECT DIRECTIVE COHERENCE" note) — the global profile is a
delivery channel on this machine, but it is not a memory source and was
not needed for any leg. Claude Code wrote its session transcript under
`~/.claude/projects/` — ordinary session logging, not a profile sync.

Evidence channel: the hook_started/hook_response events in the session
stream; absence of any native-store read in the access trace.

## (5) Single source

`AGENTS.md` is the single source. A relative alias probe ran in a second
clone with `CLAUDE.md -> AGENTS.md` (symlink, no second content): the same
context-only recall prompt answered identically, again with zero tool
calls. The alias adds no divergent content — it is the same file — and in
2.1.286 it is not even necessary, since `AGENTS.md` loads natively. This
matches design v8 §3 (a relative CLAUDE.md link is permitted for
installations that need it; a second divergent content is not).

Evidence channel: `alias-events.jsonl` (zero tool calls, same answer as the
no-alias probe) and the `ls -la CLAUDE.md` symlink record.

## Limits

- One session, one model (`claude-opus-5-5`), one prompt family: this is
  smoke evidence for the loading and tooling legs, not a certification of
  adherence over repeated scenarios (design v8 §9 defers that measurement
  to the 0918 evaluation protocol).
- The context-only recall probes prove AGENTS.md content was in context;
  they do not measure whether it is always followed in longer sessions.
- Claude Code's live profile (hooks) fired because the host profile is
  configured; a clean machine may not show the coherence hook. This leg's
  finding does not depend on that hook.
- The raw event files quoted here (`events.jsonl`, `noalias-events.jsonl`,
  `alias-events.jsonl` under `/tmp/mem0924/claude-code/`, plus the
  `~/.claude/projects/` transcript) are ephemeral on the executing host and
  are not preserved in the repository; the quotations in this document are
  the surviving record.
- The capture entry lives in a disposable clone; it is quoted here and the
  raw clone is deleted after this document records the evidence. The
  journal of record carries the wave's own capture entry
  ([2026-10-02-memory-v8-runtimes-verified.md](../memory/journal/2026/2026-10-02-memory-v8-runtimes-verified.md)),
  not the clones' entries.

## Exit-criteria map

- Versions with limits and omissions → Runtime and scope; Limits.
- AGENTS.md single source, relative CLAUDE.md alias without divergent
  content → (5).
- Thematic reading, journal search and effective capture on this runtime
  → (1), (2), (3).
- No native-profile sync needed to read the common memory → (4).
