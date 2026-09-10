> **FROZEN — v1, superseded.** The text the Fable second-round review read,
> kept so its findings F1–F8 and its verification ledger resolve against the
> wording they judged. Do not amend it and do not act on it: the current
> version is
> [`2026-09-10-dragon-memory-design.md`](./2026-09-10-dragon-memory-design.md).
> v1's central amendment — duplicate slugs as retrieval failures, hence the
> door — was refuted on the ref and is gone from v2. See also the frozen
> [v0](./2026-09-10-dragon-memory-design-v0.md).

# The Dragon's memory: measured assessment and design proposal

**Status:** reviewed and amended · 2026-09-10 · v1
**Reviews received:** in-family and out-of-family — see §9
**Baseline:** `origin/main` at `b79c2ad`, plus open PRs #875 and #885 where noted
**Superseded version:**
[`2026-09-10-dragon-memory-design-v0.md`](./2026-09-10-dragon-memory-design-v0.md)
— the text the two reviews read, frozen with its section numbering intact so
their citations resolve

This document exists to be attacked. It reports what the harness's memory
system does, what it was measured to do, where those two differ, and what is
proposed. Section 8 lists the questions where an outside reading is most
useful; a reviewer short on time should read §2, §4 and §8.

Conventions: every number is characters unless marked. Token figures use
2.8 chars/token, derived against `/context` on 2026-09-10 — **derived, not
measured**, and about 45% worse than the chars/4 rule of thumb because
identifiers and paths tokenize badly. Character counts are the contract.

---

## 1. What the system is

The harness is a set of files under `~/.claude`, tracked in git, that a coding
agent loads at session start. Memory is one channel among six.

**Two tiers.** Each project has a directory `projects/<slug>/memory/` holding:

- `MEMORY.md` — an **index**, one line per memory: `- [Title](filename.md)`.
- one **body** file per memory, with YAML frontmatter (`name:`, `description:`,
  `metadata.type` ∈ {user, feedback, project, reference}) and a prose body.

Above them sits a harness tier, `memory/`, holding entries **promoted** because
they proved to matter in more than one project, plus `memory/.provenance.json`
recording, per entry, its originating projects, `first_seen`, `last_confirmed`
and promotion status.

**What is resident.** At session start the runtime places in the system prompt:
the project's `MEMORY.md`, and (via a hook) the harness `MEMORY.md`. **Bodies
are not resident.** They are read on demand, by the agent, with a file-read
tool. This is the pointer-and-payload split the whole design turns on.

**What maintains it.** A skill, `/dream`, runs per project at wrap-up. It
classifies each entry (NOOP / ADD / UPDATE / DELETE), extracts five "key
insights", rewrites the index, records provenance, evaluates promotion
candidates (entries seen in ≥2 projects), and runs a decay pass flagging
entries unconfirmed for 90 days.

On paper this is a competent design: admission control, per-type caps, a TTL
table, a promotion tier, a decay sweep. The measurements below are about how
much of it is actually connected.

## 2. Measured assessment

Instruments and commands are in Annex B. Everything here was measured on
2026-09-10 over the local corpus and 5 753 session traces (4.2 GB).

### 2.1 What a session pays

