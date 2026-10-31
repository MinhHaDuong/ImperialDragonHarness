# Skill case notes — design note

**Date:** 31 October 2026.
**Prepared by:** Claude Opus 5.5 (`claude-opus-5-5`), Claude Code session on
padme, from an idea by the author.
**Status:** design note for a pilot. It writes no rule, skill, prompt or AGENTS.md
text.
**Related:** ticket 1346 (memory use census, parent), 1349 (hoard as a rebuild),
1354 (outcome trial), audit `conception/2026-10-29-memory-system-audit.md`.

## 1. Idea

Attach to each skill a short note of cases from experience, kept per project, and
deliver it to the model when the skill loads. One note holds four cases: the
**most recent as of the note date**, the **usual**, the **best** and the **worst**. Each case follows the
case method used in management teaching: **context**, **what happened**, **how we
reacted**, **outcome**.

## 2. Why

- **Reading is the bottleneck, not writing.** The 1346 census: Claude Code main
  sessions read repository memory in 1 of 148 sessions on padme and 0 of 5 on
  doudou; Codex in about one session in five. Memory that waits to be pulled is
  not read. A note pushed at skill load does not depend on the model choosing to
  read.
- **Scope.** A per-skill note enters the context only when the skill runs.
- **Cases carry their context.** An abstract lesson loses the conditions that make
  it apply; a case keeps them, so the model can judge whether today looks alike.
  In the author's terms (memory is case law), these notes are case law per skill.

## 3. Design

### 3.1 Where notes live

`memory/skills/<skill-name>.md` in the **project** repository. Skills live in the
harness; cases belong to the project (AGENTS.md § Project memory boundary). The
harness holds procedure, the project holds experience.

Rejected: a project skill of the same name shadowing the harness skill. Claude
Code ranks personal over project skills, so the harness copy wins; Codex lists
both; Pi keeps the first discovered, order undocumented. Even where it worked, a
project copy forks the procedure. Too clever.

### 3.2 Note format

```markdown
# <skill> — cases
Updated: YYYY-MM-DD · skill version: <commit or date>

## Most recent as of YYYY-MM-DD
Context. What happened. Reaction. Outcome. Source: <journal entry / PR / ticket>.

## Usual
…  (with the count it summarises: "12 of 15 runs since 2026-09-01")

## Best — YYYY-MM-DD
…

## Worst — YYYY-MM-DD
…  Status: fixed by <commit/ticket> | still open.
```

Cap: about 400 words. Each case is dated and sourced. The worst case states
whether its cause was fixed since: an undated scare over-anchors the model and
outlives its fix.

### 3.3 Delivery: one script, wired per runtime

Same pattern as `scripts/guard-destructive-bash.sh`: one canonical script in
`scripts/`, launched through `idh-hook`, wired by each runtime's adapter.

| Runtime | Trigger | Context channel | Pilot stage |
|---|---|---|---|
| Claude Code | `PostToolUse` on `Skill` | `additionalContext` (to confirm) | 1 |
| Codex | to be found by the probe | only `SessionStart` measured so far | 2, probe |
| Pi | extension on a read of `skills/<name>/SKILL.md` | unverified: `idh-guard.ts` handles only `session_start` and `tool_call` | 3 |

The script: parse the payload → skill name → project root by
`git rev-parse --show-toplevel` (the cwd may be a worktree) → read
`memory/skills/<name>.md` → skip if already delivered → print the note under a
declarative header, "Case notes for skill <name>, from this project's memory:",
never an imperative (`rules/claude-code.md` § Hook output).

It logs one line for every outcome, not only deliveries: `delivered`, `no-note`,
`already-delivered`, `no-skill-name`. Without the misses, "no note" and "hook never
fired" look the same.

### 3.4 Delivered once per context

A marker file per context, `${XDG_STATE_HOME:-~/.local/state}/idh/skill-notes/<session_id>-<agent_id>`,
listing the skill names already delivered. Present → silent.

- Key on **session and agent**. Claude's payload carries `agent_id` only inside a
  subagent (`scripts/on-end.sh`), and a subagent does not share its parent's
  context.
- Deferred until a read-back shows the gap: re-delivery when the note changes
  mid-session, and a reset after compaction.

### 3.5 Deferred triggers and fallback

- `UserPromptSubmit` on a typed `/<name>`: added only if the read-back shows a
  typed slash command bypasses the `Skill` tool.
- Step 0 in the skill ("if `memory/skills/<name>.md` exists, read it"): only for a
  runtime where the probe shows a hook cannot inject.

### 3.6 Who writes notes

Pilot: written by hand from the journal. Later, if the pilot pays: roar refreshes
**Most recent**; smelt re-derives the other three in its rebuild (1349). Smelt writes only
`MEMORY.md` and `topics/` today (`memory/SMELT.md`), so this needs its own ticket.
Not in the pilot.

## 4. Pilot

The design stays portable; the pilot is staged so each stage starts only when the
previous one is shown working.

1. **Claude Code.** Script, `PostToolUse` wiring on `Skill`, a fixture test, and
   one note: `memory/skills/merge.md` in the harness, four cases from the journal
   (candidates: gate record staleness, local main sync, classifier refusals).
2. **Read-back, Claude.** In a fresh session, run `/merge` on a dry target and
   have the model quote a token planted in the note; check the log shows one
   `delivered`, then `already-delivered` on a second load. Repeat inside a
   subagent, and once with a typed `/merge`.
3. **Codex probe** (15 min): a hook prints a token at skill load; ask the model
   whether it sees it. Positive control: the same token from `SessionStart`, which
   is known to reach the model. Pass → wire Codex; fail → step 0 for Codex.
4. **Pi**, after stage 2 passes: extension wiring and the same read-back.

Out of scope: measuring whether notes improve outcomes. That is the 1354 trial; a
"skill case notes" arm can join it.

**Price (estimate):** half a day of agent time, 20–40 USD; author 30 min to read
the `/merge` note. Odds the hook works (estimate): Claude ~90 %, Pi ~80 %,
Codex ~50 %.

**Review.** KISS review by one Sonnet seat (same family, not independent),
2026-10-31. Taken: script location, staging, plain marker dedup, deferred
compaction reset and slash trigger, logging misses, declarative framing,
worktree-safe root, quoted-token read-back. Not taken: dropping Codex and Pi from
the pilot, because portability is the author's requirement; they are staged
instead.

## 5. Risks

- **Over-anchoring** on the worst case → dated cases, fixed/open status.
- **Staleness** after a skill changes → skill version in the header; smelt rebuilds.
- **Silent no-delivery** looks like "no note" → every outcome is logged, and the
  read-back has the model quote a planted token.
- **Context cost** ~500 tokens per skill per context; the marker keeps it to once.
