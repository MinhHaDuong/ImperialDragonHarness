# Memory system audit — 2026-10-29

**Date:** 29 October 2026.
**Prepared by:** Claude Opus 5.5 (`claude-opus-5-5`, runtime-stated), Claude Code
subagent, at the author's request. Web gathering delegated to one Sonnet
subagent (same family, not an independent review); every primary source cited
below that carries a claim used in a recommendation was re-fetched by the writer
or is marked otherwise.
**Base:** `origin/main` at `ea71df6e`; specimen `origin/hoard-2026-10-29`
(PR #1975, head `68b01d64`).
**Status:** audit and recommendations. It writes no rule, skill, prompt or
AGENTS.md text; every change below is the author's call.
**Companion:** the state-of-the-art survey [dream-research.md](dream-research.md),
updated in place the same day (§ "State of the art, 2026-10-29").

Labels: **[O]** is an observation with its evidence; **[I]** is an inference
from observations; **[M]** is a measurement taken for this audit, with its
command and host (padme). Derived numbers show their arithmetic.

## 1. Summary

The pipeline does what its contract says, and the contract produces
accumulation. Roar records facts, hoard integrates the facts recorded since the
last accepted report, and nothing in the contract asks hoard to make the topic
set smaller, states what a topic is for, or measures whether anyone reads it.
Five consolidations have added 1,683 lines to topics and the index and removed
138. The consolidated store has grown from 15 KB to 120 KB in four weeks while
the Claude Code sessions it is meant to inform almost never open it. Meanwhile
a second store, Claude Code's native auto-memory, is injected into every
harness session, carries rule-like feedback the author dictated, and sits
outside roar, hoard and review.

The five findings that matter for a decision:

1. Hoard is delta-driven and has no output budget for topics; each run appends
   a dated section. Deletions are 4-13 % of insertions across five runs (§3.2).
2. Claude Code working sessions do not read repository memory: 0 `Read` calls on
   `memory/MEMORY.md` or `memory/topics/` in 148 main sessions since
   2026-10-15, against 77 % of Codex working sessions that do (§4.2).
3. Half the journal (183 of 380 entries) is review-attribution telemetry that
   roar must write for every reviewed PR, which design v8 §4 says the journal
   should not hold (§3.1).
4. The behaviour-shaping memory in Claude Code is native auto-memory: 28
   unreviewed notes, injected at every start, one of which states its own
   disagreement with `rules/git.md` (§4.3).
5. Current evidence (2026) says consolidation by repeated LLM rewriting can
   degrade a memory below no memory at all, and that coding-agent memory
   systems rarely beat a no-memory baseline. The harness has no outcome
   measurement that would tell whether its memory helps (§5).

## 2. What was audited

| Layer | Files read |
|---|---|
| Contract | `AGENTS.md` § Project memory, § Project memory boundary; `memory/HOARD.md`; `skills/{roar,hoard,brood}/SKILL.md`; `skills/roar/runbooks/capture.md`; design v8 `conception/2026-09-10-dragon-memory-design.md` |
| Store | `memory/` on `origin/main` and on `origin/hoard-2026-10-29`; git history of every accepted hoard |
| Injection | `scripts/on-start-context.sh`; `adapters/codex/hooks.json`; `adapters/README.md`; `scripts/resident_census.py`; `tests/test_on_start_memory_injection.py`, `tests/test_rules_resident_budget.py`; `scripts/census/memory-recall.py` |
| Native stores | `~/.claude/projects/-home-haduong--agents/memory/` (28 files); `~/.codex/memories_1.sqlite` (row counts only); `~/.pi/agent/` |
| Transcripts | Claude Code `~/.claude/projects/*agents*/**/*.jsonl`; Codex `~/.codex/sessions/2026/10/`; Pi `~/.pi/agent/sessions/` — tool-call scans only, since 2026-10-15 |

## 3. The long-term pipeline

### 3.1 Capture (roar)

**[O]** Roar captures "significant" experiences: novelty, surprise, a
consequential failure or success, a near miss
(`skills/roar/runbooks/capture.md:10-17`). Routine completion "alone does not
require an entry" (`capture.md:16`).

**[O]** The same runbook requires a review-attribution record "for every
reviewed merged PR, even when routine completion produces no
significant-experience entry" (`capture.md:36-37`), written as a dated journal
entry by `attribution_record.py` through `memory-capture.sh`
(`capture.md:106-108`).

**[M]** `ls memory/journal/2026 | grep -c review-attribution` → 183 of 380
journal files (48 %). The journal holds 1.19 MB (`git ls-tree -l`, base
`ea71df6e`); `memory/evidence/` holds another 1.2 MB (`du -sh`).

**[O]** Design v8 §4 says the agent "ne reproduit pas un diff ou un compte
rendu de routine uniquement pour remplir le journal : les artefacts ordinaires
sont des preuves à citer" (`conception/2026-09-10-dragon-memory-design.md:118-119`),
and its acceptance table expects "Aucune entrée artificielle" for routine work
(`:302`).

**[I]** Attribution records are routine telemetry for the route grid, not
experiences. They are useful data, but storing them in the journal makes every
hoard read them: the fifth hoard's 187 Markdown sources included 98 of them
(fifth report, line 28), and its writer split the reading across five helpers
because the journal alone was about 120K tokens (fifth report, line 10).

**[M]** Journal entries per day rose from a median of about 8 in the first half
of October to 38, 51 and 21 on 27-29 October (`ls memory/journal/2026 | cut -c1-10 | uniq -c`).
Raids drive the rate: every merged PR adds at least one record.

### 3.2 Consolidation (hoard)

**[O]** Hoard reads "the entries of `memory/journal/YYYY/` not yet covered by
an accepted report" (`memory/HOARD.md:13-15`); a blob already examined "is
processed: cite its revision, do not re-import its content as new"
(`HOARD.md:23-25`). The pass is therefore defined by its new input.

**[O]** The three functions are pruning, merging and refreshing
(`HOARD.md:34-41`). Pruning requires a recorded reason and retained source
references (`HOARD.md:34-36`); merging must preserve "source links,
conditions, exceptions and unresolved contradictions" (`HOARD.md:37-39`);
verified quotations are carried "verbatim … never paraphrase, condense or
merge them away" (`skills/hoard/SKILL.md:69-71`). The only size bound is the
100-line index (`HOARD.md:110-112`, `AGENTS.md:74-75`). Topics have none.

**[O]** Neither the design nor HOARD.md states what a topic is for, beyond
"connaissances consolidées avec sources" (design `:38`). The design's
acceptance criteria test preservation, provenance, idempotence and authority
(design `:297-308`); none tests compactness or usefulness to a later session.

**[M]** Net change to `memory/topics/` and `memory/MEMORY.md` per hoard
(`git show --numstat` on the commit adding each report; PR #1975 by
`git diff --numstat origin/main...origin/hoard-2026-10-29`):

| Hoard | Date | Lines added | Lines removed | Removed / added |
|---|---|---:|---:|---:|
| Pilot | 2026-10-02 | 29 | 17 | 59 % |
| Second | 2026-10-07 | 403 | 19 | 5 % |
| Third | 2026-10-13 | 514 | 69 | 13 % |
| Fourth | 2026-10-15 | 195 | 8 | 4 % |
| Fifth (PR #1975, open) | 2026-10-29 | 542 | 25 | 5 % |

**[M]** Topic bytes on `origin/main` (`git ls-tree -r -l` at the last commit of
each day): 15,404 (10-03), 39,448 (10-08), 72,226 (10-14), 84,363 (10-16),
84,555 (10-29); 119,743 on the PR #1975 branch (derived: sum of the eleven
edited topics' new sizes plus the unchanged acceptance-trial topic).

**[O]** The topics grow as chronological registers. On the PR branch,
`ci-and-test-suite.md` keeps its opening scope "2026-10-02 to 2026-10-13" (line 3)
and then appends "## Later measurements (2026-10-14 to 2026-10-15)" (line 87) and
"## Later measurements (2026-10-15 to 2026-10-29)" (line 113);
`raid-review-and-merge.md` appends "Later review and integration evidence
(2026-10-13 to 2026-10-15)" (line 231) and "Later evidence (2026-10-15 to
2026-10-19)" (line 275); `shared-checkout-concurrency.md` appends "Refresh:
2026-10-15 to 2026-10-29" (line 112). The new 11.9 KB topic
`merge-flow-and-review-evidence.md` is scoped by date ("2026-10-19 to
2026-10-29", line 1).

**[O]** Supersession is marked in place rather than removed: the fifth report
lists "Pruning by supersession" as annotations that a claim is now history
(report line 58 onward), and the topic diff removes 25 lines in total. The
`ci` topic still lists the test count series 1640 → 3041 by date (branch
line 115 onward), a figure no later session can act on.

**[I]** Top structural causes of accumulation, in order of weight:

1. **The unit of work is the delta.** Hoard is asked to integrate what is new.
   Old topic text is only revisited when a new entry touches it, so the
   default fate of a claim is to stay.
2. **Removal costs more than addition.** Adding a sourced sentence needs one
   link; removing one needs a reason, retained references and a report line,
   and every preservation clause (conditions, exceptions, contradictions,
   verbatim quotations) argues for keeping. Under uncertainty a careful
   writer keeps.
3. **Topics have no job and no budget.** Without "a topic holds what a future
   session would act on, in at most N bytes", the safest reading of
   "consolidated knowledge with sources" is an evidence register. The
   date-scoped headings show the writer took that reading.
4. **The input is inflated by telemetry.** Half the journal is attribution
   records (§3.1), so a hoard spends its context reading data that should not
   become topic prose, and it summarises some of it anyway (the fifth hoard's
   new topic carries "the 98 attribution records with their capture friction").
5. **Nothing measures use.** No signal tells hoard which topics were read or
   which advice changed an outcome (§4.2), so completeness is the only
   quality it can show.

The author's reading of PR #1975 ("accumulative rather than distilled") is
confirmed by the measurements. The doubt that stale memories were retired is
partly confirmed: the fifth hoard corrected nine stale claims (report § Second
pass), but by annotation; no topic shrank.

### 3.3 Implementation from memory (brood)

**[O]** Brood is explicit-only (`skills/brood/SKILL.md:7`), reads accepted
reports and topics, and may "annotate, simplify or decay consolidated topics"
(`:73-76`). `git log --all -i --grep=brood` shows its adoption (PR #1187,
2026-10-05) and no later run.

**[I]** The only actor allowed to decay topics with a project change has not
run. Distilled lessons therefore have no exit from memory into procedure:
roar and hoard are barred from proposing rules (`AGENTS.md:64-67`), which is
sound, but the barrier plus an unused brood means lessons stay as topic prose
indefinitely.

## 4. Injection: what reaches a model, and when

### 4.1 Task memory at session start

**[M]** `python3 scripts/resident_census.py` (padme, base `ea71df6e`):

| Channel | Chars | ~Tokens (derived at 2.8 chars/token) |
|---|---:|---:|
| `rules/` resident (workflow, git, claude-code, guards) | 18,317 | 6,542 |
| `AGENTS.md` import | 3,822 | 1,365 |
| Native auto-memory index (largest project; harness: 4,252) | 14,484 | 5,173 |
| Skill names and descriptions | 6,282 | 2,244 |
| Agent descriptions | 604 | 216 |
| Total | 43,509 | 15,539 |

**[M]** `scripts/on-start-context.sh` prints 706 bytes without a project root
and 1,112 bytes with `CLAUDE_PROJECT_DIR` set (`wc -c`). It no longer prints the
memory index: `tests/test_on_start_memory_injection.py:1-7` pins the removal,
reasoning that AGENTS.md already tells the session to read the index.

**[O]** Resident rules reach Claude Code only (`~/.claude/rules` symlinks); the
hook comment says the resident rules "have no room left and reach Claude
only" (`on-start-context.sh:18-22`). Codex and Pi receive `AGENTS.md` natively
and the same start hook (`adapters/codex/hooks.json`, `adapters/README.md:227-231`).
The rules budget is a ratchet at 18,350 chars (`tests/test_rules_resident_budget.py:61`),
raised three times since 2026-09-24 (docstring, lines 40-60).

**[O]** Repository memory is pull-only on every runtime: `AGENTS.md:25-28`
asks the session to read `memory/MEMORY.md` at task start and open relevant
topics. Design v8 §3 says so explicitly: "Aucun hook commun ne garantit cette
lecture … son respect reste une propriété comportementale" (design `:75-76`).

### 4.2 Is repository memory read?

**[M]** Scan of tool calls in transcripts dated from 2026-10-15
(`python3 -I conception/2026-10-29-memory-system-audit/repo_mem_reads.py 2026-10-15`
and `codex_mem.py ~/.codex/sessions 2026-10-15`, same directory, run on padme;
a session counts once per channel):

| Runtime, arm | Sessions | Read index or topic (Read tool) | Any shell command naming index/topics |
|---|---:|---:|---:|
| Claude Code main, working | 148 | 0 | 2 |
| Claude Code main, maintenance (roar/hoard/lair) | 70 | 0 | 17 index, 5 topics, 55 journal |
| Claude Code subagents, working | 2,649 | 1 | 38 index, 35 topics |
| Codex sessions with harness AGENTS.md, working, with tool calls | 468 | — | 360 (77 %) |
| Pi sessions with harness AGENTS.md | 4 | — | 0 |

Positive controls: the maintenance arm's shell channel fires (55 of 70 sessions
touch the journal), and the Read channel fires on `rules/` paths in 116
transcripts of the same directories. Limits: the Codex "maintenance" split is a
keyword heuristic on the user turn; Pi's sample is four sessions; `Grep` by
content is invisible to the scan.

**[I]** The AGENTS.md instruction works on Codex and is almost never followed
on Claude Code. The likely reason is that Claude Code already shows a memory
index at start, the native one (§4.3), which satisfies "read the memory index"
in the model's reading. This is a hypothesis; a ten-session A/B with native
auto-memory off would settle it.

**[O]** The existing census `scripts/census/memory-recall.py` cannot see
repository topics: its path pattern accepts `memory/<name>.md` only
(`memory-recall.py:57`) and its shell pattern only native prefixes
`feedback|project|reference|user` (`:69`).

### 4.3 Native auto-memory

**[O]** Claude Code loads the first 200 lines or 25 KB of
`~/.claude/projects/<project>/memory/MEMORY.md` into every session; topic files
are read on demand; the store is shared across worktrees of one repository; it
can be disabled with `autoMemoryEnabled: false` or
`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, or relocated with `autoMemoryDirectory`
([Claude Code memory docs](https://code.claude.com/docs/en/memory), accessed
2026-10-29).

**[M]** The harness's native store holds 28 files, all modified 2026-10-09 to
2026-10-29 (`ls -l`), index 4,252 bytes. Across hosts' projects: 46 indexes, 1,182
notes (`ls ~/.claude/projects/*/memory/*.md | wc -l`).

**[O]** Several native notes are rules in substance: "check CI once, never
--watch/sleep loops", "ticket-only PRs: /merge immediately", "Night mode: an
escalation goes to Fable to finish, not to the author"
(`feedback_dont_idle_on_background.md:19`). `feedback_prose_edits_are_on_main.md`
ends: "`rules/git.md` still says main is read-only … so the written rule and
this preference disagree", against `rules/git.md:9`.

**[O]** Design v8 accepted this exposure: native memories "restent actives …
peuvent influencer les sessions avant leur ingestion ; une instruction seule ne
garantit pas que l'agent ignore une note contradictoire" (design `:269-271`).
Hoard reads native notes "only as attributed sources" (`HOARD.md:18-21`); the
fifth hoard saw the index and used no note body (report § Coverage).

**[I]** In Claude Code the de facto long-term memory is the native store: it is
injected, written in imperative form, read by every session, and governed by
nothing. The reviewed repository store is governed by everything and read by
Codex. The fifth hoard's open question 4 (night mode versus "calls by right
are never delegated") is a native note colliding with a rule; the collision
surfaced only because the same fact also reached the journal.

**[O]** Codex native memories exist (`~/.codex/memories_1.sqlite`; tables
`stage1_outputs` and `jobs` empty, `consolidation_progress` one row). Codex
documents them as off by default and warns not to use them as the only home
for required rules ([Codex memories](https://learn.chatgpt.com/docs/customization/memories?surface=app),
accessed 2026-10-29 by the research subagent, not re-fetched). Pi has no
built-in memory (pi-mono docs, same caveat).

### 4.4 Short-term memory and handoffs

**[O]** `STATE.md` is 27 lines and 4,371 bytes; its Handoff section is a run of
long paragraphs listing closed trackers (e.g. "Forge-less review (tracker
1252, closed 2026-10-28 …)"). It is read on instruction (`AGENTS.md:15`), not
injected. Compaction guidance is one line: preserve modified files, test
commands and the plan (`rules/workflow.md:184-186`). Claude Code re-injects
the project-root instruction file after `/compact` (Claude Code docs, as
above); the native index is re-loaded with it.

**[I]** STATE.md shows the same accumulation pattern as topics on a small
scale: closed work stays as narrative. It is outside this audit's
recommendations except as a note for lair.

## 5. Comparison with current practice

Sources and dates are in the survey's 2026-10-29 section
([dream-research.md](dream-research.md#state-of-the-art-2026-10-29)).

| Function | Harness mechanism | Current practice (2025-2026) | Gap |
|---|---|---|---|
| Capture | Roar journal entry per "significant" episode plus one attribution record per reviewed PR | Mem0 (April 2026) single-pass ADD-only extraction; Codex memories from idle chats, skipping short sessions; Anthropic dreams read raw sessions directly | Telemetry shares the episodic store; capture rate scales with merges |
| Consolidation | Hoard over new journal entries, rewriting topics in place, PR-reviewed | Anthropic dreams write a *separate* output store from 1-100 sessions, reviewed then attached or discarded; Letta dreaming with optional review and a defrag skill that restructures memory into about 15-25 files | No size target or restructure step; output is a diff on the old store, so old text survives by default |
| Forgetting | Supersession marked in place; journal append-only; git history | Graphiti invalidates with validity intervals and queries current state; Mem0 keeps old facts and ranks current ones first at retrieval | Topics serve current and past state in one text; no "current only" view |
| Evidence on consolidation | None measured locally | "Useful Memories Become Faulty…" (2026): repeated LLM consolidation first helps then degrades, sometimes below no memory; raw episodes competitive | Hoard is exactly a repeated LLM rewrite of the same topics |
| Retrieval | Pull: index read on instruction, `rg`/`grep` on topics and journal | Files plus a coding agent beat RAG on agent-experience recall (LongMemEval-V2: 72.5 % vs 48.5 %); Letta file tools on LoCoMo 74.0 % (vendor result) | Mechanism matches the evidence; Claude Code does not use it (§4.2) |
| Injection | Rules resident (Claude only, ratcheted); AGENTS.md native on all three; native auto-memory index on Claude | Anthropic guidance: smallest high-signal context, just-in-time retrieval, notes outside the window; Claude Code: CLAUDE.md under 200 lines, auto-memory 200 lines / 25 KB | Budgets exist for rules, not for native memory; two indexes compete in Claude |
| Context files | AGENTS.md and rules as the instruction channel | Gloaguen et al. (ICLR 2026): context files do not generally raise task success and cost over 20 % more inference; useful for non-standard practices | Supports the existing rules budget; argues against growing resident memory |
| Evaluation | Preservation, provenance and authority tests; v8 acceptance trial | VibeMemBench (2026): 11 of 12 solver × memory-system pairs did not beat no memory on repository tasks, while injecting verified experience helped by 1.1-4.5 points | No outcome measure: nobody knows whether memory helps |
| Native memory | Claude auto-memory on, unreviewed, injected; Codex memories present, empty | Codex docs: required rules belong in AGENTS.md, not memories; Claude docs: auto-memory is context, not enforced configuration | Rule-like native notes bypass review; one contradicts a rule |

## 6. Recommendations

Prices are author-hours (the author's own time to decide and review); agent
time is not priced. Options are independent unless stated.

| # | Change | Author-hours | Trade-off |
|---|---|---:|---|
| R1 | **Give topics a job and a budget.** Define a topic as the current guidance a future session would act on, with a per-topic byte cap (for example 6 KB) and a total cap below today's 85 KB; dated evidence stays in the journal and hoard reports. Edit HOARD.md and the hoard skill. | 1.5 | Loses evidence detail in topics (still one link away); a cap invites over-compression, which ACE's "brevity bias" warns about, so the cap should bind on history, not on conditions and exceptions. |
| R2 | **Make each hoard a rebuild, not a delta.** Hoard re-derives every topic from the journal and the previous topic, writes it fresh, and reports the net byte change; the author accepts a run only if it is net-neutral or explains growth. | 1 | Costs more model tokens per run; a rewrite from scratch can drop a caveat a delta would keep. Pair with R1's exception rule and the existing second pass. |
| R3 | **Move attribution records out of the journal** into their own data path (for example `memory/evidence/attribution/` or git notes, where the review evidence already lives), excluded from hoard input. | 0.5 | One more path for the route grid's reader to follow; hoard loses sight of capture-friction episodes unless roar also writes a normal entry when capture fails. |
| R4 | **Settle the two-store question in Claude Code.** Option a: turn native auto-memory off for the harness (`autoMemoryEnabled: false` in project settings) and have roar journal what the author dictates. Option b: keep it, and have each hoard list every native note, then the author either moves it into a rule by explicit request or deletes it. Option c: keep it as is and disclose. | a: 1, b: 0.5 per hoard, c: 0 | a removes the only memory Claude Code reads today, so pair it with R5; b keeps fast capture of author preferences at a recurring cost; c leaves rule-like text unreviewed and contradictions surfacing by chance. |
| R5 | **Restore an index in Claude Code's start context** (reverse the removal pinned by `test_on_start_memory_injection.py`) or point `autoMemoryDirectory` at a repository path. The hook route costs about 2.0 KB per session. | 0.5 | Adds resident bytes on every Claude session; worth it only if R6 shows the index is then used. Does nothing for Codex, which already reads it. |
| R6 | **Measure use and outcome.** Extend `scripts/census/memory-recall.py` to repository paths on all three runtimes, and run one small outcome trial: the same ten harness tickets with and without the topics, judged on rework and reviewer findings. | 2 | The outcome trial costs model spend and author review; without it every recommendation here is a guess about usefulness. VibeMemBench's result makes a null plausible. |
| R7 | **For PR #1975:** either accept it as the last delta hoard and run the next one under R1-R2, or reroll it now under R1 with the same ledger. | accept 0.5; reroll 1 | Accepting preserves a correct, sourced record of two busy weeks and lets R1 be designed on it; rerolling avoids merging 38 % topic growth that a later run must undo. |
| R8 | **Run brood once on the harness**, scoped to decaying topics and listing lesson candidates for the author, to test whether the exit from memory to procedure works. | 1.5 | Needs an explicit crystallisation request with a destination; may conclude "no change", which is a valid result. |

Recommended default: R3 and R6 first (cheap, they inform the rest), then R1
with R2 at the next hoard, and R7 as "accept, then rebuild". R4 waits for R6's
read counts. Total for the default path: about 5.5 author-hours.

## 7. What this audit did not establish

- Whether reading topics changes outcomes. No outcome data exist (R6).
- Why Claude Code skips the AGENTS.md read instruction. The native-index
  explanation (§4.2) is a hypothesis.
- Codex and Pi native memory content: only the Codex SQLite row counts were
  read, and Pi has no store. Codex and Pi documentation claims come from the
  research subagent's fetches and were not re-fetched by the writer.
- Transcript scans cover sessions from 2026-10-15 on one host (padme); doudou
  was not scanned.
- The quality of individual topic claims. This audit measured shape and size,
  not correctness; the fifth hoard's own second pass checked 24 quotations.
