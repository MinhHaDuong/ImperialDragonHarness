# Memory systems compared with IDH v6

**Publication date:** 11 September 2026  
**Préparé par ChatGPT prompté par Ha-Duong Minh**  
**Status:** architectural comparison; no installation, integration test or performance benchmark  
**Related design:** [IDH memory v6](./2026-09-10-dragon-memory-design.md)

## Executive summary

Do not adopt a second canonical memory system merely because it offers richer
retrieval. Evaluate reuse at the boundary where it helps: host adapters, candidate
extraction, optional retrieval or strong-host analysis. The acceptance test is
whether the travelling project remains intelligible and useful without that
component.

MemU is a close comparator for cross-agent learning; Letta is also a serious
file/Git-based comparator. Describing all alternatives as opaque vector stores
would be inaccurate. Mem0 and Graphiti offer contrasting service and temporal
retrieval patterns. None of the documentation reviewed establishes the whole
IDH contract out of the box; this is an absence of demonstrated fit, not a claim
that custom integration is impossible.

## Contents

1. [Documented architectures](#1-documented-architectures)
2. [What IDH should borrow](#2-what-idh-should-borrow)
3. [Reuse decision and comparison protocol](#3-reuse-decision-and-comparison-protocol)
4. [Review outcomes carried into v6](#4-review-outcomes-carried-into-v6)

## 1. Documented architectures

Descriptions below are from current primary documentation checked on the
publication date. Product designs change: these are not generic claims about
every historical release. The final column is our architectural inference.

| System | Documented shape | Consequence for IDH |
|---|---|---|
| **MemU** | Agents synthesise Markdown skills from prepared session jobs; a service stores, embeds and retrieves them. Host adapters separate capture from instructed retrieval and share a configured SQLite/Postgres or cloud backend. [Project README](https://github.com/NevaMind-AI/memU) | Close conceptual neighbour. A shared backend is a different ownership boundary from project-committed canonical bodies and offline snapshots. |
| **Letta** | Current MemFS memory is an agent-owned Git repository projected onto a device. System files enter context; other files are discovered through a tree. Background dreaming updates memory. [Current memory documentation](https://docs.letta.com/agent-sdk/memory) | Git-backed files and dreaming are not IDH differentiators. Agent-owned state versus project-owned knowledge is the more useful distinction. |
| **Mem0** | Current README describes additive extraction and semantic/keyword/entity retrieval, with library, self-hosted and managed offerings. It explicitly distinguishes managed benchmark results from the open-source SDK. [Project README](https://github.com/mem0ai/mem0) | Useful retrieval baseline; do not infer that managed performance transfers to a local integration or that an API replaces IDH's editorial boundaries. |
| **Graphiti / Zep** | Graphiti represents evolving facts and provenance in temporal graphs with hybrid retrieval and a graph backend. Zep is the managed context infrastructure; they are not interchangeable deployments. [Graphiti documentation](https://github.com/getzep/graphiti) | Strong comparator for temporal questions, but substantial machinery for a project whose baseline must remain readable without a service. |

## 2. What IDH should borrow

### MemU: reuse the separation, test the adapter boundary

MemU's preparation → agent judgment → commit split is directly relevant to
editorial dreaming versus deterministic publication. Its documented agent can
choose no change, which is compatible with rediscovery being only an opportunity.
Its retrieval is requested through host instructions; that should not be
mistaken for mechanically guaranteed invocation. The self-hosted path documents
an embedding requirement. [MemU README](https://github.com/NevaMind-AI/memU)

**Recommendation:** inspect adapters and candidate preparation before writing
equivalents. An IDH experiment should export candidates through its admission
gate; it should not silently enable another store, rewrite host instructions,
or turn learned procedures into adopted skills.

### Letta: compare ownership rather than file formats

Letta already combines an in-context subset with on-demand file access. Its
shared repositories are also relevant, but the current documentation centres
memory on the persistent agent. [Letta memory](https://docs.letta.com/agent-sdk/memory)

**Recommendation:** borrow its explicit treatment of memory delivery and
compaction boundaries. Test whether a plain project clone, without the Letta
agent/session machinery, meets IDH's offline evidence and withdrawal contracts.
Do not claim that an agent export and a travelling project are equivalent
without performing that test.

### Mem0: benchmark retrieval without importing authority

Mem0's current documented extraction/retrieval design differs from older
descriptions centred on update/delete decisions. Its published managed figures
are not an apples-to-apples result for IDH's proposed lexical baseline.
[Mem0 README](https://github.com/mem0ai/mem0)

**Recommendation:** use a reproducible self-hosted or library configuration as an
optional task-recall baseline. Preserve distinction between agent inference,
observed evidence and governing decisions regardless of retrieval score.
Compare end-to-end task quality, not just its ability to return a stored fact.

### Graphiti: learn temporal semantics before adopting a graph

Graphiti explicitly keeps invalidated facts as history and ties claims to their
source episodes. This is relevant to IDH's separation of historical preservation,
current eligibility and applicability. [Graphiti README](https://github.com/getzep/graphiti)

**Recommendation:** borrow that conceptual discipline. Add graph machinery only
if relationship- or time-dependent retrieval failures justify it. A relation
such as `generalizes` does not alone justify a graph service; UUID references
and generated reverse links can represent the initial requirement.

## 3. Reuse decision and comparison protocol

**Licence condition**

All component-reuse recommendations are conditional: inspect the specific
revision's licence and dependency obligations for the intended distribution,
retain required notices and record the assessment before adoption. No component
in this comparison has been cleared for integration. Unclear permissions mean
no copying, adaptation or dependency adoption until clarified. Reusing an idea
does not justify copying its implementation.

**Recommended order**

1. Implement the smallest IDH admission/compiler/reader contract as one internal
   Python library with thin CLI and adapters, reusing existing knowledge hints
   and repository workflows.
2. Inspect MemU's adapter and preparation interfaces for reusable parts.
3. Compare one optional retrieval implementation against lexical retrieval on
   the same accepted corpus.
4. Consider a different canonical backend only if concrete maintenance or
   reliability evidence outweighs the travelling-project requirement.

This is a build-versus-reuse recommendation, not a claim that IDH must implement
every retrieval algorithm itself. An optional backend can be a derived view or
candidate-producing component. It must have a removable boundary.

**Common comparison protocol**

Hold the accepted corpus, tasks, model, context allocation and evaluation rubric
constant where possible. Record version/commit, configuration, export procedure,
preparation cost, query cost and any hosted dependency. If equivalence cannot
be established, state the mismatch rather than rank the scores.

Evaluate:

- a fresh offline clone with no original home directory;
- new lessons before consolidation;
- task recall with irrelevant-memory growth;
- generalisations with local exceptions;
- retraction, compaction and resume;
- ledger-shaped content at entry;
- concurrent runtime/native memory enabled;
- removal of the optional component without losing canonical evidence.

Measure useful decisions, harmful stale advice, provenance fidelity, latency,
resident exposure and cumulative retrieval cost. Report retrieval recall
separately from behavioural success. Vendor benchmark tables and different
versions of LongMemEval or LoCoMo are not interchangeable evidence.

**No performance ranking is offered here.** These systems solve overlapping but
different problems. IDH's distinctive requirement is project ownership plus
graceful consumption across runtimes, with editorial memory kept separate from
decisions and existing knowledge assets.

## 4. Review outcomes carried into v6

Three independent reviewers examined runtime memory, neighbouring subsystems,
and design integrity. The applied amendments are:

| Finding | Applied resolution |
|---|---|
| Native auto-memory can bypass canonical admission | One ownership contract and a single delivery owner; disclose uncontrollable native memory |
| Compaction and child sessions can retain stale paraphrases | Explicit boundaries and a small non-model delivery record; limited guarantees |
| Admission omits existing canonical homes | Route STATE, tickets, reusable assets and hints before admitting memory |
| Knowledge hints duplicate discovery | Reuse the pointer/caveat interface and account for its exposure |
| “Ledger” implies a new subsystem | Bind to existing canonical project decision records |
| Harvested advice can compete with an amended procedure | Preserve evidence but qualify old prescriptions and link the governing artefact |
| Provenance can be a private, unusable pointer | Carry a concise portable observation and disclose missing evidence |
| Semantic routing treated as a deterministic gate | Require a recorded judgment; test correctness behaviourally |
| Immutable views and mutable status are conflated | Pin publication G and accepted corpus C explicitly |
| Snapshot cannot supply every ranked shared candidate | Fix the available shared set before publication and ranking |
| Static rank cannot optimise post-filter redundancy | Static orientation; selection-dependent adjustment in task recall |
| Pending generalisation blocks publication | Separate editorial dreaming from compilation |
| Optional machinery appears compulsory | Defer rich scoring telemetry, broad predicates and embedding details |

These changes refine the design, not the runtime implementation. Rediscovery
remains an opportunity; a useful dreaming pass can make no generalisations.