| channel | chars | ~tokens |
|---|---|---|
| `rules/` (auto-loaded rule bodies) | 35 926 | 12 831 |
| import (`CLAUDE.md` + its `@` chain) | 9 646 | 3 445 |
| hook (harness memory index) | 367 | 131 |
| **memory (the project's own index)** | **14 061** | **5 022** |
| skills (name + description only) | 6 261 | 2 236 |
| agents (name + description only) | 350 | 125 |
| **total** | **66 611** | **23 790** |

Memory is **21.7%** of what a session carries before its first question. Only
one project index is resident in a given session, so the largest is the upper
bound rather than the sum.

**Read that share for what it is.** The denominator is the preamble, which is
the session's smallest input; every tool result, file read and turn of
conversation that follows dilutes it. 21.7% is therefore the share at its
maximum, not the share over a session, and the two numbers support opposite
conclusions about urgency. The traces can supply the second one. Reported here
because the resident cost is what an adapter without auto-load must inject, and
that cost is paid at the maximum.

### 2.2 The corpus

| | |
|---|---|
| project memory directories | 47 |
| live bodies | 949 |
| tombstones | 35 (3.6%) |
| index entries | ~905 |
| bodies listed by no index | 13 |
| bodies in a directory with no index at all | 5 |
| tracked entries whose body no longer exists | 12 |

Bodies cost nothing until opened: in the harness project, 212 529 characters of
bodies against 10 368 of index. **Corpus growth is nearly free; index growth is
the tax.**

### 2.3 Is the index used?

The one thing residency buys is *unprompted awareness*: knowing a lesson exists
when nothing in the conversation would surface it. Measured by classifying
every trace and counting sessions that open a memory body. A maintenance arm
(sessions running a memory skill) serves as positive control.

```
maintenance (positive control)  132 / 246   53.66%
working (the measurement)        35 / 318   11.01%
  consumer projects only         23 / 273    8.42%
subagent runs                   185 / 5189   3.57%
```

**About one working session in nine follows the index into a body.** But:

> **50 distinct bodies were opened by working sessions, out of ~900 entries.**

**94% of the index has never been followed** in the window. The cost is paid on
the whole list; the traffic lands on a twentieth of it.

Two limits on that figure. The window's length is not stated anywhere in this
document and must be, because an entry written last week cannot have been
followed for as long as one written in March: the rate needs an exposure
denominator per entry, not a single corpus-wide count. And a body opened by a
subagent serves its root session without that session opening anything, so the
3.57% subagent row and the 11.01% working row overlap by an unmeasured
amount.

Cost against use, summing each project's index over the sessions it served:
4 784 923 chars served for 86 body opens — **55 638 chars (~19 900 tokens) per
body actually opened**, against a body averaging ~2 000 chars. The index costs
roughly 28× the payload it delivers. The title-only pass in #875 brings this to
33 773 (~12 100 tokens), about 17×.

### 2.4 No recall channel was detected

The platform's memory instructions say a body's `description:` decides recall
relevance. **On this runtime, nothing fires.**

Two probes over all 5 753 traces: 25 distinctive mid-body sentences, then 40
`description:` lines (a channel injecting only summaries would be invisible to
the first). Positive control: 32 of the 40 appear somewhere in the traces.

```
found somewhere            32 / 40      <- probe works
  in a tool_result (read)     113
  anywhere else                24
     20  the agent writing the body
      2  the file re-attached after a write
      2  the text inside a shell command
```

**Zero injections detected.** Every appearance of a memory body, in 5 753
sessions, is a session opening the file itself.

Stated precisely: no verbatim injection of the probes was detected in the
channels these traces expose. That is weaker than "no channel exists" — a probe
reads what the traces record, and anything placed in the system prompt, or
paraphrased through a compaction summary, would be invisible to it. The
distinction does not change the design. Depending on no automatic recall is
robust whether or not one exists, and it is the only assumption that survives a
runtime upgrade. It changes what may be claimed from the measurement.

This is the load-bearing finding of the document, because it inverts the
obvious remedy: **an entry dropped from an index is not demoted, it is
unreachable.** Any plan to shorten the resident index by unlisting entries
silently deletes them.

### 2.5 The maintenance machinery is mostly not connected

| mechanism | designed | measured |
|---|---|---|
| eviction (`DELETE`) | on falsehood or redundancy | **2 deletions in 13 runs**, +110 entries net |
| decay (90-day flag) | flag unconfirmed entries | **covers promoted entries only: 3 of 960** |
| decay yield today | — | **0 entries flagged**, while **191 exceed 90 days** |
| provenance coverage | every entry recorded | **651 of 949** before #885; 960 after |
| promotion | entries seen in ≥2 projects | **3 candidates** in ~40 projects |
| promotion cleanup | project copy becomes a tombstone | **not done** — 4 live orphan copies |
| type vocabulary | 4 types | **28 distinct prefixes, 24 of them singletons** |
| index cap | 200 lines | not yet binding (largest 141) |
| corpus cap | — | none exists |

Two of these deserve restating because they are not mere gaps:

**The decay pass flags nothing.** It iterates the store, skips anything not
promoted, and 3 entries are promoted, none of them old. So a mechanism
described as the harness's forgetting policy has, today, a yield of zero over
191 eligible entries.

**Promotion is blocked at the root.** Entry identity is filename equality, so
the same lesson under two names never merges. A lexical pass over slug words
(Jaccard ≥ 0.5, cross-project) finds **35 pairs involving 49 slugs**, which
would take candidates from 3 to ~38 — a twelvefold increase. Examples:
`feedback_gh_pr_edit_broken_use_rest` / `..._use_api_patch` /
`feedback_gh_pr_edit_graphql_broken` are one lesson under three names. **Plain
lexical matching suffices**; the "semantic slug matching" deferred to a future
version looks over-engineered.

**But read the duplicates as a symptom before reading them as a supply of
candidates.** One lesson written three times under three names is three
sessions that failed to find the two entries already there. That is a retrieval
failure, and it is the strongest local evidence for P2's door — stronger than
anything in §2.3, because it is a positive observation rather than an absence.
The rise from 3 to ~38 promotion candidates is therefore a count of past
retrieval failures, not a benefit being unlocked. Deduplication cleans the
record; only the door stops the next one being written. This is why the door
precedes T3 in the wave order below.

A second consequence for the promotion criterion itself: "seen in ≥2 projects"
measures how often the author repeats a mistake, not how general the lesson is.
A maximally general lesson learned once and never violated again scores zero.
The criterion is a usable heuristic for candidacy and should be labelled as
one, not as a measure of transferability.

**Maintenance is the same order as consultation.** 726 body writes against 974
body reads across all arms — writes do not exceed reads, as an earlier draft of
this line said, but they come within a quarter of them. The memory system
spends nearly as much effort maintaining itself as every session spends
consulting it.

The provenance populations need the same care: 949 live bodies less 651 covered
is 298, where §7 reports 308 without a record, and 960 covered after the repair
exceeds the 949 live bodies it covers. Different snapshots or different
populations can explain both; the document must say which, with a date against
each count.

## 3. What the literature calibrates

A survey of published work on agent memory (full version:
`docs/2026-09-10-portable-agent-memory-calibration.md`) yields three usable
results and one honest refusal.

- **Portability is architectural.** An architectural study across thirteen
  configurations concludes retention logic must live outside the model to
  transfer across runtimes. This harness satisfies it: policy is a skill over
  plain files under git. Index *shape* does not bear on portability; index
  *size* does, because an adapter without auto-load must inject the resident
  set itself.
- **The staged hybrid wins.** Six forgetting policies benchmarked (FIFO, LRU,
  Priority Decay, Reflection-Summary, Random-Drop, staged Hybrid): the hybrid
  takes the best composite (≈0.911) by running temporal → reflective
  consolidation → importance-based removal → cap. Its ranking is **normalised
  by token cost** — utility per token, so a long entry must earn its length.
  `/dream` today runs one of those four passes.
- **Byte budgets saturate near 10 KB, and past it get worse.** The one
  benchmark of write policies under fixed byte budgets finds coverage saturating
  at 10 240 bytes, with larger budgets *lowering* F1 because reduced eviction
  pressure admits low-value items. Utilisation is not the metric: the winning
  policy used 34% of budget for full coverage while a fill-everything baseline
  used 99% for 19%.
- **The refusal:** decay parameters are explicitly left to practitioners; no
  published η, κ or freshness threshold. Long-horizon benchmarks demonstrate
  failures without quantifying breakpoints. **The 10 KB knee is measured on a
  different task** (drift-event coverage in agent traces, not a resident
  orientation index) and is therefore an analogy, not a measurement on this
  corpus.

One result cuts against a natural instinct: **counting accesses cannot rank
this corpus.** 852 of 902 entries are tied at zero in working sessions. A
least-frequently-used policy over a corpus that is 94% zeroes is random
eviction with extra steps.

## 4. The seven defects

1. **Promotion leaves the project copy live.** The spec says it becomes a
   tombstone; the implementation does not do it. Four live orphans, and the
   frequency count that drives the next promotion is inflated by them.
2. **Decay does not reach project entries.** Coverage 3/960, yield 0 against
   191 eligible.
3. **The cap bounds the index, not the corpus.** Bodies accumulate unindexed —
   and with no recall channel, an unindexed body is unreachable, so the leak is
   silent loss rather than silent growth. Currently 18 bodies.
4. **Duplicate detection is filename equality.** 3 promotion candidates where a
   lexical pass finds ~38.
5. **No orphan collector.** Nothing sweeps bodies no index lists, or bodies in
   directories with no index at all.
6. **No composite retention signal.** Age, observed use and a durability
   annotation are all needed; #885 supplies the first two, the third does not
   exist.
7. **The type vocabulary has drifted.** 28 prefixes where the design has 4, 24
   of them singletons. Any per-type policy is meaningless until this is
   normalised.

## 5. Design principles proposed

**P1 — Tier, do not evict.** Bodies are free; the index is the tax. The
primitive is movement between tiers, not deletion. Nothing is deleted for size.

**P2 — Every tier has a door.** Because no recall channel fires, a demoted
entry must remain reachable by a deterministic act. The resident index carries
one line naming the full index — about 60 characters — and the full index lists
everything. Demotion moves an entry from the resident layer to that file, never
to nowhere.

**P3 — Freshness is deterministic.** Age comes from timestamps, not from a
model's judgment of whether a memory has become false. A criterion that fires
only on demonstrated falsehood, in a corpus where almost nothing becomes false,
deletes twice in thirteen runs — which is what it did.

**P4 — Rank by utility per token.** Composite score over age, observed use and
declared durability, divided by the entry's size. Observed use is a
**secondary** signal, for two reasons that do not go away: it is machine-local
and traces are prunable, so it is a floor; and it counts *opens*, while an
entry whose index title carried the lesson is never opened. A ranking that
evicts on it evicts the entries that worked best.

**P5 — Control admission, and annotate at the point of writing.** Durability is
known when a memory is written and guessed at forever after. The writer
declares it; the retention policy reads it.

**P6 — Measure the mechanism, not the intention.** Every gate proposed here
ships with a positive control, because this system's characteristic failure is
a pass that reports success over the entries it can see. Three instances were
found and fixed while writing this document, twice in the author's own new code.

## 6. Proposed changes

Grouped into waves by dependency. Tickets in Annex A.

**Wave 0 — the door (T8).** Everything that demotes depends on it, and nothing
in the original wave list built it. Both external reviews raised this
independently, and §2.5's duplicate pairs are the local evidence for it.

**Wave 1 — repairs, independent of each other.**
- Promotion tombstones the project copy (defect 1).
- Orphan collector: report bodies no index lists, then tombstone or relist
  (defects 3, 5). Report first: the decision is per-file.
- Lexical slug matching for promotion candidates (defect 4).

**Wave 2 — needs the provenance repair (#885) merged.**
- Extend decay to all entries, thresholds per type, following the TTL table
  that already exists in the memory skill and is currently wired to nothing
  (defect 2).
- Durability annotation at write time, and normalise the 28 prefixes to 4
  (defects 6, 7).

**Wave 3 — needs both.**
- Composite retention score, normalised per token (defect 6).
- Corpus cap per project, biting at write time.

**Ordering constraint:** the corpus cap comes after decay. Otherwise the cap
forces deleting what decay would have demoted, and bodies are lost for a
counting reason.

## 7. What is already done

- **#875** — the title-only index pass: the index line is a title and a link,
  the trailing hook having been a third copy of a sentence the body carries as
  `name:` and `description:`. 47 indexes, 198 636 → 111 021 chars (−44%); the
  largest 26 531 → 14 061. 139 entries whose link text was a filename were
  retitled first, since for those the hook was the only readable content.
  Carries the trace instrument and the measurements in §2.3 and §2.4.
- **#885** — provenance coverage: 308 live bodies had no record, invisible to
  promotion, decay and dedup at once. Backfilled with dates recovered from git
  history rather than the clock, plus observed read counts folded in from the
  traces. A coverage gate keeps it shut.
- **#883** (merged, by a parallel session) — a census of all six resident
  channels with per-channel budgets, and the chars/token ratio this document
  uses.

## 8. Questions for the reviewer

Ordered by how much a wrong answer would cost.

1. **Is §2.4 right?** It is a strong negative claim — no recall channel on this
   runtime — resting on two probes with one positive control. What would you
   run to falsify it? Is there a channel the probes would structurally miss?
2. **Does a resident index earn 5 022 tokens at an 11% hit rate?** The
   alternative is zero resident bytes plus an explicit "consult memory" step in
   the session-start ritual, which trades a standing cost for a per-session
   action and a reliability question.
3. **Is 94%-inert a demotion list?** It measures follow-through, not need: an
   entry whose title alone did its work is indistinguishable here from one
   ignored. How would you measure the silent-title effect without an A/B that
   removes entries and waits for a regression nobody would notice?
4. **Is a corpus cap justified when bodies are free?** The argument for it is
   maintenance cost and dedup tractability, not tokens. The argument against is
   that it forces deleting things that cost nothing to keep.
5. **Is durability the right axis for per-type TTL?** The four types
   (user / feedback / project / reference) mix subject matter with lifetime. A
   project fact can be permanent and a reference can rot.
6. **Is the composite score worth its complexity** given that one of its three
   inputs is a floor with a known inverted bias (P4), and the published
   parameters for the other do not exist?

---

## 9. Decision requested, and what these amendments changed

The draft asked six questions and proposed seven tickets, but never said what
it was asking the reader to decide. Stated now: **approve the wave order below
and the door as its prerequisite; defer T6 and T7 until T8 and T4 have run.**
If the program is not approved, the fallback is T1, T2 and T3 alone — the three
repairs are independently justified by the defects they fix and need no
retention policy above them.

One question is closed rather than answered. §8 asked how to measure the
silent-title effect without an ablation nobody would notice. The harness owner
treats context pressure as established, not as a hypothesis, so no ablation is
proposed and no benefit experiment gates the work. The argument for reducing
the resident tier is the context budget; it does not rest on §2.3's hit rate.

**Review record.** Three study reports commissioned before this draft
([Fable](./2026-09-10-memoire-agent-fable.md),
[Perplexity](./2026-09-10-memoire-agent-perplexity.md),
[ChatGPT](./2026-09-10-memoire-agent-chatgpt.md)) fed it. Two reviews answer
it: [Claude](./2026-09-10-dragon-memory-design-review-claude.md), in-family,
and [ChatGPT](./2026-09-10-dragon-memory-design-review-chatgpt.md), the
out-of-family read this draft asked for. Both are non-normative. The amendments
above take the points on which they converge — the missing door, deferring the
composite score, separating durability from type — plus the arithmetic and
scoping corrections each found alone.

---

## Annex A — Proposed tickets

Each is sized to one review unit. Dependencies are on the real prerequisite,
never on the tracker.

| id | title | wave | depends on | exit criterion |
|---|---|---|---|---|
| T0 | Tracker: memory retention program | — | — | all children merged, integration review |
| T1 | Promotion tombstones the project-level copy | 1 | — | the 4 live orphan copies become tombstones; a test asserts a promoted entry has no live project body |
| T2 | Orphan collector for unlisted memory bodies | 1 | — | a command reports the 13 + 5; each resolved to tombstone or relist; a gate keeps the set empty |
| T3 | Lexical slug matching for promotion candidates | 1 | — | candidates rise from 3 to the measured ~38; each merge confirmed inline before it applies |
| T4 | Extend decay to project entries, thresholds per type | 2 | #885 | the 191 aged entries are flagged; per-type thresholds read from the memory skill's TTL table |
| T5 | Durability annotation at write time; normalise the type vocabulary | 2 | #885 | 28 prefixes → 4; new memories carry a declared durability; a gate rejects an unknown type |
| T6 | Composite retention score, normalised per token | 3 | T4, T5 | score computed from age, use and durability; ranking reproducible from the store alone |
| T7 | Corpus cap per project, enforced at write time | 3 | T4, T6 | a cap exists and bites; exceeding it requires a consolidation before the write |
| T8 | The door: bounded resident index, full catalogue, targeted lookup | 0 | — | every live body resolves from the full catalogue; a demoted entry is retrieved by a tested operation; the resident index respects a character budget; an interrupted move is recoverable |

Not tickets, deliberately: the 12 tracked entries with no live body (fold into
T2), and the filename redundancy that is 47% of the trimmed index — measured,
and dominated by demotion, which returns 1.8× as much with no renames.

## Annex B — Reproducibility

Every figure above regenerates from two instruments and the local trace corpus.
Numbers were taken at `origin/main` `b79c2ad` with #875 and #885 applied.

```bash
# Resident cost per channel (merged, #883)
python3 scripts/resident_census.py

# Does the resident index get followed? (#875)
python3 scripts/census/memory-recall.py --out /tmp/memory.json

# Provenance coverage and observed use (#885)
python3 skills/dream/provenance.py backfill --root . --dry-run
python3 skills/dream/provenance.py usage --root . --dry-run

# Decay yield today
python3 skills/dream/provenance.py decay
```

Corpus counts (live bodies, tombstones, orphans, index entries) come from
direct filesystem walks; the walkers live in `skills/dream/provenance.py`
(`live_bodies`) and in the coverage test.

**Known limits of the measurement.** The trace corpus is one machine's and
traces are prunable, so every count derived from it is a floor. `Grep` carries a
pattern rather than a path, so a body found by content search is invisible to
the trace instruments; it measured 0 occurrences naming a body slug, so the
residue is small. Token figures are derived, not measured.
