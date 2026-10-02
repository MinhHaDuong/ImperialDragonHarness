# Memory v8 runtime evidence — Codex (ticket 0924)

Evidence for [ticket 0924](../tickets/0924-remaining-runtime-adapters.erg), raid-0909
Wave 3 (Vibe was smoked by
[0923](2026-10-02-memory-v8-runtime-smoke.md)). Session: 2026-10-02,
headless (`codex exec --json --sandbox workspace-write
--skip-git-repo-check -C <clone>`), one real task in a disposable clone of
this repository at commit 81a468a8; the clone lives under
`/tmp/mem0924/codex/` on the executing host and nothing was committed from
it. The task instruction was the same common prompt the other two runtimes
received, with the capture slug `memory-v8-smoke-codex` and the findings
path substituted.

Method: observations are quoted from the runtime's own event stream and
session transcript (`--json` events plus
`~/.codex/sessions/2026/10/02/rollout-…jsonl`) — channels recorded by the
runtime, independent of the agent's own final message.

## Runtime and scope

Runtime: codex-cli 0.159.3 (`codex --version`), model `gpt-6.1-sol`,
provider openai, approval never, sandbox workspace-write, reasoning effort
low — all from the exec header the runtime prints and its session log.
Detached-executor note (blind-spot F5): `codex exec` requires a trusted or
git directory or `--skip-git-repo-check`, and it consumes stdin when piped
— the first probe attempt failed with exit 1 until stdin was closed; the
session proper ran with stdin closed and exit 0.

## (1) Read-before-action

Codex loaded `AGENTS.md` natively: the session transcript contains the
AGENTS.md body ("…For shell tooling conventions, read and follow
[RTK.md](../RTK.md). ## Project memory boundary…") as session instructions,
before the user instructions. The access trace then shows the reading
order in the session's first commands:

```text
rg --files -g 'AGENTS.md' -g 'RTK.md' -g 'MEMORY.md' -g '*capture*' -g 'STATE.md'
cat memory/MEMORY.md RTK.md
cat AGENTS.md memory/topics/git-worktree-session-guards.md scripts/memory-capture.sh
```

The index (`memory/MEMORY.md`), the theme
(`memory/topics/git-worktree-session-guards.md`), its reference note and
the capture script were all read before the session's first write (the
findings file), which is the fifth command in the stream.

Evidence channel: the `item.completed` command events in the `--json`
stream and the AGENTS.md instructions block in the rollout transcript.
The model's own final message ("Read: AGENTS.md, RTK.md, …") was not used
as proof.

## (2) Journal search

The session ran `rg -n -i 'gaze panel' memory/journal/` and found
`memory/journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md`,
then read the entry. Same hit as Claude Code and Pi found independently;
ordinary tools (`rg`), no index line and no dream report needed.

Evidence channel: the command event and its output in the event stream.

## (3) Public capture

The session invoked the repository's capture script as-is:

```text
bash scripts/memory-capture.sh /tmp/mem0924/codex/clone public memory-v8-smoke-codex <<'EOF'
# Ticket 0924 — smoke evidence: Codex memory verification …
```

Exit 0; the entry exists in the clone (audience `public`, 946 bytes, mode
0644), clearly marked smoke evidence for ticket 0924. Nothing was
committed from the clone — its `git status --short` shows exactly the one
untracked capture entry. The private `.age` leg stays deferred by author
decision F2 (recorded on 0923); no ciphertext was written.

Evidence channel: the command event (exit 0) and the entry file in the
disposable clone.

## (4) Native-profile independence

No native-profile sync was performed or needed: the whole common memory
surface was read from the clone; `~/.codex` contributed configuration and
its own session log, not memory content. Sandboxed-HOME observable,
recorded rather than hidden: under `--sandbox workspace-write` the
session's writes were confined to the workspace, and the public capture
needed no `HOME` writes — the entry is written inside the repository by
the script. A future private capture, which derives an age key under
`~/.config/keys/memory/`, would need `HOME` write access beyond this
sandbox mode; that leg is deferred (F2) and its sandbox requirement is
recorded here as an observable, not resolved.

Evidence channel: the sandbox header in the exec output; the command
events (no `HOME` write in any of them); the clone's clean status.

## (5) Single source

The clone has no `CLAUDE.md`; Codex read `AGENTS.md` natively and, having
found it, also `cat`-ed it explicitly. No divergent instruction content
participated: the only instruction source in the session was `AGENTS.md`
(plus the repository's `RTK.md` and `tickets/AGENTS.md` references it
points to, which are the repository's own instruction surface). Nothing
was added to make the repository loadable — no adapter, no extension, no
symlink was created for this leg.

Evidence channel: the instructions block and command events in the
session transcript; absence of `CLAUDE.md` in the clone.

## Limits

- One session, one model (`gpt-6.1-sol`), one prompt family: smoke
  evidence, not a certification of adherence over repeated scenarios
  (design v8 §9 defers that to the 0918 evaluation protocol).
- Codex's native memory/auto-compact behaviour was not measured; only
  loading and tool-use of the common surface.
- The sandbox observation covers `workspace-write` only; other sandbox
  modes were not tried.
- The capture entry lives in a disposable clone, quoted here; the raw
  clone is deleted after this document records the evidence. The journal
  of record carries the wave's own entry
  ([2026-10-02-memory-v8-runtimes-verified.md](../memory/journal/2026/2026-10-02-memory-v8-runtimes-verified.md)).

## Exit-criteria map

- Versions with limits and omissions → Runtime and scope; Limits.
- AGENTS.md single source; no divergent CLAUDE.md content → (5).
- Thematic reading, journal search and effective capture on this runtime
  → (1), (2), (3).
- No native-profile sync needed to read the common memory → (4).
