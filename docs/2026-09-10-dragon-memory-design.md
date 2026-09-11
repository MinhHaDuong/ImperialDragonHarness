# The Dragon's memory — design v5

**Publication date:** 11 September 2026  
**Status:** design draft for review; incorporates the owner's design discussion following v4  
**Préparé par ChatGPT prompté par Ha-Duong Minh**  
**Repository baseline:** `a90a9f5e9be4f88889b180bd05ba0ef8aaa993f6`  
**Previous design:** [v4, frozen](./2026-09-10-dragon-memory-design-v4.md)

This is an architectural specification, not a report on implementation progress.
It replaces v4's architectural proposal. Historical measurements, runtime probes
and earlier reviews remain in the frozen versions; they are not revalidated here.
The established current-design filename is retained so existing references still
lead to the latest design.

## Contents

1. [Executive summary](#1-executive-summary)
2. [Purpose, boundaries and guarantees](#2-purpose-boundaries-and-guarantees)
3. [Stores, scope and portability](#3-stores-scope-and-portability)
4. [Identity, format and lifecycle](#4-identity-format-and-lifecycle)
5. [Admission and authority](#5-admission-and-authority)
6. [Orientation, recent supplement and task recall](#6-orientation-recent-supplement-and-task-recall)
7. [Applicability, retrieval and ranking](#7-applicability-retrieval-and-ranking)
8. [Capacity policy](#8-capacity-policy)
9. [Dreaming and generalisation](#9-dreaming-and-generalisation)
10. [Publication and synchronisation](#10-publication-and-synchronisation)
11. [Runtime adapters and graceful degradation](#11-runtime-adapters-and-graceful-degradation)
12. [Acceptance criteria](#12-acceptance-criteria)
13. [Migration and remaining choices](#13-migration-and-remaining-choices)
14. [Decision trace and references](#14-decision-trace-and-references)

## 1. Executive summary

The canonical store is readable Markdown bodies with structured frontmatter,
tracked with the project. Generated catalogues, rankings and retrieval caches
are views over those bodies. Dreaming may require a capable host; ordinary
consumption must work in disposable containers and across Codex, Pi and Claude
Code. Without the harness, a reader can still browse and assess the memory.

Project memory and shared memory are separate knowledge scopes. IDH itself has
ordinary project memory: maintaining the harness does not confer global scope.
A project combines its own memories with applicable shared memories, deduplicates
by UUID, and selects within one orientation budget. It does not allocate separate
fixed quotas to local and shared entries.

Three delivery components handle different timescales:

| Component | Purpose | Refresh |
|---|---|---|
| Orientation | Stable awareness through a ranked index | Ranked by dreaming; filtered and budgeted at loading |
| Recent supplement | Bridge the interval before changes are processed by dreaming | Derived from accepted memory revisions absent from the publication |
| Task recall | Supply relevant bodies or focused excerpts, including below-cut memories | When the task is clear and when it materially changes |

Memory has no mandatory-residency class. User emphasis can influence weight,
but requirements belong in rules, skills and, where machine-checkable, hooks.
Instruction injection can be deterministic; model adherence remains probabilistic.
Hooks enforce only conditions and action paths they actually intercept.

At entry, distinguish experience from decisions. Decisions, commitments and
authorisations go through the decision-ledger process. Memory can reference a
decision or provide evidence for reconsideration; it cannot become a parallel
ledger or determine which decision governs.

Scope expansion, generalisation and supersession are different operations.
Each rediscovery is only an opportunity to consider generalisation, never an
automatic trigger or a requirement to synthesise. An accepted generalisation
creates a new claim linked to its source memories; particulars
remain active unless explicitly superseded or retracted. Preserve history,
but exclude inactive advice from normal selection.

Fixed configurable ceilings, variable occupancy and measured recalibration
govern capacity. The proposed 1,500 / 500 / 2,000-token allocation is an engineering
starting point, not an adopted optimum or a literature-derived constant.

## 2. Purpose, boundaries and guarantees

Memory helps an agent reuse observations, experience and inferred lessons.
Its success is better task behaviour at a bounded cost, not a high count of
stored entries, reads or injected tokens.

| Mechanism | Contract |
|---|---|
| Decision ledger | Canonical record of adopted decisions and authorisations |
| Rules and contracts | Required text supplied through a defined loading mechanism |
| Skills | Procedure supplied when the relevant skill is loaded |
| Scripted hooks | Mechanically enforce checked conditions on intercepted paths |
| Memory | Ranked evidence and discovery aids that may improve behaviour |

Memory cannot guarantee awareness or obedience. V4 correctly distinguished
reachability from unprompted awareness, but its mandatory-residency remedy
created another instruction system and an impossible promise under unbounded
mandatory growth. V5 keeps the distinction and removes that remedy.

A preventive lesson may enter memory immediately. Periodic harvesting can propose
a rule, skill or hook amendment. Urgent explicit requirements use the normal
instruction-change path directly rather than waiting for dreaming.

Preservation means no automatic destruction merely because of age, score or
capacity. It does not prohibit explicit owner-directed removal or justify storing
secrets and unsuitable material in a travelling repository. Inactivity is normal;
historical preservation is distinct from eligibility for current advice.

No universal optimal budget, semantic-retrieval advantage or automatic runtime
discovery is claimed.

## 3. Stores, scope and portability

### 3.1 Project and shared scopes

Each project owns memory inside its repository. A user's home directory may hold
an installation, shared store or derived cache, but cannot be the sole canonical
home of project memory.

The shared store holds reusable knowledge with explicit applicability. It is not
automatically resident everywhere. IDH's implementation notes belong to the IDH
project unless a separate scope-expansion or generalisation process establishes
broader applicability.

Provenance answers where a lesson came from. Applicability answers where it is
useful. Neither storage location nor a score establishes authority.

A stable project identifier independent of checkout path is the proposed default.
Cloning or moving the same project preserves that identifier; creating a genuinely
independent project is an explicit identity decision. The identifier format and
fork policy remain schema decisions, not inferred from directory names.

### 3.2 Portable project layout

The following names are an illustrative layout, not a mandated migration path:

| Path under the project memory root | Role |
|---|---|
| `README.md` | Plain-language discovery and usage instructions |
| `*.md` | Active locally owned bodies, with reserved filenames for views |
| `inactive/` | Preserved superseded or retracted local bodies |
| `shared-snapshot/` | Committed readable replicas of relevant shared bodies |
| `index.md` | Generated complete catalogue of active available bodies |
| `MEMORY.md` | Generated bounded default orientation |
| `publication.json` | Publication inputs, processed revisions, ordered candidates and scores |
| `.cache/` | Ignored, disposable acceleration data |

All navigational links are relative. Generated catalogues use ordinary Markdown
links: a bare reader must not need a UUID resolver just to open a body. A link
validator distinguishes reserved view files from actual memories.

Inactive bodies display a conspicuous human-readable status notice as well as
machine-readable frontmatter. Moves must preserve historical navigability:
regenerate affected local links, resolve machine references by UUID, and provide
a redirect or equivalent repair for old path links where needed. Redirects are
not active memories and cannot enter rankings.

### 3.3 Shared snapshots

Each project commits a snapshot of shared bodies selected for its orientation
and those explicitly referenced by active local memories. Required reference
dependencies are included or explicitly reported unavailable. Do not copy the
whole shared corpus by default.

A replica preserves the UUID, upstream revision and content hash. It is not a new
memory and is not independently editable. Changes are proposed upstream, or an
explicitly distinct local observation is authored with provenance.

Dreaming refreshes the snapshot and publishes it with the project views. Ordinary
consumption needs no network. The manifest records the upstream revision and
refresh date. No secrets or access credentials are packaged with it.

When a live shared store is available, reconcile by UUID and proven revision
ancestry. A verified successor can replace a snapshot revision; divergent versions
must not be resolved by timestamp alone. Such updates enter the recent supplement
until processed by dreaming.

Offline recall covers local bodies and the snapshot. It cannot discover uncached
shared bodies or learn upstream retractions after the last synchronisation.
Expose this boundary; do not claim complete or current global knowledge.

## 4. Identity, format and lifecycle

### 4.1 Stable identities and readable files

Each memory receives an immutable UUIDv4 at creation. Filenames are readable
slugs and can change without changing identity. Scope and location are independent
of identity. Two distinct memories may have similar filenames; duplicate UUIDs
with conflicting bodies require explicit resolution.

Machine relations use UUIDs. A generated UUID-to-path map is rebuildable from
frontmatter, including inactive bodies and replicas. Clocks are not identity or
conflict-resolution mechanisms.

### 4.2 Body format and language

Canonical text is English with UK spelling: titles, descriptions, tags and prose.
Preserve quotations, proper names, code, paths and external identifiers exactly.
Schema keys retain their specified spelling.

Keep the portable base field names discussed in v4: `type`, `title`,
`description`, `tags`, `timestamp`. Add identity, scope, lifecycle and provenance
explicitly. Compatibility with an external convention must be validated against
its version before being claimed; runtime-specific aliases are derived, never
canonical alternatives.

The schema must represent the following concepts; exact field nesting is an
implementation decision:

| Concept | Meaning |
|---|---|
| Identity | Immutable UUID and schema version |
| Description | Human title, retrieval description and useful keywords |
| Scope | Project associations and explicit applicability conditions |
| Lifecycle | Active, superseded or retracted |
| Provenance | Source references; user-stated, observed or inferred; author |
| Dates | Creation and semantic updates, separately from file migration time |
| Relationships | Generalises, superseded-by, challenges, decision references |
| Ranking inputs | Declared importance, user emphasis and supporting evidence |

A single `timestamp` does not collapse observation time, creation time and
last edit. Preserve their meanings where they differ. Mechanical reformatting
must not manufacture semantic freshness.

Computed scores and ranks do not belong in filenames or canonical bodies.
Annotated importance is a judgment with provenance, not an authoritative score.

### 4.3 Lifecycle, applicability and provisional status

| Dimension | Values or meaning |
|---|---|
| Lifecycle | Active / superseded / retracted |
| Applicability | True / false / unknown in a named consuming context |
| Processing | Provisional relative to a publication, or processed by that publication |

Superseded means replacement advice exists. Retracted means withdrawn without
necessarily having a replacement. Set the status in frontmatter and move the
local body into `inactive/` in one committed operation. Frontmatter is
authoritative: a misplaced inactive body remains excluded and disagreement is
reported. Supersession references resolve to replacement UUIDs.

An inapplicable workaround remains active knowledge for another environment.
A retracted or superseded memory cannot revive merely because a tool version
or path changes. Restoration is an explicit editorial act.

Provisional is not a third knowledge scope. A body is provisional for a project
publication when its accepted revision is not in that publication's processed
manifest. The same shared body can be processed in one project and recent in
another. Losing a freshness allowance does not delete the body or claim it was
processed.

Normal selection excludes inactive bodies. Historical retrieval deliberately
includes them with their status and replacement links. Unknown applicability is
retained as uncertainty, never silently rewritten as true.

## 5. Admission and authority

### 5.1 The entry question

Before a candidate enters memory, ask:

> Does this record what was decided or authorised, or what was observed or learned?

| Candidate | Route |
|---|---|
| Adopted decision, commitment, authorisation | Decision-ledger process |
| Observation, experience or inferred lesson | Memory, with provenance |
| Both | Split; memory references the canonical decision |
| Ambiguous | Proposal or unresolved question; do not assert an adopted decision |

This is an agent classification step, not an automatic request for human
confirmation. Clarify only if the conversation cannot establish the distinction.

A candidate must also pass structural validation and a suitability check for the
repository's audience. Recording an observation does not grant permission to
publish confidential material. Unresolved scope or audience questions must not
silently expand access.

### 5.2 Editorial authority

Sessions may record experiential memories. Dreaming may consolidate, generalise,
rescope and retire experiential memories, preserving their originals and the
reason for semantic changes. Shared changes follow the established repository
review process.

Decisions and authorisations remain in the ledger. Memory may challenge a
decision with new evidence but cannot amend its governing status. Repeated
inferences do not become a user statement; repeated copies of one incident do
not become independent observations.

Budget changes, authority policy and harvested rules, skills or hooks follow
their normal decision and change processes. A self-authored `approved` field
cannot grant authority.

Admission is not ranking. Validating syntax does not establish truth, and a
deterministic score over model-authored inputs does not remove model judgment.
Judgment is recorded and reviewable; selection is reproducible for fixed inputs.

### 5.3 Harvesting requirements

During dreaming, identify experiential lessons that warrant an amendment to:

- a rule for broadly applicable behavioural requirements;
- a skill for a particular procedure;
- a hook for an invariant whose condition and action path can be checked.

Propose the amendment through the existing process. After acceptance, record a
reference to the adopted artefact and reduce redundant exposure where appropriate.
Do not automatically delete the supporting evidence or treat the harvesting
proposal as an adopted instruction.

## 6. Orientation, recent supplement and task recall

### 6.1 Orientation

Dreaming combines local and applicable shared candidates, deduplicates replicas
by UUID, and publishes a ranked candidate order plus a bounded readable default
index. There is no fixed local N plus shared M allocation.

At loading, a lightweight adapter checks current lifecycle and applicability,
walks the published order and selects what fits the orientation budget. It need
not invoke a model, embed a query or recompute importance.

**V5 drafting default:** publish a full ranked candidate order rather than only
the budget-sized excerpt. This permits refilling after current-context filtering
without moving ranking into the container. It replaces the earlier discussion's
temporary acceptance of underfilling solely because the published excerpt was
too short. Genuine lack of useful applicable candidates still leaves the view
underfilled.

The manifest must describe the pool it ranks. An absent uncached shared body is
not a locally available candidate. New or semantically changed revisions belong
to the supplement, rather than inheriting an obsolete content score.

### 6.2 Recent-memory supplement

Accepted revisions not processed by the published dream snapshot are immediately
discoverable. At the next supported loading boundary, applicable entries can
enter a small recent supplement even though the orientation remains frozen.

This supplement has its own reserved allowance inside the total memory allocation.
It does not grow with the backlog. Overflow remains searchable by task recall.
Use deterministic freshness/relevance ordering with a stable tie-break, no
mandatory status and no self-awarded global authority.

A configurable freshness interval limits preferential exposure. Entries losing
that preference remain provisional until processed and remain searchable. Report
an ageing backlog rather than hiding it through expiry.

Suppress UUID duplication between components; if a new revision replaces an old
orientation revision, expose the current revision at most once. Never fall back
to obsolete advice merely because its replacement did not fit.

Retractions and supersessions are processed before positive selection, independent
of the supplement's content budget. Their effect cannot depend on ranking.

### 6.3 Task recall

Once the task is sufficiently clear, retrieve before the first consequential
action relevant to that task. An explicit user request to remember is unnecessary.
Refresh on a material task change or newly relevant constraint.

Search the whole eligible local plus available shared pool, including entries
below the orientation cut and unprocessed entries. Return relevant bodies or
focused excerpts with source identity, scope, status and links. Avoid repeating
content already supplied; keep qualifications with the advice they constrain.

The task bundle has a separate bounded allowance. Refresh replaces the logical
active bundle rather than accumulating bundles indefinitely. If the runtime
cannot remove old messages, track cumulative injected tokens, avoid repeats and
preserve only the current bundle through supported compaction. Report the
difference between active allocation and actual retained transcript cost.

## 7. Applicability, retrieval and ranking

### 7.1 Consuming context

Evaluate applicability against the consuming project's identity, environment and
available tool versions, not the host that ran dreaming. Task recall additionally
uses the current task.

A small closed predicate grammar may express paths, bounded text checks and tool
version conditions. It must not execute arbitrary memory-authored shell code.
Bind paths to explicit roots and bound evaluation cost.

False excludes current use. Unknown is explicit and may remain a candidate with
a qualification; it is not positive evidence of applicability. Keyword absence
is not a hard exclusion.

At entry, reject malformed predicates and unknown grammar operators. For an
intended local, currently applicable observation, flag an evaluable false
predicate as a mismatch to resolve. An unevaluable predicate in a lightweight
container must not prohibit recording the observation: retain it as unverified,
with provenance, for later evaluation. This deliberately replaces v4's universal
write-time requirement that every predicate evaluate true. A container need not
possess every environment a reusable lesson describes.

Environmental predicates express only a subset of obsolescence. Decisions
reversed and observations disproved need explicit relations or lifecycle changes;
they cannot be inferred reliably from filesystem state.

### 7.2 Lexical baseline and optional semantics

Keywords and tags help retrieval, alongside title, description and body text.
They are useful for tool names, concepts and aliases. They do not define the
whole applicability boundary.

Lexical retrieval is the portable baseline. Empty or weak evidence may yield
an empty bundle; capacity is not an obligation to provide advice.

Embeddings are optional, initially most useful to dreaming for proposing related
groups. Their use must justify identifiable lexical misses. Embeddings suggest
similarity, not equivalence or contradiction resolution.

A disposable embedding cache is keyed by content hash, embedding model/version
and preprocessing configuration. It is ignored by git. Deleting it changes
cost, not canonical knowledge. Warm and cold runs with fixed inputs must agree
on deterministic downstream results within a documented numerical policy.

Task-time semantic retrieval additionally needs a compatible query embedder.
Precomputed body vectors alone do not make semantic search available offline.
Absence of the model or cache falls back to lexical retrieval and reports the
capability difference.

### 7.3 Ranking and reproducibility

Rank eligible candidates using declared importance, cost of rediscovery,
project/task relevance, user emphasis and evidence of use. Observed opens remain
secondary: a useful title may prevent an action without a body read.

Preventive value can contribute weight but never grants mandatory residency.
No blanket preference awards local origin precedence over a more useful shared
lesson.

Account for length and redundant content when selecting a bundle. Once a
generalisation is selected, a related particular must justify its additional
context cost; local conditions can justify it. Do not permanently penalise every
generalised source or force every active memory to fill remaining capacity.

Exact weights, thresholds and redundancy functions are versioned calibration
choices. Start simple. Record component scores and ordered UUIDs in generated
manifests, not filenames.

Reproduction requires more than the bodies:

`selection = F(corpus revisions, policy version, consuming context, evaluation time, task where relevant)`

A dream publication records its scoring inputs and evaluation time. A runtime
records the context used for filtering. Stable tie-breaking is required. Model
judgments enter as recorded annotations; semantic consolidation is not claimed
to regenerate identical prose from identical prompts.

## 8. Capacity policy

Fixed ceilings, variable occupancy and periodic measured recalibration are the
capacity policy. Do not increase limits automatically because the corpus grew.
Do not allocate a constant percentage of an advertised context window without
evidence of utility.

| Channel | Proposed initial ceiling | Status |
|---|---:|---|
| Orientation | 1,500 tokens | Calibration proposal |
| Recent supplement | 500 tokens | Calibration proposal |
| Task recall | 2,000 tokens | Calibration proposal |
| Total active allocation | 4,000 tokens | Sum of proposals; not a measured optimum |

These figures were proposed in the discussion, not separately ratified as
permanent values. They exclude rules, skills, conversation and task evidence.
Leaving capacity unused is acceptable.

Count the rendered payload, including headings, status labels, links and
identifiers. A runtime tokenizer is preferred where available. A portable
character or byte profile must disclose its estimation rule; it cannot claim an
exact token guarantee across models. Publication can carry derived estimates
without treating them as measurements.

Keep profiles versioned and fixed within a run. Compare half, baseline and double
allocations on representative tasks, changing one component at a time. Prefer
the smallest allocation with comparable task quality, recording latency, actual
injected tokens and cumulative refresh cost.

The persistent corpus has no score- or count-driven deletion cap. Monitor growth,
consolidation duration and unresolved backlog. Memory bodies can be cheap to
store without being free to retrieve, judge or maintain.

## 9. Dreaming and generalisation

Dreaming may run on a strong host with model access, the shared store and optional
embeddings. A consuming container need not run it.

### 9.1 Three distinct operations

| Operation | Identity and consequence |
|---|---|
| Broaden an unchanged lesson's scope | Same UUID; reviewed applicability change |
| Generalise observations into a broader claim | New UUID with `generalizes` references to sources |
| Replace obsolete or redundant advice | Explicit supersession; source becomes inactive |

The wire key `generalizes` retains its specified spelling; human prose uses UK
spelling. Compute the reverse relation rather than maintaining both directions
by hand.

Particular observations remain active after generalisation unless explicitly
superseded or retracted. A generalisation can be wrong while its source
observation remains correct. Local exceptions and evidence must survive.

If several redundant bodies are replaced by a synthesis, create a new UUID,
retain the originals inactive and identify the replacement. Reject cyclic
supersession and dangling replacement claims; a disputed replacement is not
resolved by choosing the latest timestamp.

**Rediscovery creates an opportunity, not an obligation.** Every rediscovery may
prompt consideration of whether the observations support a useful broader claim.
There is no occurrence threshold that automatically generalises, broadens scope,
or creates a synthesis. Leaving the particular memories unchanged is a valid
outcome, and the pass need not manufacture a generalisation to show progress.

Similar wording is a candidate signal, not proof of one lesson. Neither two
projects nor repeated copies automatically establish global applicability.
Generalisation requires an explicit judgment about shared conditions, independent
evidence, exceptions and usefulness, followed by the applicable review process.
Record the rationale for accepted generalisations; do not equate the number of
rediscoveries with confidence. A single sufficiently grounded observation can
support a proposed broader claim, while many recurrences may still support only
particular claims.

### 9.2 Pass responsibilities

A pass captures its input snapshot, validates identities and links, identifies
candidate groups, applies the authorised editorial process, updates shared
snapshots, computes rankings and publishes views.

Deterministic work can be tested independently from model-authored synthesis.
Record model identity, prompt/template version, source revisions, judgments and
accepted outputs for semantic changes.

A pass works in isolation and refuses to overwrite uncommitted bodies. A local
lock prevents local overlap; it does not establish exclusivity across machines.
Concurrent edits to the same UUID require a merge or explicit conflict state.
Independent additions and per-body granularity reduce contention without
eliminating semantic conflicts.

Review contradictory claims as well as near duplicates. A semantic report can
identify possible conflicts; it does not autonomously declare which decision
governs or which observation is false.

## 10. Publication and synchronisation

### 10.1 Snapshot and atomic handover

A publication manifest identifies:

- input project revision and relevant shared revisions;
- each processed UUID and body revision/hash;
- included snapshot bodies and source provenance;
- schema, generator and ranking-policy versions;
- evaluation time, contextual assumptions and budget profile;
- full ordered candidates and their component scores;
- hashes of emitted views.

Bodies processed but below the cut are still processed. Selection and processing
are different sets.

Publish related catalogues, snapshots and manifests as one coherent generation.
On disk, stage a generation and switch its reference atomically; a reader pins a
generation for its load. In git, commit the corresponding change set together.
Exact packaging may vary, but readers must not mix generations.

New or changed accepted body revisions absent from the processed manifest remain
recent, including writes made while dreaming ran. A timestamp alone is
insufficient. Record the actual processed set after editorial changes as well as
the original snapshot; do not leave newly produced synthesis bodies accidentally
unprocessed.

Before publication, reconcile against the current branch. Reject or rebase
conflicting semantic updates; do not overwrite a concurrent retraction or
publish a misleading claim of having processed a newer body. This is a
revision check, not a filesystem-lock assumption.

### 10.2 Loading and withdrawal

Refresh at session start and task boundaries. Check locally known withdrawals
before consequential actions on adapter-supported paths. Filtering must consult
current local lifecycle state, not trust the status copied into an old index.

A withdrawal suppresses advice even if the replacement is unavailable. Already
injected text cannot always be removed: emit an explicit correction at the next
supported boundary and exclude it from future bundles. This guarantees delivery
only on instrumented paths; subsequent model adherence remains probabilistic.

Offline consumers cannot know later upstream withdrawals. Once synchronisation
reveals one, it takes effect without awaiting the next dream.

### 10.3 Missing or damaged publication

Proposed fallback: validate local frontmatter and offer deterministic catalogue
browsing or lexical search over available active bodies. Report unavailable
ranking, missing shared coverage or unresolved identity conflicts. A malformed
file is reported, not silently certified active.

Do not claim successful complete generation from an empty enumeration. Positive
controls must distinguish an empty store from a broken walker. A missing cache
requires rebuilding or a slower path; a missing publication must not destroy
access to readable bodies.

## 11. Runtime adapters and graceful degradation

| Capability | Full adapter | Lightweight container | No harness |
|---|---|---|---|
| Read canonical bodies | Yes | Yes | Plain Markdown |
| Discover through catalogue | Yes | Yes | Ordinary relative links |
| Filter and budget orientation | Yes | Small local loader | Published default only |
| Recent supplement | Automatic at supported boundaries | Small local loader | Manual discovery; catalogue may lag |
| Task recall | Lexical, optional semantic | Lexical baseline | Manual search |
| Dreaming | Available on capable host | Not required | Not required |
| Shared knowledge | Live store plus snapshot | Snapshot; optional synchronisation | Readable snapshot |
| Withdrawal propagation | At instrumented boundaries | At supported boundaries | Explicit body status; no automatic guarantee |

Codex, Pi and Claude Code adapters share canonical schema and lifecycle semantics.
Runtime aliases and injection packaging are generated. No adapter may silently
switch off one delivery channel because a native recall feature activates.
It must supply an equivalent path or report the reduced capability.

A plain checkout guarantees intelligibility and local access, not automatic
discovery, timely filtering or prompt injection. Offline, harness-free operation
cannot be advertised as full behavioural equivalence.

A reader should be able to inspect the evidence and its status without access
to embeddings, an external database, private session traces or the original host.

## 12. Acceptance criteria

### 12.1 Deterministic contracts

Each gate includes a fixture that fails when the relevant mechanism is removed.

| Fixture | Required result |
|---|---|
| Fresh clone in a relocated disposable container, no original home directory | Local bodies and committed shared snapshot readable; relative navigation works |
| Same corpus and declared context across adapters | Equivalent eligibility, lifecycle handling and policy inputs; tokenizer-dependent cuts disclosed |
| Retracted body still present in stale orientation | Excluded at next supported load, even if incorrectly placed outside `inactive/` |
| Replacement is unavailable or below budget | Superseded advice remains suppressed; unavailability is reported |
| New write during dreaming | Present in the unprocessed set after publication |
| Concurrent edit/retraction to a processed UUID | Publication detects revision mismatch; no silent overwrite |
| Interrupted publication | Reader sees a complete old or new generation |
| False and unknown applicability | False excluded; unknown retains its label |
| Rediscovery in several projects | Candidate consideration only; no automatic scope change or synthesis |
| Accepted generalisation from particulars | New identity, intact sources and resolvable relations |
| Duplicate UUID replicas and divergent revisions | Replicas deduplicated; divergence reported |
| Cold cache, missing embedding model, no network | Lexical baseline works and reduced capability is explicit |
| Ranking manifest absent or corrupt | Local inspection remains possible; no false completeness claim |
| Oversized pool and repeated task changes | Per-component bounds hold; retained cumulative injection is measured |
| Decision-shaped input | Routed to ledger process, not admitted as authoritative experiential advice |

Tests of publication atomicity and conflict handling concern machine behaviour.
A test that merely checks whether a skill contains a required sentence does not
prove the runtime honours the contract.

### 12.2 Behavioural evaluation

Run matched task scenarios with memory disabled, orientation alone and the full
delivery design. Include representative IDH maintenance, consumer-project coding
and research tasks. Repeat runs and report denominators, model/runtime versions
and uncertainty.

Evaluate whether agents:

- use a relevant lesson without an explicit request to recall it;
- obtain below-cut evidence through task recall;
- preserve a local exception when applying a generalisation;
- recognise a correction rather than repeat superseded advice;
- distinguish an observation from a ledger decision;
- avoid inventing applicability when the environment is unknown;
- maintain task quality as irrelevant memories accumulate;
- remain usefully informed from a bare clone and an offline snapshot.

Measure task success, costly mistakes, unsupported memory use, unnecessary
retrieval, latency and total memory-related tokens. Body opens and ranking
misses are diagnostics, not the objective.

Deterministic invariants are hard acceptance gates. Behavioural success is a
measured rate, not a guarantee from one green run. Define task-specific
non-inferiority margins and desired gains before comparing budgets; numeric
release thresholds require calibration and are not invented here.

## 13. Migration and remaining choices

### 13.1 Migration outline

This is a design dependency outline, not a claim that the existing tickets
implement v5.

1. Freeze v4 and reconcile the architecture decisions through the project's
   decision-ledger process. Preserve prior review citations.
2. Specify the minimal schema, stable project identity and portable layout.
   Preserve historical dates before bulk rewriting; assign UUIDs with an
   auditable old-path-to-ID mapping and repair links.
3. Separate IDH project memory from shared memory. Move project-owned bodies
   into their repositories and introduce readable versioned shared snapshots.
4. Establish ledger routing at entry, lifecycle handling and canonical validation.
   Remove mandatory-memory residency from the design and any later implementation.
5. Implement deterministic publication, ranked candidate manifests, local loading
   and the recent supplement before relying on model-assisted consolidation.
6. Add lexical task recall and the adapter capability contract. Exercise fresh
   containers and no-harness browsing.
7. Add reviewed generalisation, semantic consolidation and harvesting on the
   strong host. Add embeddings only when justified.
8. Calibrate capacity and behavioural acceptance with the preserved evaluation
   fixtures.

Existing tickets 0908–0919 must be reviewed against this outline before execution.
Their v4 premises concerning promotion, identity, write-time validity and index
ownership cannot simply be retained. This document does not allocate or close
tickets, and it does not modify runtime code.

### 13.2 Explicit proposal boundaries

The principal architecture follows the owner's discussion. The following are
drafting defaults or calibration work, not claims of separately ratified detail:

| Item | V5 position |
|---|---|
| 1,500 / 500 / 2,000 tokens | Proposed initial profile |
| Full ranked manifest for load-time refilling | Recommended resolution of the earlier underfill alternative |
| Project identifier and exact directory names | Stable identity required; concrete format/layout to specify |
| Unknown write-time predicates | Preserve unverified observation; reject malformed grammar |
| Ranking weights, freshness interval and relevance threshold | Versioned calibration choices |
| Predicate operators and context probing | Bounded portable grammar to specify |
| Adapter refresh/interception coverage | Must be declared and verified per runtime |
| Behavioural release thresholds | Set from representative trials before claiming improvement |

No new database service, globally unique human slug scheme, automatic capacity
growth or memory-specific approval bureaucracy is required.

## 14. Decision trace and references

This section explains design changes and points to their source discussion.
It is not a substitute decision ledger. Adoption and subsequent changes belong
in the project's established decision process.

| V4 premise | V5 resolution |
|---|---|
| Mandatory resident memories | Removed; requirements harvested to rules, skills and hooks |
| Harness tier conflates infrastructure and shared knowledge | Ordinary IDH project memory plus separate shared scope |
| Local and harness indexes have independent resident allocations | Combined eligible pool within one orientation allocation |
| Promotion moves a lesson up and tombstones the local source | Distinguish scope expansion, generalisation and supersession |
| Filename provides identity | UUID identity; readable mutable filenames |
| Bodies unavailable until periodic scoring | Recent supplement and task recall expose accepted unprocessed revisions |
| Ranking supplies admission control | Entry routing and provenance precede ranking |
| Nothing deleted implies current advice remains safe | Explicit lifecycle, status-aware retrieval and historical access |
| File portability is enough | Fresh-container, offline-snapshot and no-harness contracts |
| Store alone reproduces a view | Record revisions, policy, context, time and task inputs |
| A generated index cannot drift | Revision-aware publication plus current-state filtering |
| Memory can carry commitments | Route decisions to the ledger at entry |

**Historical design and evidence**

- [Frozen v4](./2026-09-10-dragon-memory-design-v4.md): historical measurements,
  earlier runtime observations, review record and previous ticket plan.
- [Portable-memory calibration note](./2026-09-10-portable-agent-memory-calibration.md):
  earlier research synthesis; its numerical analogies are not v5 budget mandates.
- [Validity-coverage ledger](./2026-09-10-valid-while-coverage-ledger.md):
  limits of environmental predicates for real experiential memories.

**Research informing the capacity prior, not specifying the architecture**

- [LongMemEval](https://arxiv.org/abs/2410.10813): evaluates long-term interactive
  memory and indexing/retrieval/reading choices; does not establish an IDH
  resident-token optimum.
- [LazyMem v2](https://arxiv.org/abs/2607.22690v2), under review: reports compact
  answer-context memory using a trained query-time compressor. Its token figure
  excludes upstream work and is not a general allocation rule.
- [Scale-conditioned evaluation of agent memory](https://arxiv.org/abs/2605.07313),
  preprint: motivates evaluating usable reliability and retrieval burden as
  irrelevant evidence accumulates.

The draft's acceptance suite must assess IDH's own workloads. External benchmark
results do not certify this design or its adapters.
