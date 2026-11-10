# Memory system, as built

This page describes the repository memory system as it runs on 2026-11-10, in
the harness (the pilot) and in every project that adopts the convention. It is
the blueprint: the procedures live in the skills it names, and history lives in
git and in the documents listed under § History. When the system changes,
update this page in the same merge request.

## Purpose and principle

Shared memory lives in the project's repository as Markdown, read and searched
with ordinary agent tools (`rg`, `grep`, file reads) and reviewed through merge
requests. There is no memory server, database, embedding or ranking model. The
circuit is **factual capture → consolidation → review → accepted knowledge**,
with an optional last step, **brood**, that turns accepted knowledge into
project rules or skills on explicit request. Capture does not interpret;
consolidation may produce no lesson and never invents one; a memory never
overrides a harness rule.

## Stores

| Path | Content | Written by | Shape and budget |
|---|---|---|---|
| `memory/journal/YYYY/YYYY-MM-DD-<slug>.md` | Factual episodes: context, observations, outcome, evidence | roar (capture), smelt (retirement records only) | Append-only; a correction is a new entry linking the original. About 300 words is guidance. |
| `memory/topics/<department>.md` | The as-built guide to one department of the project: current claims, each linked to its journal episode | smelt | At most 8 pages; each at most 4096 bytes outside its `Sources` section. Sections: current guidance, hazards, open questions, sources, fallback. |
| `memory/topics/user-rulings.md` | The author's rulings, kept as contextual jurisprudence | smelt (preserves), brood (integrates and retires), author (edits) | Exempt from the topic template; an overflow is reported, never cut to fit. |
| `memory/MEMORY.md` | Index: one line per department plus local location facts | smelt | At most 40 lines, including headings and blank lines. |
| `memory/skills/<skill>.md` | Case notes for one skill: one to four dated, sourced cases, each ending in a `Use:` line | smelt (case-note lane) | About 400 words. |
| `memory/smelts/YYYY-MM-DD-<slug>.md` | Consolidation reports: blob ledger of sources read, changes, measured net bytes, native-note table, open questions | smelt | Only a report merged into main counts as processing. |
| `memory/evidence/` | Bulky evidence; `attribution/` holds review-attribution records | roar (attribution), tasks that produce evidence | Outside consolidation input. |
| `~/.claude/projects/<project>/memory/` | Claude Code's native auto-memory, notes the author dictates or the runtime saves | Claude Code | Outside the repository and its review; kept by author choice (ticket 1350, option b). |

Codex native memories exist but are empty (off by default); Pi has no native
store.

## Lifecycle

**Capture (roar).** After a merge, roar writes a journal entry for a
significant experience: novelty, surprise, a consequential failure or success,
a near miss, or a departure from an existing principle. Routine completion
needs no entry. It also records review attribution for every reviewed merged
PR, with `scripts/attribution_record.py --capture-pr N`, into
`memory/evidence/attribution/`. Capture goes on the wrap-up branch with the
rest of roar's bundle. Runbook: `skills/roar/runbooks/capture.md`.

**Consolidation (smelt).** Smelt rebuilds each topic from its previous page and
the journal episodes it links, one department at a time, instead of appending.
It prunes superseded claims (the journal and git keep them), merges overlaps
and refreshes stale context, then reports the net byte change measured by
`scripts/memory_sizes.py`. It checks coherence across indexed memories and
against harness rules, and files a ticket for every contradiction it leaves
exposed. It ends with two lanes: a read-only table of native auto-memory notes
with a proposed disposition each (nominate for brood, promote to repository
memory, delete), and a re-selection of skill case notes. It opens a merge
request and never merges itself; the author's acceptance is the review. Skill:
`skills/smelt/SKILL.md`, editorial detail in
`skills/smelt/references/consolidation.md`.

**Cadence.** Lair suggests a smelt in its conclusion when at least five journal
experiences are not yet covered by an accepted report. It neither waits nor
launches one. Smelt runs on explicit invocation, in a fresh session. There is
no timer.

**Promotion (brood).** On a separate explicit request naming scope and
destination, brood reads accepted reports and topics, judges whether the
evidence supports a specific change (including removing a bad rule), and
implements it as a project change or files a harness nomination. It integrates
author rulings into rules or skills and retires the integrated ones to the
journal. Neither roar nor smelt proposes rules. Skill: `skills/brood/SKILL.md`.

## Delivery: what reaches a model, and when

| Channel | Claude Code | Codex | Pi |
|---|---|---|---|
| AGENTS.md instruction to read `memory/MEMORY.md` and relevant topics (pull) | Loaded | Loaded | Loaded (first AGENTS variant per directory plus home) |
| Repository index injected at session start | No (removal pinned by `tests/test_on_start_memory_injection.py`) | No | No |
| Skill case note pushed at skill load, once per session, by `scripts/skill-case-notes.sh` | PostToolUse on Skill, UserPromptSubmit on a typed `/skill` | UserPromptSubmit on `$skill`, PostToolUse on a shell read of a `SKILL.md` | `read` handler in `adapters/pi/extensions/idh-guard.ts` |
| Native auto-memory index injected at start | Yes (first 200 lines or 25 KB) | Empty | None |

