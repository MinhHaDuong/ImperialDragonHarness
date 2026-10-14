# Design 3 (author's proposal, 2026-10-14): investigate-and-report scripts at roar and lair

Proposed by the author after round 2; framed by the orchestrator. Assess it like the other designs.

## Mechanism
One script (shared core), called from roar and from lair. It deletes nothing.

1. **Scan** the usual places: `${TMPDIR:-/tmp}`, `~/.cache` minus a list of known tool caches (huggingface, uv, pip, numba...), runtime scratch roots (`/tmp/claude-<uid>`, Pi bash logs), and every registered worktree's `.tmp/`. Rank by bytes; report unreadable entries as a count.
2. **Investigate** each candidate above a size floor: grep local session histories for the creating command or the path, bounded to histories modified after the candidate's mtime (a search bound, never a deletion criterion).
   - Claude Code: `~/.claude/projects/*/*.jsonl` and `*/subagents/*.jsonl` (2.9G on padme)
   - Pi: `~/.pi/agent/sessions/` (11M)
   - Codex: `~/.codex/sessions/YYYY/...` rollouts (1.9G)
   A runtime with no reader still gets the scan with "creator unknown".
3. **Report candidates** with: path, bytes, quoted creating line (history file + line), creating session, whether that session is live, linked ticket state if the name maps to one, and whether any PR body / verdict / commit cites the path.
4. **Disposal belongs to the session** reading the report. Guards stay: never inside a live session's paths, never anything cited as evidence.

## Scopes
- **Roar:** only candidates whose creating line is in this session or its nested agents (task end).
- **Lair:** whole host, with creators named (crash recovery: leftovers of sessions that died before roar show with a dead creator).
- Per host: doudou's leftovers are found by a lair on doudou.
- Project-test leaks (zoteus-*, glossary-0882-*) have no creating command in a trace; expected attribution "created by a test run in repo X" via the test command and cwd.

## Price (orchestrator estimate)
6-8 agent-hours (~75-120 USD), 1 author-hour. Scan 2-3 h, Claude+Pi readers 2-3 h, Codex reader + tests with positive controls (planted directory + planted trace line) 2 h.
