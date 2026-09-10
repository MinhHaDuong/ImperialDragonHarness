# Portable agent memory: what the literature calibrates, and what it refuses to

Written 2026-09-10, to set method and thresholds for the harness memory tier
after the title-only index pass (PR #875). The question is narrow: **how large
should a resident memory index be, and by what rule should entries leave it?**

The short answer is that one paper gives a usable number, three give a usable
method, and the rest explicitly decline to give thresholds. That refusal is
itself a finding, and it points at a local measurement this repo can run.

## 1. Portability is an architectural property, and this harness already has it

The relevant result is [Control-Plane Placement Shapes
Forgetting](https://arxiv.org/pdf/2606.15903), an architectural study across
thirteen configurations varying where memory logic lives (in the model, in the
application, split), what is retrieved, and which backend stores it. Its
conclusion: **retention and forgetting logic must live outside the model** to be
portable. Policy embedded in model weights couples to a model version and does
not transfer; policy at the application boundary runs unchanged across
runtimes. The design rule it states is to treat the LLM as stateless and
implement forgetting at the boundary.

The harness satisfies this by construction — the policy is `/dream`, a skill
that reads and writes plain files under git, and nothing about it is in a
model. The [Memory Atlas](https://www.memoryatlas.dev/families/filesystem-markdown)
catalogues this as its own family (filesystem-markdown), and its practical
claim is the one that matters here: memory is portable across tools *because it
is just text*, with the `AGENTS.md` convention as the bridge.

Two consequences worth stating plainly, because they cut against a reflex:

- The wiki / knowledge-tree option discussed earlier is *not* better for
  portability. Both a flat index and a linked graph are plain files. What would
  cost portability is moving the retention decision into a vector store or into
  a runtime's own memory feature.
- The adapter question (Pi, Codex) is unaffected by index *shape* and entirely
  determined by index *size*, since an adapter without auto-load must inject
  the resident set itself.

## 2. Method: six policies have been compared, and the staged hybrid wins

[Forgetful but Faithful](https://arxiv.org/abs/2512.12856) proposes MaRS, a
retention schema, and benchmarks six forgetting policies against it: FIFO, LRU,
Priority Decay, Reflection-Summary, Random-Drop, and a staged Hybrid. The
**Hybrid takes the best composite score (≈0.911)**, by running the passes in
order — temporal, then reflective consolidation, then importance-based removal,
then a privacy filter. FIFO and LRU are cheapest and lose salient-but-old
items; Reflection-Summary preserves narrative coherence; importance-aware
methods retain what is salient despite age.

Its scoring formula is the piece worth importing:

```
imp(n) = α·type_weight(t_n) + β·recency(n) + γ·frequency(n)
score(i) = (Û_i − λ_priv·s_i) / w_i        # utility per token
```

Two details matter for this harness. First, `score` is **normalised by token
cost** `w_i` — the unit is utility per token, not utility, so a long entry must
earn its length. Second, MaRS allows **soft budget partitioning by type**
(`B^(epi)`, `B^(sem)`, `B^(soc)`, `B^(task)`), with the split tuned to equalise
marginal utility per token across slices. That is the defensible form of the
per-type caps `skills/memory/SKILL.md` already declares — a byte split, not a
count.

Measured against this, `/dream` today runs **one of the four passes**:
reflective consolidation. It has no temporal pass, no importance-based removal,
and its deletion criterion is neither. That is the mechanical explanation for
the observed record — 13 runs, +110 entries net, 2 deletions.

## 3. The deletion criterion is the defect, and it has a named fix

`/dream` deletes an entry when the model judges it contradicted or stale. [Don't
Ask the LLM to Track Freshness](https://arxiv.org/pdf/2606.01435) argues
directly against that arrangement: a model asked to arbitrate the freshness of
its own retrieved memory is reasoning circularly, and lacks a reliable
mechanism for temporal validity. Its recipe separates evidence extraction from
policy execution — **freshness from explicit timestamp metadata, not semantic
assessment**; newer supersedes older on direct contradiction; threshold
filtering below a configurable confidence.

The paper proposes the architectural principle without publishing an empirical
comparison, so this is a design argument rather than a measured result. But the
harness has its own measurement, and it agrees: a criterion that fires only on
demonstrated falsehood, in a corpus where almost nothing becomes false, deletes
twice in thirteen runs.

[SSGM](https://arxiv.org/html/2603.11768v1) supplies the decay form for the
temporal pass — a Weibull weight with a freshness cutoff:

```
w(Δτ) = exp(−(Δτ/η)^κ)        retain while w(Δτ) ≥ θ_fresh
```

κ < 1 gives fast early decay and a long tail; κ > 1 delays forgetting then
drops it sharply. **SSGM publishes no value for η, κ or θ_fresh** — explicitly,
"implementation left to practitioners". The harness's current 90-day
unconfirmed flag is this function with κ → ∞: a step at η = 90 days, applied
only to the five promoted entries.

## 4. The one real number: budgets saturate near 10 KB, and past it get worse

[WritePolicyBench](https://arxiv.org/html/2602.02574) is the only source found
that benchmarks **memory write policies under fixed byte budgets** — 1 024,
10 240, 102 400 and 1 048 576 bytes — which is exactly this repo's question.

| budget | best policy | F1 |
|---|---|---|
| 1 024 B | `priority_greedy` | 0.446 |
| 10 240 B | `priority_threshold` | **1.000** |
| 102 400 B | `priority_threshold` | 1.000 |
| 1 048 576 B | `priority_threshold` | 1.000 |

Three findings carry over:

1. **Performance saturates at ~10 KB.** Coverage tops out "once the budget can
   store essentially all labeled drift events"; the hundred-fold budgets above
   it buy nothing.
2. **A bigger budget can score worse.** Added capacity "reduces eviction
   pressure, allowing more low-value steps into memory; this increases recall
   but lowers precision and thus F1." Growth is not neutral even when it is
   affordable.
3. **Utilisation is not the metric.** At 10 240 B, `fifo_store_all` fills
   0.994 of the budget for 0.188 coverage, while `priority_threshold` uses
   0.337 of it for 1.000. A full index is evidence of a bad policy, not a
   working one.

Reading across to the context-length literature gives the same shape from the
other side: Chroma's [context rot](https://www.trychroma.com/research/context-rot)
study finds all 18 frontier models tested degrade as input grows, and the
Stanford multi-document result has accuracy falling from 70–75% to 55–60% once
~20 documents (~4 000 tokens) are in context. [Less Context, More
Accuracy](https://arxiv.org/pdf/2606.09900) reports accuracy peaking at
intermediate context size and declining with full history.

**Where the harness now sits.** After the trim the worst index is 14 061 bytes
and the ceiling is 14 500 — just above WritePolicyBench's saturation knee. The
pre-trim state was 26 531 bytes, in the region the same paper associates with
falling precision. The current number is therefore in the right zone by this
evidence, and the finding argues against ever raising it.

## 5. Growth is the expected regime, and stale reuse is the measured harm

[Memora](https://arxiv.org/html/2604.20006v1) measures memory-operation load
across horizons: 103.2 operations per persona weekly, 374.3 monthly, 1 171.4
quarterly — an 11.3× rise from week to quarter. Accretion is not a harness
pathology; it is what these systems do.

Its second result is the one that should set priorities. Its
Forgetting-Aware Memory Accuracy metric penalises answers that reuse
invalidated memory, and applying it **cut system scores by 18.2 to 29.5
points** — systems routinely reuse superseded memory while looking correct on
standard metrics. Memora likewise publishes no recommended budget: it
"demonstrates failures occur but doesn't quantify breakpoints."

## 6. Calibration for this harness

Ordered by evidential strength, weakest claims flagged.

| # | Decision | Value | Basis |
|---|---|---|---|
| 1 | Resident index ceiling | hold at **14 500 B**, never raise | WritePolicyBench saturation at 10 240 B; precision falls above it |
| 2 | Per-type caps | replace **counts with a byte split** | MaRS budget partitioning; the declared "feedback ≤ 5" has no support anywhere |
| 3 | Eviction | staged **Hybrid**: temporal → distil → importance → cap | MaRS composite ≈0.911 vs single policies |
| 4 | Ranking | `imp = α·type + β·recency + γ·frequency`, **divided by token cost** | MaRS; `provenance.py` already stores recency and frequency |
| 5 | Freshness | **timestamps, deterministic**; the model summarises, it does not arbitrate | Don't-Ask-the-LLM; and 2 deletions in 13 runs locally |
| 6 | Decay curve | Weibull, κ<1, η ≈ current 90 d, applied to **all** entries not only promoted ones | SSGM form — *values unpublished, so η and θ_fresh are guesses* |
| 7 | Retention target | distil to a rule, then delete; do not compress | the local "caps force pruning, not compression" note, now corroborated by finding 3 above |

The load-bearing gap: **item 6 has no published value, and item 1's number
comes from a different task.** WritePolicyBench measures drift-event coverage
in agent traces; this index is a resident orientation list. The 10 KB knee is
an analogy, not a measurement on this corpus — and by this repo's own rule, a
number obtained by reading across from someone else's aggregate is a derived
quantity, not a measured one.

**What would settle it locally.** The discriminator is whether the resident
index does the job residency buys — unprompted awareness. Session traces are
already collected and `scripts/census/` already reads them; the measurable
event is a session opening a memory body *without* a recall having surfaced it,
which can only have come from the index. If that event is common, the flat
resident index earns its bytes and item 1 stands. If it is rare, recall is
doing all the work, the index is orientation nobody uses, and the two-level or
wiki shapes become correct — and much cheaper than 14 500 bytes. That is an A/B
the harness can run on its own traces, and it is worth more than any threshold
transplanted from this literature.

## Sources

- [Control-Plane Placement Shapes Forgetting](https://arxiv.org/pdf/2606.15903) — retention logic must live outside the model
- [Forgetful but Faithful (MaRS)](https://arxiv.org/abs/2512.12856) — six forgetting policies benchmarked, staged hybrid wins
- [WritePolicyBench](https://arxiv.org/html/2602.02574) — write policies under fixed byte budgets
- [Don't Ask the LLM to Track Freshness](https://arxiv.org/pdf/2606.01435) — deterministic conflict resolution
- [SSGM: Governing Evolving Memory in LLM Agents](https://arxiv.org/html/2603.11768v1) — Weibull decay, freshness threshold, failure taxonomy
- [Memora: From Recall to Forgetting](https://arxiv.org/html/2604.20006v1) — long-horizon benchmark, forgetting-aware accuracy
- [Less Context, More Accuracy](https://arxiv.org/pdf/2606.09900) — lean retrieved context beats full history
- [Context Rot (Chroma)](https://www.trychroma.com/research/context-rot) — 18 models degrade with input length
- [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110) — Zettelkasten links and memory evolution, already on `/dream`'s v3 roadmap
- [Memory Atlas — filesystem/markdown family](https://www.memoryatlas.dev/families/filesystem-markdown) — portability comes from being plain text

---

## 7. The experiment, run (2026-09-10)

Section 6 ended on the local measurement that would settle item 1. It has been
run, over the whole trace corpus: `scripts/census/memory-recall.py`, 5 753 trace
files, 4.2 GB.

### Design

The measurable event is a **working** session opening a memory body — the only
thing residency buys, since recall relevance is decided by each body's own
`description:`. Four arms, so that a number in the one under test can be read:

| arm | what it is | role |
|---|---|---|
| maintenance | main session invoking `/dream`, `/roar`, `/lair`, `/memory` | positive control |
| working | every other main session | **the measurement** |
| subagent | nested `…/subagents/agent-*.jsonl` runs | counted apart, see below |
| writes | `Edit`/`Write` on a body | housekeeping volume |

Two counting decisions changed the answer by an order of magnitude each, and
both were errors caught before the result was believed:

- **Subagent runs outnumber main sessions nine to one** (5 189 vs 564). Folding
  them in put the working rate at 3.83%. They are launched with a task, not
  with uncertainty about what the project knows, so they were never candidates
  for the behaviour; diluting the arm with them is how a real effect is made to
  look like noise.
- **A session that both `Read` and `cat`'d a body is one session.** Summing the
  two channels inflated the arm under test by a quarter.

Shell reads (`cat`, `sed`) carry no `file_path` and are scanned separately from
the Bash command strings; `Grep` carries a pattern, not a path, and measured 0
occurrences naming a body, so that residue is small.

### Result

```
maintenance (positive control)  132 / 246   53.66%     <- the probe sees the event
working (the measurement)        35 / 318   11.01%
  consumer projects only         23 / 273    8.42%     <- memory used as memory
  harness repo                   12 /  45   26.67%     <- memory IS the work there
subagent runs                   185 / 5189   3.57%
```

**About one working session in nine opens a memory body; one in twelve outside
the harness repo.** The index is therefore not orientation nobody uses, and the
pure-wiki shape — zero resident bytes — would give up a real function.

But the second number is the one that decides the shape:

> **50 distinct bodies were opened by working sessions, out of roughly 900
> index entries.**

Around 94% of the index has never been followed in the trace window. The
resident cost is paid on the whole list; the traffic lands on a twentieth of it.

### Economics

Summing each project's index size over the main sessions it served:

| | index bytes served | per body actually opened |
|---|---|---|
| before the title-only pass | 4 784 923 | 55 638 B (~13 900 tokens) |
| after | 2 904 530 | 33 773 B (~8 400 tokens) |

A body is ~2 000 characters. Each one actually consulted therefore costs about
**seventeen times its own length** in standing index tax, down from
twenty-eight before the pass. This omits the benefit nothing here can measure —
a lesson *not* re-derived leaves no trace — so it bounds the cost, not the
value.

For contrast: **726 writes against 974 body reads across all arms.** The memory
system spends nearly as much effort maintaining itself as every session spends
consulting it.

### What this changes

Neither of the two shapes proposed before the measurement is right.

- **Not the flat index.** 94% inert is not a list to keep resident whole.
- **Not the wiki.** 11% is a real hit rate; zero resident bytes gives up a
  function that fires once every nine sessions.
- **The two-level shape is what the data supports**, and the harness already
  has it in embryo: `## Key insights` above `## Entries`, with `/dream`'s
  promotion pass to fill it. The measurement names what belongs in the resident
  layer — the entries that actually get opened — and that set is small enough
  to fit an index a fraction of today's size. The rest stays reachable by
  recall, at zero resident cost.

Item 1 of §6 therefore stands but is no longer the binding constraint: the
ceiling matters less than *which* entries sit under it, and that is now
measurable rather than argued.

### Caveat

This measures follow-through, not need. A session that recalled a lesson from
the index line alone, and never opened the body, is indistinguishable here from
one that ignored the entry — and that is precisely the case where a
lesson-stating title does its job without any read. So 11% is a floor on the
index's usefulness, and the 94%-inert figure is an upper bound on what could be
demoted. Deciding the promotion set on this evidence alone would evict entries
whose titles were doing silent work.

Instrument: `scripts/census/memory-recall.py`. Re-running it after a promotion
pass is how the demotion would be validated.

## 8. The next redundancy, and why it is not the next job

With the hook gone, the largest remaining line in the index is the filename.
Across the 902 entries in all 47 indexes:

| | chars | share |
|---|---|---|
| titles | 31 170 | 44.1% |
| **filenames** | **33 242** | **47.0%** |
| markdown syntax | 6 314 | 8.9% |

**38.4% of filenames are exactly the slug of their title**, and 51.7% are
contained in it: `[A guard's exemption must be anchored]` links to
`feedback_guard_exemption_must_be_anchored.md`. The lesson is written twice,
once for a reader and once for a filesystem.

| scheme | saves | costs |
|---|---|---|
| drop `.md` | 2 706 (3.8%) | nothing, beyond the link ceasing to be one |
| drop the type prefix | 7 760 (11.0%) | the path stops being reconstructible |
| both | 10 466 (14.8%) | same |
| derive the link from the title | 36 850 (52.1%) | 556 renames, 900 `[[wiki-links]]` rewritten, 1 duplicate title |

**None of these is the next job.** §7 measured that 94% of the index is never
followed. Demoting that share returns about 66 000 chars — 1.8× the most
aggressive filename scheme — without renaming a file or breaking a link. Even a
cautious demotion keeping 150 resident entries returns ~59 000.

The ordering matters more than either number: encoding a list of which 94% should
not be resident optimises the wrong axis. After a demotion the filename
redundancy on the survivors is ~5 500 chars, and scheme D shrinks to a 2 800-char
saving for 556 renames.

Two findings worth keeping from the measurement even so:

- **The naming convention is already inconsistent.** Only 38% of files carry
  their title's slug; the rest are named by topic (`[Zotero library]` →
  `reference_zotero.md`). Aligning names is a contained job *if scoped to the
  resident layer* — tens of files rather than 556.
- **The type prefix is not fat.** It is what makes the path reconstructible from
  the index line, and it is the key for the per-type byte partitioning §2
  recommends. Dropping it saves 11% and costs the ability to find the file.
