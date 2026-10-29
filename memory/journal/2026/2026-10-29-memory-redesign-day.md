# Memory redesign day: fifth hoard closed, audit, department rulings

Date: 2026-10-29. Session: lair, then author-led design, Claude Code (claude-opus-5-5).

## Context
The author found the fifth hoard (PR #1975: +895/-25 lines in `memory/`) accumulative
and asked whether stale memories had been retired.

## Events
- Two cross-family reviews of PR #1975 were run read-only on its head: Fable (anthropic) and
  gpt-6-astra (openai, through `codex exec`). Both returned "redo". They estimated 10-35% of
  topic text as current-state claims, and found superseded claims marked in place rather than
  removed. Both named `skills/hoard/SKILL.md:69-70` and the absence of a topic budget as causes.
- An audit (PR #1984, `conception/2026-10-29-memory-system-audit.md`) measured on padme:
  - 0 of 148 Claude Code working sessions since 2026-10-15 used `Read` on `memory/MEMORY.md`
    or topics; a lair recheck found 0 of 106, with a positive control of 26 sessions.
  - Codex read them in 77% of 468 working sessions.
  - 183 of 380 journal entries are attribution records.
  Gaze reproduced the numbers.
- The author closed PR #1975 unmerged and filed tickets 1346-1352 (PRs #1985-#1995).
- Author rulings recorded on 1348:
  - departments: a shared core of Commission, Site practice, Environment and History, plus
    departments by type of work (accepted provisionally);
  - the as-built file (DOE) as the organizing metaphor;
  - hoard renamed smelt (1352);
  - 4 KB per department page, index 40 lines;
  - the journal stays the intact source, and department pages are guides to it;
  - pinned rulings; recall shown with its source.
- Probes, padme only:
  - Claude Code native notes: 1,137 notes in 47 stores, 26% in superseded or old-path dirs.
    In the harness store, 41% are rules in disguise and 52% hold knowledge the repo never captured.
  - Codex `memories` feature: off, store empty.
  - Pi 1.4.0 and Vibe 2.26.0: no built-in memory. pi.dev lists 219 memory packages.
- Web survey recorded on 1346:
  - Claude Code docs: `autoMemoryDirectory` is accepted from project settings; subagent `memory:` field.
  - Qwen Code: managed memory, `pinned/`, documented Dream, team memory in the repo.
  - ReMe v0.4.2.0 (Alibaba AgentScope, 2026-10-26), with Claude Code and Codex plugins.
  - DreamBench-SWE (arXiv:2608.20664): a typed consolidation pipeline did not beat verbatim
    memory, 95/180 versus 89/180, p = .52.

## Outcome
The memory redesign is ticketed and ordered: 1346 and 1347 first, then 1352, then 1349, then
1351. The README's memory section carries a "being reworked" notice.
