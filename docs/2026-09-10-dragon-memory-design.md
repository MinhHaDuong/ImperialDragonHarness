# The Dragon's memory: measured assessment and design proposal

**Status:** draft · 2026-09-10 · v4 · four reviews received, see §9
**Baseline:** figures reproduce at `6187ad8` (main just after #885)
**Runtime:** Claude Code 2.1.267 — §2.4 records what it does; the architecture
below does not branch on it
**Superseded versions:** [v0](./2026-09-10-dragon-memory-design-v0.md),
[v1](./2026-09-10-dragon-memory-design-v1.md),
[v2](./2026-09-10-dragon-memory-design-v2.md) and
[v3](./2026-09-10-dragon-memory-design-v3.md), frozen with their section
numbering intact so the four reviews' citations resolve

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

Memory is **21.1%** of what a session carries before its first question. Only
one project index is resident in a given session, so the largest is the upper
bound rather than the sum.

**Read that share for what it is.** The denominator is the preamble, which is
the session's smallest input; every tool result, file read and turn of
conversation that follows dilutes it. 21.1% is the share at its maximum, not
the share over a session, and the two numbers support opposite conclusions
about urgency.

**And read what the resident cost prices.** The index sits in the system
prompt, so after the first turn it is a cache read, not a fresh input. Cost per
turn is therefore an order below what a chars-to-tokens conversion suggests,
which is why the "28× the payload it delivers" figure below invites the wrong
optimisation. Two costs survive that correction and neither is measured here:
attention dilution, and what an adapter without auto-load must inject to stand
the harness up on another runtime. The second is the one that makes the
resident tier's size an architectural quantity rather than a billing one.

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

Two limits on that figure. The window is **2026-06-01 to 2026-09-10, 101
days**, and the instrument has no date filter — so an entry written in August
had a third of the exposure of one written in June, and the rate needs a
per-entry exposure denominator rather than one corpus-wide count. And a body
opened by a subagent serves its root session without that session opening
anything, so the 3.57% subagent row and the 11.01% working row overlap by an
amount nobody has attributed.

Cost against use, summing each project's index over the sessions it served:
4 784 923 chars served for 86 body opens — **55 638 chars (~19 900 tokens) per
body actually opened**, against a body averaging ~2 000 chars. The index costs
roughly 28× the payload it delivers. The title-only pass in #875 brings this to
33 773 (~12 100 tokens), about 17×.

### 2.4 The recall channel exists, and is switched off

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

**Zero injections.** Every appearance of a memory body, in 5 753 sessions, is
a session opening the file itself.

Earlier versions of this document read that as an absence. It is not. The
channel is in the runtime, and reading the binary rather than the traces says
what the traces cannot:

- **Per-turn recall exists.** A selector picks up to five bodies matching the
  last user prompt and appends them as a `relevant_memories` attachment,
  truncated to 200 lines or 4 096 bytes each. `description:` is its retrieval
  key, exactly as the platform documentation says.
- **It is gated, and the gate is observable.** It opens on a remote flag or on
  `CLAUDE_MEMORY_STORES`. Both are closed here — this session's own system
  prompt carries the raw `MEMORY.md`, which is reachable only with both closed,
  and the corpus holds no BM25 index and no pinned entries.
- **The gate is a switch between two regimes, not a feature toggle.** The same
  condition that opens recall **hides the `MEMORY.md` index.** Index-resident
  and recall are mutually exclusive.

**The design does not branch on this.** An earlier version made the flag an
axis and described two regimes; that was a mistake, and it is the reason this
section was unreadable. The architecture in §5 has one shape, and it survives
the flag in either position for one reason: **the index is generated from the
bodies.** If the gate opens and the index stops being loaded, what is lost is a
regenerable view, not a store. The directories, the files and their frontmatter
are untouched, and they are what the harness owns.

Two facts from this section do carry into the design. The runtime already
builds a derived index — it sorts bodies by modification time, takes the 200
most recent, and renders each as `- [name](path): description` with an overflow
line saying how many it did not list. That is the mechanism §5 adopts, with a
better score than recency. And `description:` is the runtime's retrieval key
whenever any selection happens, which is a reason to write it well that does
not depend on any flag.

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

**What the duplicates record is not a retrieval failure.** v1 read them as
sessions that failed to find entries already there, and made that the argument
for the door. On the ref it does not hold: **zero** of the pairs are
same-project, so no writer's resident index could have surfaced the entry being
duplicated — a session sees its own project's index and the harness tier,
nothing else. The multiplicity is what per-project tiering produces, not what
retrieval failure produces. Of the pairs reproduced, roughly half are lexical
false positives; the real yield for deduplication is 17–21 pairs, not ~38.

**The `gh_pr_edit` family says something the design does not.** Seven bodies in
seven project directories, 2026-05-11 to 2026-09-04, none promoted. The
workaround entered `rules/git.md` on 2026-09-04 — the same day as the seventh
copy — and no eighth has appeared. The mechanism that ended the repetition was
the resident **rules** channel, not the memory tier that exists to carry
cross-project lessons.

That is the uncomfortable finding of this section. The harness already has a
working way to make one lesson visible in every session, and it is a rule edit
through a pull request. The promotion tier built for the same purpose has
promoted four entries in four months and has one candidate waiting. Before
repairing promotion, the program should ask whether it is repairing a road
nobody drives — and, if it is kept, what it does that a `rules/` line does not.
The honest answer may be scope: a rule is resident everywhere and therefore
costs everywhere, while a promoted memory is resident everywhere at 100
characters. That is an argument, and this document has not made it.

**Maintenance is the same order as consultation.** 726 body writes against 974
body reads across all arms — writes do not exceed reads, as an earlier draft of
this line said, but they come within a quarter of them. The memory system
spends nearly as much effort maintaining itself as every session spends
consulting it.

The provenance populations reconcile once the dead records are separated out:
651 records before the repair include 12 whose body no longer exists, so 639
live bodies were covered; 308 uncovered project-tier bodies plus one in the
harness tier is 309 backfilled; 651 + 309 = 960, and 960 − 12 = **948 live
bodies covered**, against 954 files carrying 948 distinct slugs. The corpus
count of 949 in §2.2 is that population off by the alias collapse.

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

## 4. What is actually broken

The list is shorter than earlier versions claimed, because most of what they
called defects were consequences of a retention policy this document no longer
proposes.

1. **Promotion leaves the project copy live.** The skill writes a `# PROMOTED`
   stub; `skills/dream/provenance.py:349` counts a body dead only when its head
   starts `# DELETED`. Five stubs are therefore still counted live, and they
   inflate the frequency count that drives the next promotion. A one-line
   marker fix, not a design ticket.
2. **Duplicate detection is filename equality.** A lexical pass over slug words
   finds 17–21 genuine pairs against the 1 candidate the current rule yields.
   About half of any lexical pass is false positives, so a confirmation step is
   part of the ticket, not an afterthought.
3. **The frontmatter is not uniform enough to rank on.** 47 bodies carry no
   type field, and two shapes are in use (`type:` at top level versus
   `metadata.type`). Ranking reads frontmatter, so this blocks §5's index
   generation. The 28 filename prefixes are cosmetic by comparison —
   `metadata.type` already holds exactly the four designed values.
4. **Nothing declares when a memory stops being true.** Every entry is
   currently treated as valid forever, and the TTL table meant to handle this
   gives `feedback` — 74% of the corpus — no threshold at all.

What is *not* on this list, and was: unindexed bodies, orphan collection, the
absence of a corpus cap, and the decay pass's zero yield. §5 dissolves all four
rather than repairing them.

## 5. The architecture

**The store is the bodies. The index is a view.** One directory per project,
one file per memory, tracked in git. `MEMORY.md` is not a store and is not
edited by hand: it is regenerated from the directory, and it lists the top N by
score, with N chosen to hit a size. Everything below N is still there, still
tracked, still findable.

That single move settles most of what earlier versions argued about. An entry
is never "dropped from the index" — it ranks below the cut and comes back when
its score changes. Orphan bodies stop being a class, since being unlisted is
the normal state of most of the corpus. And a budget stops being a wall to
crash into: it *defines* N.

**But it does not make demotion harmless, and v3 claimed it did.** §2.3 says
what residency buys is *unprompted awareness* — knowing a lesson exists when
nothing in the conversation would surface it. The cut protects **reachability**,
which is a different property. For a memory whose whole function is to stop an
action before it is taken, falling below the cut is functionally deletion: the
agent never forms the hypothesis that would send it to the search, because not
forming it is exactly the failure the memory existed to prevent. You do not
search for what you do not know to look for.

So the cut needs a floor that ranking cannot cross. **A body may declare that
it must stay resident**, and the generator honours that declaration before it
honours any score. The claim "demotion has no failure mode" is withdrawn; the
honest claim is that demotion has no failure mode *for entries whose value is
retrieval*, and a declared class exists because not all of them are.

This also disposes of a test that would have passed while the defect ran: "no
entry becomes unreachable" is true of a guard memory the moment after it stops
working. The test that means something is that no declared entry falls below N.

**P1 — Nothing is deleted.** Not by age, not by size, not by score. The only
removal from a project directory is promotion, which moves a lesson up rather
than out. The harness tier, being the top of that movement, has no removal at
all. Disk and consolidation time are the costs of keeping a body; context is
not, because context is paid by the view.

*On growth, and why there is no file-count cap.* A cap on the number of files
is a deletion mechanism wearing a budget's clothes, and it would delete for a
counting reason — the failure earlier versions of this document warned about
and then proposed anyway. What actually degrades as the corpus grows is the
consolidation pass, whose duplicate detection is quadratic: a thousand bodies
is half a million pairs and milliseconds, ten thousand is fifty million and
seconds, and somewhere past that the pass needs blocking rather than the corpus
needing pruning. Search does not degrade meaningfully in that range — 49 ms
today, well under a second at ten times the size — and neither does version
control.

So the corpus gets an **alarm, not a cap**: the run records the body count and
its own wall-clock duration in its provenance, and the trend is visible long
before it is a problem. The right threshold is on the pass's duration, which is
the thing that hurts, rather than on a file count, which is a proxy for it.

Waiting is the correct choice here precisely because this failure is visible
and costs nothing when it arrives: the pass gets slow, and the fix is
algorithmic. Contrast the resident index, which could not wait — its budget
gate's only legal move was to delete index lines, and that destroyed
reachability. **Cap what fails destructively; alarm on what fails visibly.**

*Who writes what, and why the generated index conflicts with nothing.* Two
write sets, disjoint by construction, one writer each. Sessions create **bodies**
— one file per memory, so two sessions adding two memories never touch the same
file. Only the consolidation pass writes **`MEMORY.md`**. A regenerated,
score-ordered index would collide with concurrent work if anything else wrote
it; nothing does, so the objection that generating it reintroduces the merge
conflict the file grain exists to avoid does not apply here. It would apply
immediately if a second writer appeared, which is the rule to defend.

Two consequences follow, and both are load-bearing:

- **A new memory is invisible until it is scored.** The lesson exists on disk
  the moment it is written and does nothing until the next pass. The session
  that wrote it already knows it, so the interval costs only other sessions —
  and its length is set by how often the pass runs, which makes the cadence a
  design parameter rather than an operational detail.
- **Scoring is therefore the admission gate**, and it is free. Nothing reaches
  residency without passing through it, so a bad write has a window in which it
  can be caught before it costs anyone context. Every earlier version of this
  document wanted admission control and proposed a mechanism for it; the
  single-writer rule supplies one as a side effect.

**P2 — The door is a search, not a second file.** A full catalogue kept as a
file is a materialised view that can go stale and needs its own collector. The
bodies already carry `name:` and `description:` in frontmatter, so the
catalogue is a grep — 49 ms over the whole corpus, and never out of date
because it is derived from the source. What is resident is one line saying the
store can be searched and how.

**P3 — Validity is declared at writing and checked by a program.** A memory
says what it is true *while*: a path exists, a pattern is still present in a
named file, a tool is below a version. It must be an executable predicate from
a small closed grammar, not a sentence — prose degrades into a comment nothing
can check.

**The predicate is checked twice, and fails differently each time, because the
two moments have different audiences.**

*At writing, it fails closed.* The predicate must parse and must evaluate, and
it must evaluate **true** — a memory born already expired would never rank, so
writing one is an error, not a record. A malformed or unevaluable predicate is
rejected there and then, while the author is present and still knows what they
meant.

*At scoring, it fails open and reports.* Nobody is present, so an
unevaluable predicate leaves the entry valid and raises a lint. A silent expiry
loses a lesson for a reason no one will ever see; a stale line costs a place in
a list. Between two silent failures, prefer the visible one.

These two rules are not in tension and should not be harmonised by a later
reader. Fail closed where a human can fix it, fail open where none can.

*What this covers, measured rather than assumed.* On a sample of 54 real
bodies, the grammar could **express** a condition for about a quarter, could
**evaluate** what it expressed for rather fewer, and was the exact truth
condition for fewer still. The dominant way a memory in this corpus dies is not
a file changing but an event happening — a decision reversed, a tool replaced,
a practice abandoned — and no predicate over the working tree sees an event.

So `valid_while` is an instrument for the minority of the store it can describe,
and this document should not claim more. For everything else the default is
"valid until something says otherwise", which is where the corpus already was.
Naming that plainly matters, because a mechanism that covers a quarter and is
described as the retention policy leaves three quarters unmanaged behind a
sentence that says they are handled.

Because expiry only unranks, it is **reversible**. A tool that regresses
revives its memory at the next scoring pass with no human action. That is the
argument for keeping everything, and it is the one earlier versions never made:
deletion cannot be undone, and unranking can.

**P4 — Rank to fill N, not to evict.** The score decides display order over a
store that keeps everything, so a mis-ranked entry costs a place in a list, not
its existence. This is what makes a composite score safe here when two reviews
judged it unsafe: with eviction on the other side of it, a bad weight destroys
work; with a grep on the other side, it hides a line. That safety is bounded by
the awareness limit above — for a declared-resident entry the cut is not a
display decision — which is why the declaration overrides the score rather than
feeding into it.

**Validity is not importance, and the score needs both.** `valid_while` answers
*is this still true*. It says nothing about *does this matter*, and the two come
apart in both directions: a memory can be impeccably true and worth nothing, or
shaky at the edges and the only thing standing between an agent and an
expensive mistake. A design that ranks on validity alone would surface a wall of
correct trivia and bury the lesson that matters.

So importance is its own axis, declared like validity and read like it. What
feeds it, at least: the cost of rediscovering the thing if it is forgotten;
whether the memory *prevents* an action or merely *answers* a question, since
only the first fails silently when it is not resident; and how wide its scope
is. Observed use belongs here too and stays secondary for the reason P4 already
gives — it counts opens, and an entry whose title carried the lesson is never
opened.

**P5 — Annotate at the point of writing.** Durability, the validity condition
and what the entry supersedes are known when a memory is written and guessed at
forever after. The writer declares them; the scorer reads them. Alongside them
the store keeps what it already keeps and what #885 backfilled: provenance —
which projects an entry came from, and whether the claim was stated by the
owner, observed by an agent or inferred by one — the creation date, and the
inputs the score reads. None of that is display material; it is what lets a
reader arbitrate between two entries without a program having to.

**P6 — Measure the mechanism, not the intention.** Every gate ships with a
positive control, because this system's characteristic failure is a pass that
reports success over the entries it can see. Three instances were found while
writing this document, twice in the author's own new code, and a fourth in its
own central claim — see §9.

### Why flat files, and not a database

The store is one file per memory in a directory tracked by git. A database
belongs here as a view over that, never as a replacement for it. Five reasons,
one of which decides.

**Merge granularity decides it.** One file per memory is the grain concurrent
sessions need: two sessions adding two memories never conflict. A SQLite file
under git is a binary blob — no diff, no merge, no review, and a conflict on
every concurrent write. This harness runs parallel sessions as a matter of
course, and worktree isolation exists for that reason. A single absorbing store
would put the contention back at the centre of the thing the rest of the
architecture is built to avoid.

**There is no performance problem to solve.** 1 001 files, 1.73 MB, a full grep
over the corpus in 49 ms. At the observed growth — +110 entries across 13
consolidation runs — a corpus ten times this size is 17 MB and the grep stays
under a second. A database would answer a scale that does not exist and is not
arriving.

**git is already the audit log.** Provenance, dates, diffs, blame, and the
pull-request gate the out-of-family review called the only serious defence
against memory poisoning. A database has to rebuild every part of that.

**Portability is architectural**, the firmest result in the calibration note:
retention logic must live outside the model to transfer between runtimes. Plain
files are readable by any adapter — Pi, Codex — without a line of code.

**The runtime already reads flat files.** A database would need a translation
layer whose output is precisely what would otherwise have been written
directly.

What a database genuinely buys — full-text search, and structured queries over
the score — is available as a *derived* index: built from the files, rebuilt on
demand, never committed. That is exactly the status this design gives
`MEMORY.md`, so it costs no new principle.

One more thing absorbing the project tiers into a single store would dissolve:
the partition that keeps the resident index small. Only one project index is
loaded per session, and a single store would have to reconstruct that partition
anyway. Tiering is a context-budget constraint, not an artefact of the file
layout.

What would change this: a corpus large enough that regeneration costs real
time, or a synchronisation need beyond what git resolves. Neither holds today,
and the second would be a synchronisation problem rather than a storage one.

**The corollary is a database that is thrown away.** The consolidation pass may
load the whole corpus into whatever structure it likes — a vector store, an
embedding index, a scratch table — compute duplicates and scores there,
regenerate the indexes, and then **delete it**. Nothing about that violates a
principle, and it removes the last failure mode a derived index can have: an
index that persists can drift from its source, and one rebuilt from source on
every run cannot. It is the same reasoning that makes `MEMORY.md` generated
rather than authored, applied one level down.

This is also how the duplicate detection gets better. Lexical slug matching
finds roughly 43 candidate pairs of which 17–21 are genuine, so about half of
what it proposes is noise a human has to reject. Embeddings raise precision on
exactly that task, and the pass is periodic and offline, so it can afford to be
slow. Two conditions keep it honest: the embedding model runs locally, or the
consolidation pass acquires a network dependency the rest of the design does
not have; and the model's identity is recorded in the run's provenance, because
a ranking that silently changes when a model is upgraded fails P6.

At this scale the database is optional and the *pattern* is the point. A
thousand entries is a thousand vectors — a few megabytes, and a brute-force
comparison in microseconds. What matters is the shape: compute in memory, emit
files, discard everything else. The durable record is the bodies and their
provenance; the vectors never earn a place in git.

**One thing may survive the pass: an embedding cache keyed by content hash.**
A thousand bodies is a thousand embeddings, and recomputing all of them every
run is the one real cost of throwing the database away. Keying the cache by the
hash of the body removes the reason the database had to go: a changed body has
a different hash, so it misses and is re-embedded, and a stale entry is not
reachable by construction. Only new and modified bodies cost anything, which
makes a run proportional to what changed rather than to the corpus.

The cache is not in git — it is regenerable, binary, and belongs in a local
ignored directory, at roughly three megabytes for the current corpus. Deleting
it must cost time and nothing else, and a run that finds no cache must produce
the same indexes as a run that finds a full one. That equivalence is the test
this ticket ships with, in the spirit of P6: a cache nobody has proved
disposable is a store wearing a cache's name.

### What the model decides, and what it must not

Finding candidate groups is mechanical: embeddings cluster, lexical matching
proposes, predicates evaluate, scores compute. Deciding whether a group is one
lesson, and writing the merged text, is judgment, and no amount of similarity
settles it — two entries can be near-identical in wording and record different
conditions, which is why roughly half of what lexical matching proposes is
noise. So the consolidation pass needs a model, and the design is better for
saying exactly where.

**The model proposes a merge and writes the merged body.** It names the group,
argues that it is one lesson, produces the text that replaces it, and declares
what the result supersedes. That is authorship, and it is the one thing in this
pipeline no predicate can do.

**The model decides nothing about retention.** Not what ranks, not what
expires, not what is still true. Ranking is a score over declared fields;
expiry is a predicate a program evaluates. Keeping judgment out of those two is
what makes an index reproducible from the store alone — regenerate twice, get
the same file — and reproducibility is the property that lets anything else be
tested.

**The pass writes bodies too, and must not race or clobber.** It merges, it
tombstones, it regenerates: a run has to hold a lock, so two passes cannot
interleave, and it has to refuse a checkout with uncommitted bodies rather than
overwrite work whose author it cannot see. Both failures are cheap to prevent
and expensive to notice — an overwritten uncommitted body has no ancestor to
recover from.

**A merge is reviewed before it lands.** It is the only operation here that
replaces text with different text, so it is where both silent loss and
poisoning would enter. Merges into the harness tier reach every session, and
they go through a pull request like any other harness change; the
out-of-family review was blunt that human review of the shared tier is the only
serious defence, and this is the operation that needs it.

**And a bad merge is recoverable, which is the point of keeping everything.**
The originals are tombstoned, not deleted, so a group wrongly conflated can be
read back and split. A design that deleted its inputs would have to be right
the first time; this one only has to be reviewable. Two things go into the
run's provenance so a later reader can tell why a merge looks the way it does:
the model's identity, and the prompt it ran under.

### Contradiction between ranked entries

Keeping everything means an entry and its correction coexist, and both can rank.
Asked directly — can the index be checked for contradiction? — the literal
answer is no: the index carries titles and links, and a contradiction lives in
the claims. Any check has to read the bodies of the entries that ranked. That
is at least tractable, because only N of them ranked.

Three mechanisms, in the order they should be reached for:

1. **Declared supersession.** An entry may name what it replaces. The generator
   then refuses to rank both, and the newer one carries a line saying what it
   corrects. This is not detection but declaration, and it is exact, because the
   case that matters most — an entry written *because* the old one turned out
   wrong — is precisely the case where the writer knows.
2. **The near-miss set is free.** The consolidation pass already computes
   lexical similarity to find duplicates. Pairs that are similar enough to
   suspect and different enough not to merge are, by construction, the
   candidate set for contradiction. It costs nothing beyond a report.
3. **A semantic pass over the ranked set, as a report and never as a gate.**
   Reading N bodies for conflicting advice is a judgment, so it fails P3: it is
   not reproducible and it cannot be trusted to block anything. It can surface
   pairs for a human.

Most contradictions should not survive to need any of this. `valid_while`
retires the entry that became false, so the usual shape — advice correct until a
tool was fixed — expires rather than competing. And every entry carries its date
and its provenance, so where two do compete a reader can arbitrate: memory is
data, not instruction, and dated data with a source is arbitrable. The check is
only needed where both entries look equally current, which is the narrow case
declared supersession already covers.

### What the consolidation pass does

Periodically, and not per session: pool the project directories, detect
duplicates across them, and promote what recurs into the harness tier,
tombstoning the project copies as it goes. Then re-score and regenerate the
affected indexes.

**The harness tier is a project directory like any other.** It has its own
memories, written directly by sessions working on the harness; its index is
generated, ranked and capped by the same rule; and it is pooled for duplicate
detection on the same footing as the rest — compared against, and a full
participant in the pairs the pass finds.

**One asymmetry, and it is a direction, not a status.** Promotion moves a
lesson *up* into the harness tier and never back down. So when a pair straddles
the two tiers, the resolution is settled in advance: the harness copy survives,
the project copy is tombstoned, and nothing new is created because the lesson is
already where it belongs. That single case covers the class defect 1 belongs
to — a project copy left alive beside an entry already promoted.

The consequence easiest to miss: **the harness index is capped like the others,
and it matters more there.** It is resident in *every* session, nothing in it is
ever removed, and if deduplication starts working its membership only grows.

**Each tier has its own budget, because a session loads both.** §2.1 counts
them as separate resident channels and they are: the harness index and the
project index are both in the prompt, so neither constrains the other and each
gets its own N. Nothing here trades one against the other.

That makes the current figure a trap worth naming. `tests/test_resident_census.py`
budgets the hook at 500 characters, and `memory/MEMORY.md` uses 369 of it for
four entries. **500 is not a design decision.** It is a ratchet stamped on a
tier that happens to be nearly empty — it records where the harness tier is,
not what it should carry — and a tier meant to hold every lesson that proved
itself across projects, sized at four or five entries, is a category error
rather than a tight budget. Consolidation is expected to surface 17 to 21
genuine cross-project pairs, which is the first real evidence of what the tier
is for.

So the number to set is what the harness tier must carry, and the ratchet
follows it. Read the other way round — the ratchet as a constraint promotion
must fit inside — promotion would start *reducing* a lesson's reach past the
fifth slot, moving it out of a project index where it was visible into a queue
below a cut where it is not. That inversion is the thing to avoid, and it is
avoided by sizing the budget rather than by rationing promotions.

## 6. Proposed changes

Four tickets, no waves. They are ordered by dependency, and only the third
depends on anything.

1. **Marker fix** — `# PROMOTED` counted live (defect 1). One line, plus the
   test that would have caught it.
2. **Index generation** — regenerate `MEMORY.md` from its directory as the top
   N by score, with the overflow line, for project tiers and the harness tier
   alike. Idempotent: regenerating twice changes nothing.
3. **Frontmatter normalisation and the validity predicate** (defects 3, 4) —
   one type field, one shape, an optional `valid_while` from a closed grammar,
   and a resolver the scorer calls. Ticket 2 can ship with recency as its score
   and gain this one later.
4. **Consolidation pass** — pool, detect duplicates, promote, tombstone
   (defect 2), then trigger ticket 2's regeneration.

Dead, and worth naming so nobody revives them: the decay pass and its TTL
table, the corpus cap, the orphan collector, and the full-catalogue file. The
first two are replaced by P1 and P3, the last two by P2.

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

## 9. Decision requested, and the review record

**Approve the four tickets in §6.** T1 and T2 stand alone; T3 upgrades T2's
score; T4 needs T1's marker fix under it. No decision is left open: the one
that was — what an unevaluable `valid_while` means — is settled in P3, valid at
scoring time and rejected at write time.

**Review record.** Three study reports commissioned before this draft
([Fable](./2026-09-10-memoire-agent-fable.md),
[Perplexity](./2026-09-10-memoire-agent-perplexity.md),
[ChatGPT](./2026-09-10-memoire-agent-chatgpt.md)) fed it. Three reviews answer
it: [Claude](./2026-09-10-dragon-memory-design-review-claude.md) and
[ChatGPT](./2026-09-10-dragon-memory-design-review-chatgpt.md) on v0, neither
with repository access; and
[Fable](./2026-09-10-dragon-memory-design-review-fable.md) on v1, with access,
which is how it caught that v1's central claim was false. All are
non-normative.

**How v3 differs, and why.** v2 argued for a retention policy — decay, a corpus
cap, an eviction score — and spent §2.4 on two runtime regimes. The owner
settled the architecture instead: keep everything, delete nothing, promote on
duplication, and treat the index as a generated top-N view. That dissolves four
of the seven defects v2 listed rather than repairing them, removes half the
ticket plan, and makes the composite score safe by putting a search rather than
an eviction on the other side of it. The validity predicate replaces the TTL
table, which the third review showed was wired to nothing for 74% of the
corpus.

The document no longer asks the questions of §8; three reviews answered them,
and where an answer changed the design it is in §5 rather than in a reply.

---

## Annex A — The plan as filed

Eight tickets, in `tickets/`. The tracker is `0909`; it carries the wave order
and the reasoning, and this table is the summary.

| id | title | wave | depends on |
|---|---|---|---|
| 0909 | Tracker: memory retention program | — | — |
| 0908 | Promotion marks the project copy dead in the form the walker reads | 1 | — |
| 0911 | Frontmatter migration: one type field, one shape | 1 | — |
| 0913 | Retire the dead machinery, ship the resident search line | 1 | — |
| 0910 | Generate the index as the top N of its directory | 2 | 0913 |
| 0914 | `valid_while` grammar, resolver, scorer, `supersedes` | 3 | 0910, 0911 |
| 0915 | Enforce the validity predicate on the write path | 3 | 0914 |
| 0912 | Consolidation: deterministic pooling, grouping, reports | 4 | 0908, 0910, 0914 |
| 0916 | Model-judged merge, reviewed promotion, tombstoning | 5 | 0912 |

The seams follow one rule: **everything a program can decide ships before
anything a model decides.** 0912 proposes and 0916 judges; splitting them is
what lets the first half be tested at all.

Exit criteria are gated on fixtures rather than on counts, because a count-based
criterion passes vacuously the day after it is written — "the 47 untyped bodies
are typed" is true of an empty set, and "no entry becomes unreachable" is true
at the exact moment a guard memory stops working. Each ticket names the fixture
that would fail without the fix.

Not tickets, deliberately: a corpus cap, a decay pass, an orphan collector, a
full-catalogue file. §5 removes the need for all four, and 0913 deletes what
survives of them. The embedding database and its cache are parked rather than
planned: the design describes them, nothing depends on them.

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