Repository topics and the journal are therefore pull-only everywhere; case
notes are the one push channel.

## Measurement

`scripts/census/repo-memory-reads.py --since <date>` counts sessions that read
the index or topics, per runtime and kind, with the maintenance sessions as
positive control. On padme since 2026-10-15 (ticket 1346): Claude Code main
working sessions 1 of 148, Codex 142 of 570; doudou Claude Code 0 of 5.
`scripts/census/memory-recall.py` covers native notes. One outcome trial
(DreamBench-SWE, 95/180 with memory against 89/180 without, p = .52) was
inconclusive; the author chose monitoring over further trials (ticket 1354).

## Private material

The tracked memory has the repository's public audience, which is not a
privacy clearance. The capturing agent judges each entry's audience before the
first byte is written, and `scripts/memory-capture.sh` enforces the result:
a public entry is plain Markdown; a not-cleared entry is piped from stdin into
`age -r <recipient> -o <entry>.age`, so plaintext never exists in the working
tree. Decrypt with `age -d -i <key> <entry>.age`. The per-project key is one
age X25519 identity at `~/.config/keys/memory/<sha256[:16] of the normalized
origin URL>.age`, normalized by stripping scheme, user, default ports (22 for
ssh, 443 for https, 80 for http) and the `.git` suffix, then lowercasing, so
every transport of one project derives one key. A non-default port is kept and
derives a new key. The key is created by `age-keygen -o` on first private
capture and never tracked; repository content names this derivation, never a
key file. An ignored directory or a branch of a public repository is not a
private store. Smelt re-encrypts only consolidated topics, never a journal
entry. Limits of ciphertext at rest: the [pilot declaration](pilot.md).

## Adopting the convention in a project

Resolve the project repository first; never copy another project's memories.
Merge the [reading section](templates/AGENTS.md) into the project's AGENTS.md
without replacing its other instructions, and copy the
[index](templates/memory/MEMORY.md), adapting its links. The
[journal template](templates/memory/journal/2026/2026-10-01-example.md) and
[topic template](templates/memory/topics/example.md) are examples; remove their
placeholders. A project keeps no consolidation prompt: its local facts (where
its rules, native store or import annex live) are lines in the index or a
`SOURCES.md` the index links. Journal files stay in their original year
directory; on a slug collision choose a new slug, never overwrite. No UUID,
mandatory frontmatter or executable schema is required. A relative CLAUDE.md
symlink to AGENTS.md may help; verify each runtime's loading rather than
claiming injection.

## Known gaps

- Claude Code almost never reads repository memory (§ Measurement). The likely
  reason, that its injected native index satisfies "read the memory index", is
  a hypothesis not yet tested.
- The behavior-shaping memory in Claude Code is the native store, outside
  review. Smelt lists it for the author at each run, but notes act on sessions
  before triage, and a planted contradicting note was adopted by Codex in the
  0918 trial.
- No measurement shows that the memory improves outcomes.
- The journal outgrows one context; smelt reads it by department.

## Open design questions

These questions come from ticket 1443 (author request of 2026-11-02, design
input of 2026-11-08), closed on 2026-11-10 with its content folded here. They
await the author when the memory design is reopened; nothing here authorizes an
implementation.

The author asked to formalize that memories the user explicitly requests are
first class compared with automatic memories. Rulings are already a separate
class (`memory/topics/user-rulings.md`). The author's 2026-11-08 input treats
explicit versus discovered as an axis independent of topic: one topic can hold
both kinds, rather than forcing rulings into a topic template.

- How to keep explicit provenance and tell it apart from automatic inference?
- What does first class guarantee: retention, recall priority, precedence in
  contradictions, or something else?
- How to allow correction, obsolescence and retirement without silently
  erasing the author's intent?
- How to separate a request to remember, a factual truth and a normative
  instruction? A memory does not become a rule by itself.
- Should injectors that run before a skill merge explicit and implicit
  memories? Should memory injection mimic Claude Code's hook patterns, such as
  pre-skill injection or injection on reading a given file type?
- How should the explicit/implicit axis affect selection and presentation
  without erasing provenance or contextual scope?
- Should the repository index return to session start (audit R5), given the
  read census?

## History

The v8 design ([French, 2026-10-01](../2026-09-10-dragon-memory-design.md)) and
its [delivery plan](../2026-09-11-memory-implementation-plan.md) set the
circuit; the [pilot declaration](pilot.md), [source inventory](source-inventory.md),
[evaluation protocol](evaluation-protocol.md) and [results](evaluation-results.md)
record its trial. The [2026-10-29 audit](../2026-10-29-memory-system-audit.md)
found the consolidation accumulated text; departments with a byte cap,
rebuild-not-delta (ticket 1349), attribution out of the journal (ticket 1347)
and native-note triage (ticket 1350) followed. Case notes come from the
[case-notes design](../2026-10-31-skill-case-notes.md). The native and
shared-store DREAM helpers are retired ([retirement record](legacy-retirement.md));
the consolidation skill was named dream, then hoard, then smelt.
