# Memory v8 runtime evidence — Pi (ticket 0924)

Evidence for [ticket 0924](../tickets/closed/0924-remaining-runtime-adapters.erg), raid-0909
Wave 3 (Vibe was smoked by
[0923](2026-10-02-memory-v8-runtime-smoke.md)). Session: 2026-10-02,
headless (`pi -p --session-dir <dir> --name mem0924-pi-smoke`), one real
task in a disposable clone of this repository at commit 81a468a8; the
clone lives under `/tmp/mem0924/pi/` on the executing host and nothing was
committed from it. The task instruction was the same common prompt the
other two runtimes received, with the capture slug `memory-v8-smoke-pi`.

Method: observations are quoted from the runtime's own session record
(the `--session-dir` JSONL transcript), a channel recorded by the runtime
and independent of the agent's own final message.

## Runtime and scope

Runtime: pi 0.87.1 (`pi --version`), provider `huggingface`, model
`moonshotai/Kimi-K2.6` (the session's `model_change` header; the host's
default provider configuration, not selected for this ticket). Pi was
the slowest of the three legs: the session ran about eight minutes
(10:26Z start, capture written 10:33:56Z).

## (1) Read-before-action

Pi loaded `AGENTS.md` natively: the session record's system message
contains `<project_instructions path="/tmp/mem0924/pi/clone/AGENTS.md">`
followed by the AGENTS.md body ("# Harness agent profiles …"). Pi loads
context files by default; `--no-context-files` is the documented opt-out,
which was not used here.

The access trace shows the reading order in the session's first tool
calls, all before its first write:

```text
read  memory/MEMORY.md                       (first tool call)
read  memory/topics/git-worktree-session-guards.md
read  memory/reference_git_in_a_worktree_session.md
bash  rg -l "gaze panel" memory/journal/
read  memory/journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md
read  scripts/memory-capture.sh              (twice, the second for the tail)
```

The index was the session's very first tool call; the theme and its
reference note were read before any write.

Evidence channel: the session JSONL under `/tmp/mem0924/pi/sessions/`
(toolCall events in order) and the system message quoted above. The
model's own summary in stdout was not used as proof.

## (2) Journal search

The session ran `rg -l "gaze panel" memory/journal/` — an ordinary shell
tool through Pi's `bash` tool — then read the matching entry,
`memory/journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md`.
Same hit as Claude Code and Codex found independently; no dream report or
index line was needed for recall.

Evidence channel: the `bash` toolCall event and its toolResult in the
session JSONL.

## (3) Public capture

The session found the capture script by itself (a `find`/`ls` discovery
call, then two reads of the script), then invoked it as-is:

```text
bash scripts/memory-capture.sh . public memory-v8-smoke-pi <<'EOF'
# Smoke evidence — ticket 0924 …
```

The entry exists in the clone at
`memory/journal/2026/2026-10-02-memory-v8-smoke-pi.md`, audience `public`,
clearly marked smoke evidence; the session then read the entry back to
confirm it, and closed with a `git status --short` that shows the capture
entry as the only repository change. Nothing was committed from the clone.
The private `.age` leg stays deferred by author decision F2 (recorded on
0923); no ciphertext was written.

Evidence channel: the `bash` toolCall event, the read-back toolResult,
and the entry file in the disposable clone.

## (4) Native-profile independence

No native-profile sync was performed or needed: the whole common memory
surface was read from the clone; nothing was seeded into `~/.pi` and no
Pi-native memory store participated in recall. Pi's session record was
directed to a disposable `--session-dir`, so even the transcript evidence
stayed outside the native profile; `~/.pi` contributed only the default
provider configuration this session happened to use (huggingface — a
sovereign-backend setup this host carries, see the
[backends essay](2026-09-28-essai-pi-backends-souverains.md)).

Evidence channel: the session JSONL header (`--session-dir` target) and
the absence of any native-store access in the toolCall trace.

## (5) Single source

The clone has no `CLAUDE.md`; Pi loaded `AGENTS.md` natively as the
project instructions (quoted in (1)) and no divergent instruction content
participated. No adapter, extension or symlink was created for this leg;
Pi's context-file discovery did the work unaided.

Evidence channel: the system message in the session JSONL; absence of
`CLAUDE.md` in the clone.

## Limits

- One session, one model (`moonshotai/Kimi-K2.6` via huggingface), one
  prompt family: smoke evidence, not a certification of adherence over
  repeated scenarios (design v8 §9 defers that to the 0918 evaluation
  protocol).
- The session was noticeably slower than the other two legs (~8 minutes);
  no conclusion is drawn from the duration itself.
- Pi's extension surface (subagents, hooks — the capability survey of
  2026-09-16) was not exercised: this ticket verifies the Markdown
  contract, and no runtime plumbing was added.
- The session JSONL quoted here (under `/tmp/mem0924/pi/sessions/`) is
  ephemeral on the executing host and is not preserved in the repository;
  the quotations in this document are the surviving record.
- The capture entry lives in a disposable clone, quoted here; the raw clone
  is deleted after this document records the evidence. The journal of
  record carries the wave's own entry
  ([2026-10-02-memory-v8-runtimes-verified.md](../memory/journal/2026/2026-10-02-memory-v8-runtimes-verified.md)).

## Exit-criteria map

- Versions with limits and omissions → Runtime and scope; Limits.
- AGENTS.md single source; no divergent CLAUDE.md content → (5).
- Thematic reading, journal search and effective capture on this runtime
  → (1), (2), (3).
- No native-profile sync needed to read the common memory → (4).
